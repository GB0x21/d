import unittest
from unittest.mock import MagicMock
from bot.filters import PostFilter


def make_submission(title="", selftext="", url="", is_gallery=False):
    sub = MagicMock()
    sub.title = title
    sub.selftext = selftext
    sub.url = url
    sub.is_gallery = is_gallery
    return sub


class TestPostFilter(unittest.TestCase):
    def setUp(self):
        self.f = PostFilter(
            keywords_hot=["penny", "0.01", "clearance"],
            keywords_tools=["Milwaukee", "DeWalt"],
            keywords_exclude=["expired", "sold out"],
            locations=["Bay Area", "SF", "National", "Online"],
        )

    def test_hot_keyword_match(self):
        sub = make_submission(title="Penny deal at Home Depot!")
        result = self.f.passes_filter(sub)
        self.assertIsNotNone(result)
        self.assertIn("penny", result["hot_keywords"])

    def test_tool_keyword_match(self):
        sub = make_submission(title="Milwaukee drill clearance")
        result = self.f.passes_filter(sub)
        self.assertIsNotNone(result)
        self.assertIn("milwaukee", result["tool_keywords"])
        self.assertIn("clearance", result["hot_keywords"])

    def test_excluded_keyword(self):
        sub = make_submission(title="Penny deal expired already")
        result = self.f.passes_filter(sub)
        self.assertIsNone(result)

    def test_no_keywords(self):
        sub = make_submission(title="Just a regular post about home improvement")
        result = self.f.passes_filter(sub)
        self.assertIsNone(result)

    def test_location_filter_bay_area(self):
        sub = make_submission(title="Penny deal in SF store")
        result = self.f.passes_filter(sub)
        self.assertIsNotNone(result)
        self.assertEqual(result["location"], "sf")

    def test_no_location_passes_as_national(self):
        sub = make_submission(title="Penny deal found!")
        result = self.f.passes_filter(sub)
        self.assertIsNotNone(result)
        self.assertEqual(result["location"], "National")

    def test_has_image_imgur(self):
        sub = make_submission(title="test", url="https://i.imgur.com/abc.jpg")
        self.assertTrue(self.f.has_image(sub))

    def test_has_image_redd(self):
        sub = make_submission(title="test", url="https://i.redd.it/abc.png")
        self.assertTrue(self.f.has_image(sub))

    def test_require_image_filter(self):
        f = PostFilter(
            keywords_hot=["penny"],
            keywords_tools=[],
            keywords_exclude=[],
            locations=["National"],
            require_image=True,
        )
        sub = make_submission(title="Penny deal", url="https://reddit.com/r/test")
        result = f.passes_filter(sub)
        self.assertIsNone(result)

    def test_selftext_keyword(self):
        sub = make_submission(title="Check this out", selftext="Found a penny item at HD")
        result = self.f.passes_filter(sub)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
