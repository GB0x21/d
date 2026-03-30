import time
import unittest
from unittest.mock import MagicMock
from bot.scoring import score_post


def make_submission(score=0, num_comments=0, created_utc=None):
    sub = MagicMock()
    sub.score = score
    sub.num_comments = num_comments
    sub.created_utc = created_utc or time.time()
    sub.title = "test"
    return sub


class TestScoring(unittest.TestCase):
    def test_hot_keyword_score(self):
        sub = make_submission()
        result = {"hot_keywords": ["penny"], "tool_keywords": [], "has_image": False, "location": "National"}
        price = {"is_penny": True, "deal_price": 0.01}
        score, level = score_post(sub, result, price)
        # 40 (hot) + 15 (recent) + 10 (penny) = 65 minimum
        self.assertGreaterEqual(score, 60)

    def test_urgent_level(self):
        sub = make_submission(score=15, num_comments=10, created_utc=time.time())
        result = {"hot_keywords": ["penny"], "tool_keywords": ["milwaukee"], "has_image": True, "location": "SF"}
        price = {"is_penny": True, "deal_price": 0.01}
        score, level = score_post(sub, result, price)
        self.assertEqual(level, "URGENT")
        self.assertGreaterEqual(score, 70)

    def test_low_score(self):
        sub = make_submission(created_utc=time.time() - 7200)  # 2 hours old
        result = {"hot_keywords": [], "tool_keywords": ["ryobi"], "has_image": False, "location": "National"}
        price = {"is_penny": False, "deal_price": 15.99}
        score, level = score_post(sub, result, price)
        self.assertEqual(score, 20)  # Only tool keyword
        self.assertEqual(level, "MEDIUM")

    def test_medium_with_image(self):
        sub = make_submission(created_utc=time.time() - 7200)
        result = {"hot_keywords": [], "tool_keywords": ["dewalt"], "has_image": True, "location": "National"}
        price = {"is_penny": False, "deal_price": None}
        score, level = score_post(sub, result, price)
        self.assertEqual(score, 30)  # 20 (tool) + 10 (image)

    def test_bay_area_bonus(self):
        sub = make_submission(created_utc=time.time() - 7200)
        result = {"hot_keywords": ["clearance"], "tool_keywords": [], "has_image": False, "location": "Oakland"}
        price = {"is_penny": False, "deal_price": 5.00}
        score, level = score_post(sub, result, price)
        # 40 (hot) + 5 (Bay Area) = 45
        self.assertEqual(score, 45)


if __name__ == "__main__":
    unittest.main()
