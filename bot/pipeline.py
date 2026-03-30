"""Processing pipeline: dedup -> filter -> score -> alert."""

import logging

from bot.dedup import is_duplicate
from bot.flair_detector import get_flair_info
from bot.filters import PostFilter
from bot.scoring import score_post
from bot.price_extractor import extract_prices
from bot.store_locator import extract_store_info
from bot.telegram_sender import TelegramSender
from database.db_manager import DBManager
from utils.health import HealthMonitor

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(
        self,
        post_filter: PostFilter,
        db: DBManager,
        telegram: TelegramSender,
        health: HealthMonitor,
    ):
        self.post_filter = post_filter
        self.db = db
        self.telegram = telegram
        self.health = health

    def process(self, submission) -> bool:
        """Run a submission through the full pipeline. Returns True if alert sent."""
        self.health.record_post()
        reddit_id = submission.id
        title = submission.title or ""
        url = submission.url or ""

        # Step 1: Dedup
        if is_duplicate(reddit_id, title, url, self.db):
            return False

        # Step 2: Flair check - skip dead deals
        flair_info = get_flair_info(submission)
        if flair_info["is_dead_deal"]:
            logger.debug("Skipping dead deal: %s", title)
            return False

        # Step 3: Keyword + location filter
        filter_result = self.post_filter.passes_filter(submission)
        if filter_result is None:
            return False

        # Step 4: Price extraction
        text = f"{title} {submission.selftext or ''}"
        price_info = extract_prices(text)

        # Step 5: Store locator
        store_info = extract_store_info(text)

        # Step 6: Scoring
        bot_score, alert_level = score_post(submission, filter_result, price_info)
        bot_score = max(0, min(100, bot_score + flair_info["score_modifier"]))

        if bot_score < 20:
            return False

        # Step 7: Save to DB
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

        # Step 8: Send alert
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
                logger.info("[%s] Alert sent: %s (score=%d)", alert_level, title[:60], bot_score)
            return success
        else:
            self.db.mark_alerted(post_db_id, "DIGEST", title)
            return False
