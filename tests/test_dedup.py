import unittest
from unittest.mock import MagicMock
from bot.dedup import is_duplicate, normalize_url


class TestNormalizeUrl(unittest.TestCase):
    def test_strips_query_params(self):
        url = "https://example.com/page?ref=123&utm=abc"
        self.assertEqual(normalize_url(url), "https://example.com/page")

    def test_strips_fragment(self):
        url = "https://example.com/page#section"
        self.assertEqual(normalize_url(url), "https://example.com/page")

    def test_preserves_path(self):
        url = "https://reddit.com/r/deals/comments/abc123/great_deal"
        self.assertEqual(normalize_url(url), "https://reddit.com/r/deals/comments/abc123/great_deal")


class TestIsDuplicate(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.post_exists.return_value = False
        self.db.get_recent_titles.return_value = []

    def test_exact_id_match(self):
        self.db.post_exists.return_value = True
        self.assertTrue(is_duplicate("abc123", "title", "http://example.com", self.db))

    def test_no_match(self):
        self.db.get_recent_titles.return_value = ["Completely different title"]
        self.assertFalse(is_duplicate("xyz", "Penny deal at HD", "http://example.com", self.db))

    def test_similar_title(self):
        self.db.get_recent_titles.return_value = ["Penny deal at Home Depot store 1234"]
        self.assertTrue(is_duplicate("xyz", "Penny deal at Home Depot store 1234!", "http://example.com", self.db))

    def test_different_titles(self):
        self.db.get_recent_titles.return_value = ["Milwaukee drill on sale"]
        self.assertFalse(is_duplicate("xyz", "DeWalt saw clearance", "http://example.com", self.db))


if __name__ == "__main__":
    unittest.main()
