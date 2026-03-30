import logging

logger = logging.getLogger(__name__)

# Flair categories and their score modifiers
FLAIR_BOOSTS = {
    # Positive flairs (boost score)
    "penny": 15,
    "clearance": 10,
    "deal": 10,
    "in stock": 10,
    "verified": 10,
    "ymmv": 5,
    "hot": 10,
    "price match": 5,
    "online": 5,
    # Negative flairs (reduce score)
    "expired": -50,
    "sold out": -50,
    "dead": -50,
    "discussion": -30,
    "question": -30,
    "meta": -30,
    "meme": -40,
}


def get_flair_info(submission) -> dict:
    """Extract flair and return category info with score modifier."""
    flair = getattr(submission, "link_flair_text", "") or ""
    flair_lower = flair.lower().strip()

    result = {
        "flair_text": flair,
        "score_modifier": 0,
        "is_dead_deal": False,
    }

    if not flair_lower:
        return result

    for keyword, modifier in FLAIR_BOOSTS.items():
        if keyword in flair_lower:
            result["score_modifier"] = modifier
            if modifier <= -30:
                result["is_dead_deal"] = True
            break

    logger.debug("Flair '%s' -> modifier %d", flair, result["score_modifier"])
    return result
