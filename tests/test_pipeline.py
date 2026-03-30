import time
import unittest
from unittest.mock import MagicMock, patch
from bot.pipeline import Pipeline
from bot.filters import PostFilter
from utils.health import HealthMonitor


def make_submission(
    reddit_id="abc123",
    title="",
    selftext="",
    url="https://reddit.com/r/test",
    score=0,
    num_comments=0,
    created_utc=None,
    link_flair_text="",
    is_gallery=False,
):
    sub = MagicMock()
    sub.id = reddit_id
    sub.title = title
    sub.selftext = selftext
    sub.url = url
    sub.permalink = f"/r/test/comments/{reddit_id}/post"
    sub.subreddit = "HomeDepotPennyItems"
    sub.author = "testuser"
    sub.score = score
    sub.num_comments = num_comments
    sub.created_utc = created_utc or time.time()
    sub.link_flair_text = link_flair_text
    sub.is_gallery = is_gallery
    return sub


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.post_exists.return_value = False
        self.db.get_recent_titles.return_value = []
        self.db.insert_post.return_value = 1

        self.telegram = MagicMock()
        self.telegram.send_deal_alert.return_value = True

        self.health = HealthMonitor()

        self.post_filter = PostFilter(
            keywords_hot=["penny", "0.01", "clearance"],
            keywords_tools=["Milwaukee", "DeWalt"],
            keywords_exclude=["expired", "sold out"],
            locations=["Bay Area", "SF", "National", "Online"],
        )

        self.pipeline = Pipeline(
            post_filter=self.post_filter,
            db=self.db,
            telegram=self.telegram,
            health=self.health,
        )

    def test_duplicate_rejected(self):
        self.db.post_exists.return_value = True
        sub = make_submission(title="Penny deal at HD")
        result = self.pipeline.process(sub)
        self.assertFalse(result)
        self.db.insert_post.assert_not_called()

    def test_excluded_keyword_rejected(self):
        sub = make_submission(title="Penny deal expired already")
        result = self.pipeline.process(sub)
        self.assertFalse(result)
        self.db.insert_post.assert_not_called()

    def test_no_keywords_rejected(self):
        sub = make_submission(title="Just a regular home improvement post")
        result = self.pipeline.process(sub)
        self.assertFalse(result)

    def test_dead_deal_flair_rejected(self):
        sub = make_submission(title="Penny deal at HD", link_flair_text="Expired")
        result = self.pipeline.process(sub)
        self.assertFalse(result)

    def test_hot_keyword_sends_alert(self):
        sub = make_submission(
            title="Penny item $0.01 at Home Depot!",
            score=20,
            num_comments=10,
            created_utc=time.time(),
        )
        result = self.pipeline.process(sub)
        self.assertTrue(result)
        self.telegram.send_deal_alert.assert_called_once()
        self.db.insert_post.assert_called_once()

    def test_medium_score_no_immediate_alert(self):
        # Tool keyword only (no hot keyword) = 20 pts = MEDIUM -> digest only
        sub = make_submission(
            title="DeWalt drill combo kit sale",
            created_utc=time.time() - 7200,  # 2 hours old
        )
        result = self.pipeline.process(sub)
        self.assertFalse(result)  # MEDIUM goes to digest, not immediate
        self.db.insert_post.assert_called_once()
        self.telegram.send_deal_alert.assert_not_called()

    def test_store_info_included_in_alert(self):
        sub = make_submission(
            title="Penny deal at store #0644 in Pittsburg!",
            score=15,
            num_comments=8,
            created_utc=time.time(),
        )
        self.pipeline.process(sub)
        if self.telegram.send_deal_alert.called:
            alert_data = self.telegram.send_deal_alert.call_args[0][0]
            self.assertIsNotNone(alert_data.get("maps_url"))

    def test_health_records_post(self):
        sub = make_submission(title="Penny deal at HD")
        self.pipeline.process(sub)
        self.assertEqual(self.health.posts_processed, 1)


if __name__ == "__main__":
    unittest.main()
