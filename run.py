#!/usr/bin/env python3
"""PennyBot - Reddit Penny Deal Monitor for Telegram."""

import signal
import sys
import threading
import praw

import config
from utils.logger import setup_logger
from utils.health import HealthMonitor
from database.db_manager import DBManager
from bot.filters import PostFilter
from bot.telegram_sender import TelegramSender
from bot.reddit_monitor import RedditMonitor
from analytics.reporter import DailyReporter

logger = setup_logger(config.LOG_LEVEL)


def main():
    logger.info("Initializing PennyBot...")

    # Database
    db = DBManager(config.DB_PATH)
    db.connect()

    # Reddit
    reddit = praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent=config.REDDIT_USER_AGENT,
    )
    logger.info("Reddit connected as read-only")

    # Telegram
    telegram = TelegramSender(
        bot_token=config.TELEGRAM_BOT_TOKEN,
        chat_id=config.TELEGRAM_CHAT_ID,
    )
    if telegram.ping():
        logger.info("Telegram bot connected")
    else:
        logger.error("Could not connect to Telegram - check BOT_TOKEN")
        sys.exit(1)

    # Filters
    post_filter = PostFilter(
        keywords_hot=config.KEYWORDS_HOT,
        keywords_tools=config.KEYWORDS_TOOLS,
        keywords_exclude=config.KEYWORDS_EXCLUDE,
        locations=config.LOCATIONS,
        require_image=config.REQUIRE_IMAGE,
    )

    # Health monitor
    health = HealthMonitor()

    # Daily reporter (runs in background)
    reporter = DailyReporter(db, telegram)
    reporter.start()

    # Health check thread
    def health_loop():
        import time
        while True:
            time.sleep(600)  # Every 10 minutes
            if health.is_stale:
                telegram.send_health_report(health.get_status_report())

    health_thread = threading.Thread(target=health_loop, daemon=True)
    health_thread.start()

    # Reddit monitor
    monitor = RedditMonitor(
        reddit=reddit,
        db=db,
        telegram=telegram,
        post_filter=post_filter,
        health=health,
        subreddits=config.TARGET_SUBREDDITS,
        check_interval=config.CHECK_INTERVAL,
        max_retries=config.MAX_RETRIES,
        retry_delay=config.RETRY_DELAY,
    )

    # Graceful shutdown
    def shutdown(signum, frame):
        logger.info("Shutting down PennyBot...")
        reporter.stop()
        db.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Send startup notification
    telegram.send_message(
        "\U0001f916 <b>PennyBot Online</b>\n"
        f"Monitoring: {', '.join(config.TARGET_SUBREDDITS)}\n"
        f"Check interval: {config.CHECK_INTERVAL}s"
    )

    # Start monitoring
    monitor.run()


if __name__ == "__main__":
    main()
