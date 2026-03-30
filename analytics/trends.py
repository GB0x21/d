import logging
from collections import Counter

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_top_subreddits(self, days: int = 30) -> list[tuple[str, int]]:
        """Get most productive subreddits by alert count."""
        from datetime import datetime, timedelta

        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        rows = self.db.conn.execute(
            "SELECT subreddit, COUNT(*) as cnt FROM posts "
            "WHERE discovered_at >= ? AND alerted_at IS NOT NULL "
            "GROUP BY subreddit ORDER BY cnt DESC LIMIT 10",
            (cutoff,),
        ).fetchall()
        return [(r["subreddit"], r["cnt"]) for r in rows]

    def get_best_hours(self, days: int = 30) -> list[tuple[int, int]]:
        """Get hours with most penny deals historically."""
        return self.db.get_hourly_distribution()

    def get_keyword_effectiveness(self, days: int = 30) -> dict:
        """Analyze which keywords produce real deals vs false positives."""
        from datetime import datetime, timedelta

        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        rows = self.db.conn.execute(
            "SELECT title, selftext, alert_level, bot_score FROM posts "
            "WHERE discovered_at >= ?",
            (cutoff,),
        ).fetchall()

        keyword_stats = Counter()
        keyword_high = Counter()

        for row in rows:
            text = f"{row['title']} {row['selftext']}".lower()
            for kw in ["penny", "clearance", "glitch", "price error", "liquidation"]:
                if kw in text:
                    keyword_stats[kw] += 1
                    if row["alert_level"] in ("URGENT", "HIGH"):
                        keyword_high[kw] += 1

        result = {}
        for kw, total in keyword_stats.most_common():
            high = keyword_high.get(kw, 0)
            result[kw] = {
                "total": total,
                "high_quality": high,
                "hit_rate": round(high / total * 100, 1) if total else 0,
            }
        return result

    def get_price_distribution(self, days: int = 30) -> dict:
        """Analyze price distribution of deals found."""
        from datetime import datetime, timedelta

        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        rows = self.db.conn.execute(
            "SELECT price_detected FROM posts "
            "WHERE discovered_at >= ? AND price_detected IS NOT NULL",
            (cutoff,),
        ).fetchall()

        prices = [r["price_detected"] for r in rows]
        if not prices:
            return {"count": 0}

        penny = sum(1 for p in prices if p <= 0.10)
        under_5 = sum(1 for p in prices if 0.10 < p <= 5)
        under_20 = sum(1 for p in prices if 5 < p <= 20)
        above_20 = sum(1 for p in prices if p > 20)

        return {
            "count": len(prices),
            "penny_deals": penny,
            "under_5": under_5,
            "under_20": under_20,
            "above_20": above_20,
            "avg_price": round(sum(prices) / len(prices), 2),
            "min_price": min(prices),
        }
