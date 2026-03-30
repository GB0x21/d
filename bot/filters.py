import re
import logging

logger = logging.getLogger(__name__)


class PostFilter:
    def __init__(
        self,
        keywords_hot: list[str],
        keywords_tools: list[str],
        keywords_exclude: list[str],
        locations: list[str],
        require_image: bool = False,
    ):
        self.keywords_hot = [kw.lower() for kw in keywords_hot]
        self.keywords_tools = [kw.lower() for kw in keywords_tools]
        self.keywords_exclude = [kw.lower() for kw in keywords_exclude]
        self.locations = [loc.lower() for loc in locations]
        self.require_image = require_image

    def _combine_text(self, submission) -> str:
        title = getattr(submission, "title", "") or ""
        selftext = getattr(submission, "selftext", "") or ""
        return f"{title} {selftext}".lower()

    def has_image(self, submission) -> bool:
        url = getattr(submission, "url", "") or ""
        if any(url.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
            return True
        if "i.redd.it" in url or "i.imgur.com" in url:
            return True
        if getattr(submission, "is_gallery", False):
            return True
        return False

    def is_excluded(self, submission) -> bool:
        text = self._combine_text(submission)
        for kw in self.keywords_exclude:
            if kw in text:
                logger.debug("Post excluded by keyword '%s': %s", kw, getattr(submission, "title", ""))
                return True
        return False

    def matches_hot(self, submission) -> list[str]:
        text = self._combine_text(submission)
        return [kw for kw in self.keywords_hot if kw in text]

    def matches_tools(self, submission) -> list[str]:
        text = self._combine_text(submission)
        return [kw for kw in self.keywords_tools if kw in text]

    def matches_location(self, submission) -> tuple[bool, str]:
        """Returns (matches, detected_location).

        Posts without any location mention are treated as national/general
        and pass the filter.
        """
        text = self._combine_text(submission)
        for loc in self.locations:
            if loc in text:
                return True, loc
        # No location mentioned = assume national, allow through
        return True, "National"

    def passes_filter(self, submission) -> dict | None:
        """Returns filter result dict if post passes, None if rejected."""
        if self.is_excluded(submission):
            return None

        hot_matches = self.matches_hot(submission)
        tool_matches = self.matches_tools(submission)

        if not hot_matches and not tool_matches:
            return None

        if self.require_image and not self.has_image(submission):
            logger.debug("Post rejected (no image): %s", getattr(submission, "title", ""))
            return None

        loc_match, loc_name = self.matches_location(submission)
        if not loc_match:
            return None

        return {
            "hot_keywords": hot_matches,
            "tool_keywords": tool_matches,
            "location": loc_name,
            "has_image": self.has_image(submission),
        }
