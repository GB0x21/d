import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import field_validator

load_dotenv()


def _split_csv(v: str) -> list[str]:
    return [item.strip() for item in v.split(",") if item.strip()]


class RedditConfig(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    user_agent: str = "python:PennyBot:v1.0 (by /u/PennyBotUser)"

    model_config = {"env_prefix": "REDDIT_"}

    @field_validator("client_id", "client_secret")
    @classmethod
    def must_not_be_placeholder(cls, v: str) -> str:
        if not v or v.startswith("TU_"):
            raise ValueError("Missing required Reddit credential")
        return v


class TelegramConfig(BaseSettings):
    bot_token: str = ""
    chat_id: str = ""

    model_config = {"env_prefix": "TELEGRAM_"}

    @field_validator("bot_token", "chat_id")
    @classmethod
    def must_not_be_placeholder(cls, v: str) -> str:
        if not v or v.startswith("TU_"):
            raise ValueError("Missing required Telegram credential")
        return v


class Settings(BaseSettings):
    reddit: RedditConfig = RedditConfig()
    telegram: TelegramConfig = TelegramConfig()

    # Monitoring
    target_subreddits: str = "HomeDepotPennyItems,HomeDepot,deals,Flipping,coupons,blackfriday,amazonunder25"
    check_interval: int = 60

    # Keywords
    keywords_hot: str = "penny,0.01,glitch,clearance,liquidation,inventory,price error,unmarked,manager special"
    keywords_tools: str = "Milwaukee,DeWalt,Makita,Ryobi,Packout,Insulation,Drywall,Power Tools,Lumber"
    keywords_exclude: str = "expired,sold out,scam,fake,question,help,discussion,meme"
    search_terms: str = "penny,0.01,price error,clearance glitch"

    # Location
    locations: str = "Bay Area,SF,San Francisco,Oakland,San Jose,Hayward,Concord,Fremont,San Mateo,Richmond,Walnut Creek,East Bay,California,CA,NorCal,National,Online"

    # Technical
    db_path: str = "alerts_history.db"
    log_level: str = "INFO"
    max_retries: int = 5
    retry_delay: int = 30
    require_image: bool = False

    @property
    def subreddits_list(self) -> list[str]:
        return _split_csv(self.target_subreddits)

    @property
    def hot_keywords_list(self) -> list[str]:
        return _split_csv(self.keywords_hot)

    @property
    def tool_keywords_list(self) -> list[str]:
        return _split_csv(self.keywords_tools)

    @property
    def exclude_keywords_list(self) -> list[str]:
        return _split_csv(self.keywords_exclude)

    @property
    def search_terms_list(self) -> list[str]:
        return _split_csv(self.search_terms)

    @property
    def locations_list(self) -> list[str]:
        return _split_csv(self.locations)


def load_settings() -> Settings:
    return Settings()


# Backward-compatible module-level constants for existing code
_settings = None


def _get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def __getattr__(name: str):
    """Provide backward-compatible access to config values as module attributes."""
    _map = {
        "REDDIT_CLIENT_ID": lambda s: s.reddit.client_id,
        "REDDIT_CLIENT_SECRET": lambda s: s.reddit.client_secret,
        "REDDIT_USER_AGENT": lambda s: s.reddit.user_agent,
        "TELEGRAM_BOT_TOKEN": lambda s: s.telegram.bot_token,
        "TELEGRAM_CHAT_ID": lambda s: s.telegram.chat_id,
        "TARGET_SUBREDDITS": lambda s: s.subreddits_list,
        "CHECK_INTERVAL": lambda s: s.check_interval,
        "KEYWORDS_HOT": lambda s: s.hot_keywords_list,
        "KEYWORDS_TOOLS": lambda s: s.tool_keywords_list,
        "KEYWORDS_EXCLUDE": lambda s: s.exclude_keywords_list,
        "SEARCH_TERMS": lambda s: s.search_terms_list,
        "LOCATIONS": lambda s: s.locations_list,
        "DB_PATH": lambda s: s.db_path,
        "LOG_LEVEL": lambda s: s.log_level,
        "MAX_RETRIES": lambda s: s.max_retries,
        "RETRY_DELAY": lambda s: s.retry_delay,
        "REQUIRE_IMAGE": lambda s: s.require_image,
    }
    if name in _map:
        return _map[name](_get_settings())
    raise AttributeError(f"module 'config' has no attribute {name!r}")
