"""
Retry utilities with exponential backoff.

Provides decorator for retrying failed operations with configurable
backoff strategies for improved reliability.
"""

from collections.abc import Callable
from typing import TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

T = TypeVar("T")


def retry_with_backoff(
    max_attempts: int | None = None,
    min_wait: int = 1,
    max_wait: int = 60,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying operations with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default from settings)
        min_wait: Minimum wait time in seconds between retries
        max_wait: Maximum wait time in seconds between retries
        exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(max_attempts=5, exceptions=(ConnectionError,))
        def fetch_data():
            return api.get_data()
    """
    settings = get_settings()
    attempts = max_attempts or settings.max_retries

    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    )
