"""
Retry utility with exponential backoff.

Usage:
    result = await retry(
        my_async_func,
        arg1, arg2,
        max_retries=3,
        base_delay=1.0,
    )

Or as a decorator:
    @with_retry(max_retries=3, base_delay=0.5)
    async def my_func():
        ...
"""

from __future__ import annotations

import asyncio
import functools
import logging
import random
from typing import Any, Awaitable, Callable, Type

logger = logging.getLogger(__name__)


async def retry(
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """
    Call `func(*args, **kwargs)` with exponential backoff on failure.

    Args:
        func:                  Async callable to retry.
        max_retries:           Maximum number of retry attempts (0 = no retries).
        base_delay:            Initial delay in seconds between retries.
        max_delay:             Cap on the delay between retries.
        jitter:                Add ±25% random jitter to each delay.
        retryable_exceptions:  Only retry on these exception types.
        *args, **kwargs:       Forwarded to func.

    Returns:
        The return value of func on success.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt == max_retries:
                break

            delay = min(base_delay * (2 ** attempt), max_delay)
            if jitter:
                delay *= 0.75 + random.random() * 0.5  # ±25%

            logger.warning(
                "Retry %d/%d for %s after %.2fs: %s",
                attempt + 1,
                max_retries,
                getattr(func, "__name__", str(func)),
                delay,
                exc,
            )
            await asyncio.sleep(delay)

    raise last_exc  # type: ignore[misc]


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator that wraps an async function with retry logic.

    Example:
        @with_retry(max_retries=3, base_delay=0.5)
        async def call_external_api():
            ...
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                jitter=jitter,
                retryable_exceptions=retryable_exceptions,
                **kwargs,
            )
        return wrapper
    return decorator
