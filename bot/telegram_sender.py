import logging
import time
import requests

logger = logging.getLogger(__name__)

ALERT_EMOJIS = {
    "URGENT": "\U0001f6a8",   # 🚨
    "HIGH": "\U0001f525",     # 🔥
    "MEDIUM": "\U0001f4e2",   # 📢
    "LOW": "\U0001f4ac",      # 💬
}

RATE_LIMIT_DELAY = 0.05  # 50ms between messages (well under 30/sec limit)


class TelegramSender:
    def __init__(self, bot_token: str, chat_id: str, max_retries: int = 3):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.max_retries = max_retries
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._last_send = 0

    def _rate_limit(self):
        elapsed = time.time() - self._last_send
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_send = time.time()

    def send_message(self, text: str, disable_notification: bool = False) -> bool:
        self._rate_limit()
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
            "disable_notification": disable_notification,
        }
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(
                    f"{self.base_url}/sendMessage", json=payload, timeout=10
                )
                if resp.status_code == 200:
                    return True
                if resp.status_code == 429:
                    retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
                    logger.warning("Telegram rate limited, waiting %ds", retry_after)
                    time.sleep(retry_after)
                    continue
                logger.error("Telegram error %d: %s", resp.status_code, resp.text)
            except requests.RequestException as e:
                logger.error("Telegram send failed (attempt %d): %s", attempt, e)
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
        return False

    def send_deal_alert(self, post_data: dict) -> bool:
        alert_level = post_data.get("alert_level", "MEDIUM")
        emoji = ALERT_EMOJIS.get(alert_level, "\U0001f4ac")
        score = post_data.get("bot_score", 0)
        title = post_data.get("title", "Sin titulo")
        subreddit = post_data.get("subreddit", "?")
        permalink = post_data.get("permalink", "")
        reddit_url = f"https://reddit.com{permalink}" if permalink else ""

        # Price info
        price_text = ""
        if post_data.get("price_detected"):
            price_text = f"\n\U0001f4b0 <b>Precio:</b> ${post_data['price_detected']:.2f}"
        if post_data.get("original_price"):
            price_text += f" (era ${post_data['original_price']:.2f})"
        if post_data.get("discount_pct"):
            price_text += f" - {post_data['discount_pct']:.0f}% OFF"

        # Location info
        location_text = ""
        if post_data.get("location_detected"):
            location_text = f"\n\U0001f4cd <b>Ubicacion:</b> {post_data['location_detected']}"

        # Store link
        store_text = ""
        if post_data.get("maps_url"):
            store_text = f"\n\U0001f3ea <a href=\"{post_data['maps_url']}\">Ver en Google Maps</a>"

        # Keywords matched
        keywords = post_data.get("hot_keywords", []) + post_data.get("tool_keywords", [])
        kw_text = f"\n\U0001f3af <b>Keywords:</b> {', '.join(keywords)}" if keywords else ""

        # Reddit stats
        reddit_score = post_data.get("score", 0)
        comments = post_data.get("num_comments", 0)

        text = (
            f"{emoji} <b>[{alert_level}]</b> PennyBot Alert\n"
            f"{'=' * 30}\n\n"
            f"\U0001f4dd <b>{title}</b>\n\n"
            f"\U0001f4e1 r/{subreddit} | \U0001f44d {reddit_score} | \U0001f4ac {comments}\n"
            f"\U0001f3c6 Bot Score: {score}/100"
            f"{price_text}"
            f"{location_text}"
            f"{store_text}"
            f"{kw_text}\n\n"
            f"\U0001f517 <a href=\"{reddit_url}\">Ver Post en Reddit</a>"
        )

        # URGENT alerts get sound notification, others are silent
        silent = alert_level not in ("URGENT", "HIGH")
        return self.send_message(text, disable_notification=silent)

    def send_comment_update(self, post_title: str, update_text: str, reddit_url: str) -> bool:
        text = (
            f"\U0001f504 <b>UPDATE</b>\n"
            f"\U0001f4dd {post_title}\n\n"
            f"{update_text}\n\n"
            f"\U0001f517 <a href=\"{reddit_url}\">Ver Post</a>"
        )
        return self.send_message(text, disable_notification=True)

    def send_health_report(self, report: str) -> bool:
        text = f"\U0001f3e5 <b>Health Check</b>\n<pre>{report}</pre>"
        return self.send_message(text, disable_notification=True)

    def ping(self) -> bool:
        """Test connectivity to Telegram API."""
        try:
            resp = requests.get(f"{self.base_url}/getMe", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False
