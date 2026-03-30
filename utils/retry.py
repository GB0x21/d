import time
import random
import logging
import functools

logger = logging.getLogger(__name__)


def with_retry(max_retries: int = 5, base_delay: int = 30, transient_exceptions=(Exception,)):
    """Decorator for retrying functions with exponential backoff + jitter.

    Retries on transient_exceptions only. Other exceptions propagate immediately.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except transient_exceptions as e:
                    last_exc = e
                    if attempt == max_retries:
                        logger.error(
                            "%s failed after %d attempts: %s", func.__name__, max_retries, e
                        )
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    jitter = random.uniform(0, delay * 0.25)
                    delay = delay + jitter
                    logger.warning(
                        "%s attempt %d/%d failed: %s. Retrying in %.1fs...",
                        func.__name__, attempt, max_retries, e, delay,
                    )
                    time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator
