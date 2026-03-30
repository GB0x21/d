import time
import logging

logger = logging.getLogger(__name__)

# Alert level thresholds
URGENT_THRESHOLD = 70
HIGH_THRESHOLD = 40
MEDIUM_THRESHOLD = 20


def score_post(submission, filter_result: dict, price_info: dict) -> tuple[int, str]:
    """Score a post 0-100 and return (score, alert_level)."""
    score = 0

    # Hot keyword match (+40)
    if filter_result.get("hot_keywords"):
        score += 40

    # Tool keyword match (+20)
    if filter_result.get("tool_keywords"):
        score += 20

    # Post recency: < 30 min (+15)
    created = getattr(submission, "created_utc", 0)
    age_minutes = (time.time() - created) / 60 if created else 999
    if age_minutes < 30:
        score += 15

    # Has image (+10)
    if filter_result.get("has_image"):
        score += 10

    # Reddit score > 10 (+5)
    reddit_score = getattr(submission, "score", 0) or 0
    if reddit_score > 10:
        score += 5

    # Comments > 5 (+5)
    num_comments = getattr(submission, "num_comments", 0) or 0
    if num_comments > 5:
        score += 5

    # Bay Area specific location (+5)
    location = filter_result.get("location", "")
    if location and location.lower() not in ("national", "online"):
        score += 5

    # Penny deal bonus (+10)
    if price_info.get("is_penny"):
        score += 10

    # Cap at 100
    score = min(score, 100)

    # Determine alert level
    if score >= URGENT_THRESHOLD:
        alert_level = "URGENT"
    elif score >= HIGH_THRESHOLD:
        alert_level = "HIGH"
    elif score >= MEDIUM_THRESHOLD:
        alert_level = "MEDIUM"
    else:
        alert_level = "LOW"

    logger.debug("Post scored %d (%s): %s", score, alert_level, getattr(submission, "title", ""))
    return score, alert_level
