SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reddit_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    selftext TEXT DEFAULT '',
    url TEXT NOT NULL,
    permalink TEXT NOT NULL,
    subreddit TEXT NOT NULL,
    author TEXT DEFAULT '',
    flair TEXT DEFAULT '',
    score INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    price_detected REAL,
    original_price REAL,
    discount_pct REAL,
    location_detected TEXT DEFAULT '',
    store_number TEXT DEFAULT '',
    has_image INTEGER DEFAULT 0,
    bot_score INTEGER DEFAULT 0,
    alert_level TEXT DEFAULT '',
    created_utc REAL NOT NULL,
    discovered_at TEXT NOT NULL DEFAULT (datetime('now')),
    alerted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_posts_reddit_id ON posts(reddit_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_utc ON posts(created_utc);
CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);
CREATE INDEX IF NOT EXISTS idx_posts_alert_level ON posts(alert_level);

CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    message_text TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

CREATE TABLE IF NOT EXISTS comment_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    reddit_comment_id TEXT UNIQUE NOT NULL,
    body TEXT NOT NULL,
    sentiment TEXT DEFAULT 'neutral',
    author TEXT DEFAULT '',
    created_utc REAL NOT NULL,
    discovered_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

CREATE INDEX IF NOT EXISTS idx_comment_updates_post_id ON comment_updates(post_id);

CREATE TABLE IF NOT EXISTS daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    total_posts_scanned INTEGER DEFAULT 0,
    total_alerts_sent INTEGER DEFAULT 0,
    urgent_alerts INTEGER DEFAULT 0,
    high_alerts INTEGER DEFAULT 0,
    top_subreddit TEXT DEFAULT '',
    top_keyword TEXT DEFAULT ''
);
"""
