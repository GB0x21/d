import time
import logging
import praw
from prawcore.exceptions import ServerError, RequestException, ResponseException

from bot.filters import PostFilter
from bot.scoring import score_post
from bot.price_extractor import extract_prices
from bot.dedup import is_duplicate
from bot.store_locator import extract_store_info
from bot.flair_detector import get_flair_info
from bot.telegram_sender import TelegramSender
from bot.comment_tracker import CommentTracker
from database.db_manager import DBManager
from utils.health import HealthMonitor
from utils.retry import with_retry

logger = logging.getLogger(__name__)

TRANSIENT_ERRORS = (ServerError, RequestException, ResponseException, ConnectionError, TimeoutError)


class RedditMonitor:
    def __init__(
        self,
        reddit: praw.Reddit,
        db: DBManager,
        telegram: TelegramSender,
        post_filter: PostFilter,
        health: HealthMonitor,
        subreddits: list[str],
        check_interval: int = 60,
        max_retries: int = 5,
        retry_delay: int = 30,
    ):
        self.reddit = reddit
        self.db = db
        self.telegram = telegram
        self.post_filter = post_filter
        self.health = health
        self.subreddits = subreddits
        self.check_interval = check_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.comment_tracker = CommentTracker(reddit, db, telegram)
        self._subreddit_str = "+".join(subreddits)

    def process_submission(self, submission) -> bool:
        """Process a single submission. Returns True if an alert was sent."""
        self.health.record_post()
        reddit_id = submission.id
        title = submission.title or ""
        url = submission.url or ""

        # Dedup check
        if is_duplicate(reddit_id, title, url, self.db):
            return False

        # Flair check - skip dead deals
        flair_info = get_flair_info(submission)
        if flair_info["is_dead_deal"]:
            logger.debug("Skipping dead deal: %s", title)
            return False

        # Filter check
        filter_result = self.post_filter.passes_filter(submission)
        if filter_result is None:
            return False

        # Extract prices
        text = f"{title} {submission.selftext or ''}"
        price_info = extract_prices(text)

        # Extract store info
        store_info = extract_store_info(text)

        # Score the post
        bot_score, alert_level = score_post(submission, filter_result, price_info)

        # Apply flair modifier
        bot_score = max(0, min(100, bot_score + flair_info["score_modifier"]))

        # Only alert for MEDIUM and above
        if bot_score < 20:
            return False

        # Save to DB
        post_data = {
            "reddit_id": reddit_id,
            "title": title,
            "selftext": (submission.selftext or "")[:1000],
            "url": url,
            "permalink": submission.permalink,
            "subreddit": str(submission.subreddit),
            "author": str(getattr(submission, "author", "")),
            "flair": flair_info["flair_text"],
            "score": getattr(submission, "score", 0),
            "num_comments": getattr(submission, "num_comments", 0),
            "price_detected": price_info["deal_price"],
            "original_price": price_info["original_price"],
            "discount_pct": price_info["discount_pct"],
            "location_detected": filter_result.get("location", ""),
            "store_number": store_info.get("store_number", ""),
            "has_image": 1 if filter_result.get("has_image") else 0,
            "bot_score": bot_score,
            "alert_level": alert_level,
            "created_utc": submission.created_utc,
        }

        post_db_id = self.db.insert_post(post_data)

        # Send alert (URGENT and HIGH immediately, MEDIUM in daily digest only)
        if alert_level in ("URGENT", "HIGH"):
            alert_data = {
                **post_data,
                "hot_keywords": filter_result.get("hot_keywords", []),
                "tool_keywords": filter_result.get("tool_keywords", []),
                "maps_url": store_info.get("maps_url"),
            }
            success = self.telegram.send_deal_alert(alert_data)
            if success:
                self.db.mark_alerted(post_db_id, alert_level, title)
                self.health.record_alert()
                logger.info(
                    "[%s] Alert sent: %s (score=%d)", alert_level, title[:60], bot_score
                )
            return success
        else:
            # MEDIUM: save but don't alert immediately (included in daily report)
            self.db.mark_alerted(post_db_id, "DIGEST", title)
            return False

    def _stream_with_retry(self):
        """Stream submissions with automatic reconnection."""
        subreddit = self.reddit.subreddit(self._subreddit_str)
        retries = 0

        while True:
            try:
                logger.info("Starting stream for r/%s", self._subreddit_str)
                for submission in subreddit.stream.submissions(skip_existing=True):
                    retries = 0  # reset on success
                    try:
                        self.process_submission(submission)
                    except Exception as e:
                        self.health.record_error(str(e))
                        logger.error("Error processing post %s: %s", submission.id, e)

            except TRANSIENT_ERRORS as e:
                retries += 1
                if retries > self.max_retries:
                    logger.critical("Max retries exceeded, restarting stream")
                    retries = 0
                delay = self.retry_delay * (2 ** (retries - 1))
                logger.warning("Stream error (retry %d/%d): %s. Waiting %ds...",
                               retries, self.max_retries, e, delay)
                self.health.record_error(str(e))
                time.sleep(delay)

    def _poll_new(self):
        """Fallback: poll subreddit.new() at check_interval."""
        subreddit = self.reddit.subreddit(self._subreddit_str)
        while True:
            try:
                for submission in subreddit.new(limit=50):
                    try:
                        self.process_submission(submission)
                    except Exception as e:
                        self.health.record_error(str(e))
                        logger.error("Error processing post: %s", e)
            except TRANSIENT_ERRORS as e:
                self.health.record_error(str(e))
                logger.warning("Poll error: %s", e)

            time.sleep(self.check_interval)

    def _periodic_search(self):
        """Search subreddits for specific keywords periodically."""
        subreddit = self.reddit.subreddit(self._subreddit_str)
        from config import SEARCH_TERMS
        search_terms = SEARCH_TERMS

        while True:
            for term in search_terms:
                try:
                    for submission in subreddit.search(term, sort="new", time_filter="hour", limit=10):
                        try:
                            self.process_submission(submission)
                        except Exception as e:
                            logger.error("Error in search result: %s", e)
                except TRANSIENT_ERRORS as e:
                    logger.warning("Search error for '%s': %s", term, e)

            time.sleep(300)  # Every 5 minutes

    def check_tracked_comments(self):
        """Check comments on high-scoring tracked posts."""
        tracked = self.db.get_tracked_posts()
        for post in tracked:
            self.comment_tracker.check_comments(
                post["reddit_id"], post["id"], "", post["permalink"]
            )

    def run(self):
        """Start the monitor using streaming with polling fallback."""
        import threading

        logger.info("PennyBot starting - monitoring r/%s", self._subreddit_str)

        # Start periodic search in background
        search_thread = threading.Thread(target=self._periodic_search, daemon=True)
        search_thread.start()

        # Start comment tracker in background
        def comment_loop():
            while True:
                try:
                    self.check_tracked_comments()
                except Exception as e:
                    logger.error("Comment tracker error: %s", e)
                time.sleep(120)  # Every 2 minutes

        comment_thread = threading.Thread(target=comment_loop, daemon=True)
        comment_thread.start()

        # Main: try stream first, fall back to polling
        try:
            self._stream_with_retry()
        except Exception as e:
            logger.error("Stream failed completely, switching to polling: %s", e)
            self._poll_new()
