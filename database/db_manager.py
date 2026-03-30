import sqlite3
import logging
from datetime import datetime, timedelta
from database.models import SCHEMA_SQL

logger = logging.getLogger(__name__)


class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def connect(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()
        logger.info("Database initialized at %s", self.db_path)

    def close(self):
        if self._conn:
            self._conn.close()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.connect()
        return self._conn

    def post_exists(self, reddit_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM posts WHERE reddit_id = ?", (reddit_id,)
        ).fetchone()
        return row is not None

    def insert_post(self, data: dict) -> int:
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        cursor = self.conn.execute(
            f"INSERT INTO posts ({cols}) VALUES ({placeholders})",
            list(data.values()),
        )
        self.conn.commit()
        return cursor.lastrowid

    def mark_alerted(self, post_db_id: int, alert_type: str, message_text: str):
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "UPDATE posts SET alerted_at = ? WHERE id = ?", (now, post_db_id)
        )
        self.conn.execute(
            "INSERT INTO alert_history (post_id, alert_type, message_text) VALUES (?, ?, ?)",
            (post_db_id, alert_type, message_text),
        )
        self.conn.commit()

    def insert_comment_update(self, data: dict):
        try:
            cols = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            self.conn.execute(
                f"INSERT INTO comment_updates ({cols}) VALUES ({placeholders})",
                list(data.values()),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # duplicate comment

    def comment_exists(self, reddit_comment_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM comment_updates WHERE reddit_comment_id = ?",
            (reddit_comment_id,),
        ).fetchone()
        return row is not None

    def get_recent_titles(self, hours: int = 48) -> list[str]:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        rows = self.conn.execute(
            "SELECT title FROM posts WHERE discovered_at >= ?", (cutoff,)
        ).fetchall()
        return [r["title"] for r in rows]

    def get_tracked_posts(self) -> list[dict]:
        cutoff = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        rows = self.conn.execute(
            "SELECT id, reddit_id, permalink, bot_score FROM posts "
            "WHERE bot_score >= 40 AND discovered_at >= ? AND alerted_at IS NOT NULL",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_daily_deals(self, date: str = None) -> list[dict]:
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        rows = self.conn.execute(
            "SELECT * FROM posts WHERE date(discovered_at) = ? ORDER BY bot_score DESC",
            (date,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_weekly_stats(self) -> dict:
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        row = self.conn.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN alerted_at IS NOT NULL THEN 1 ELSE 0 END) as alerted, "
            "SUM(CASE WHEN alert_level = 'URGENT' THEN 1 ELSE 0 END) as urgent "
            "FROM posts WHERE discovered_at >= ?",
            (cutoff,),
        ).fetchone()
        top_sub = self.conn.execute(
            "SELECT subreddit, COUNT(*) as cnt FROM posts "
            "WHERE discovered_at >= ? AND alerted_at IS NOT NULL "
            "GROUP BY subreddit ORDER BY cnt DESC LIMIT 1",
            (cutoff,),
        ).fetchone()
        return {
            "total_scanned": row["total"] or 0,
            "total_alerted": row["alerted"] or 0,
            "urgent_count": row["urgent"] or 0,
            "top_subreddit": top_sub["subreddit"] if top_sub else "N/A",
        }

    def get_hourly_distribution(self) -> list[tuple]:
        rows = self.conn.execute(
            "SELECT CAST(strftime('%H', discovered_at) AS INTEGER) as hour, COUNT(*) as cnt "
            "FROM posts WHERE alerted_at IS NOT NULL "
            "GROUP BY hour ORDER BY cnt DESC"
        ).fetchall()
        return [(r["hour"], r["cnt"]) for r in rows]

    def update_daily_stats(self, stats: dict):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        self.conn.execute(
            "INSERT OR REPLACE INTO daily_stats "
            "(date, total_posts_scanned, total_alerts_sent, urgent_alerts, high_alerts, top_subreddit, top_keyword) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                today,
                stats.get("total_posts_scanned", 0),
                stats.get("total_alerts_sent", 0),
                stats.get("urgent_alerts", 0),
                stats.get("high_alerts", 0),
                stats.get("top_subreddit", ""),
                stats.get("top_keyword", ""),
            ),
        )
        self.conn.commit()
