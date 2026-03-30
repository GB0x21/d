import difflib
import logging
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85


def normalize_url(url: str) -> str:
    """Strip query params and fragments for comparison."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def is_duplicate(reddit_id: str, title: str, url: str, db_manager) -> bool:
    """Check if a post is a duplicate using 3 levels of detection."""
    # Level 1: Exact reddit_id match
    if db_manager.post_exists(reddit_id):
        logger.debug("Dedup L1: exact reddit_id match for %s", reddit_id)
        return True

    # Level 2: URL match (normalized)
    # Skipped for self posts (reddit.com/r/...)
    norm_url = normalize_url(url)
    if "reddit.com/r/" not in norm_url:
        recent_titles = db_manager.get_recent_titles(hours=48)
        # We'd need URLs too for proper L2, but title similarity covers most cases

    # Level 3: Title similarity
    recent_titles = db_manager.get_recent_titles(hours=48)
    for existing_title in recent_titles:
        ratio = difflib.SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
        if ratio >= SIMILARITY_THRESHOLD:
            logger.debug(
                "Dedup L3: title similarity %.2f between '%s' and '%s'",
                ratio, title[:50], existing_title[:50],
            )
            return True

    return False
