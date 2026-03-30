import re
import logging
import praw

logger = logging.getLogger(__name__)

CONFIRM_PHRASES = [
    "confirmed", "just got one", "just picked up", "in stock",
    "worked for me", "can confirm", "still available", "just bought",
    "ringing up", "scanning at", "found it", "grabbed one",
]

DENY_PHRASES = [
    "expired", "dead", "sold out", "out of stock", "price went back",
    "manager stopped", "no longer", "doesn't work", "fixed the price",
    "back to normal", "not working",
]

LOCATION_PATTERN = re.compile(
    r"(?:store|location)\s*#?\s*\d{4}|"
    r"\b(?:Bay Area|SF|San Francisco|Oakland|San Jose|Fremont|Concord|Hayward)\b",
    re.IGNORECASE,
)


def classify_comment(body: str) -> str:
    """Classify comment as 'positive', 'negative', or 'neutral'."""
    body_lower = body.lower()
    for phrase in CONFIRM_PHRASES:
        if phrase in body_lower:
            return "positive"
    for phrase in DENY_PHRASES:
        if phrase in body_lower:
            return "negative"
    return "neutral"


def has_location_mention(body: str) -> bool:
    return bool(LOCATION_PATTERN.search(body))


class CommentTracker:
    def __init__(self, reddit: praw.Reddit, db_manager, telegram_sender):
        self.reddit = reddit
        self.db = db_manager
        self.telegram = telegram_sender

    def check_comments(self, post_reddit_id: str, post_db_id: int, post_title: str, permalink: str):
        """Check new comments on a tracked post and send updates."""
        try:
            submission = self.reddit.submission(id=post_reddit_id)
            submission.comments.replace_more(limit=0)

            positives = 0
            negatives = 0
            location_mentions = []

            for comment in submission.comments.list():
                comment_id = comment.id
                if self.db.comment_exists(comment_id):
                    continue

                body = comment.body or ""
                sentiment = classify_comment(body)

                self.db.insert_comment_update({
                    "post_id": post_db_id,
                    "reddit_comment_id": comment_id,
                    "body": body[:500],
                    "sentiment": sentiment,
                    "author": str(getattr(comment, "author", "")),
                    "created_utc": comment.created_utc,
                })

                if sentiment == "positive":
                    positives += 1
                elif sentiment == "negative":
                    negatives += 1

                if has_location_mention(body):
                    location_mentions.append(body[:200])

            # Send update if significant activity
            if positives >= 2 or negatives >= 2 or location_mentions:
                update_parts = []
                if positives:
                    update_parts.append(f"\u2705 {positives} confirmaciones")
                if negatives:
                    update_parts.append(f"\u274c {negatives} reportes negativos")
                if location_mentions:
                    update_parts.append(f"\U0001f4cd Ubicaciones mencionadas: {len(location_mentions)}")

                reddit_url = f"https://reddit.com{permalink}"
                self.telegram.send_comment_update(
                    post_title, "\n".join(update_parts), reddit_url
                )

        except Exception as e:
            logger.error("Error tracking comments for %s: %s", post_reddit_id, e)
