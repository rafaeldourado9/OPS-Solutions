"""
Circuit breaker for external service calls.

States:
  CLOSED    → Normal operation. Failures are counted.
  OPEN      → Service assumed down. Calls rejected immediately.
  HALF_OPEN → Recovery probe. One call allowed; success → CLOSED, failure → OPEN.

Usage:
    breaker = CircuitBreaker(name="gemini", failure_threshold=3, recovery_timeout=60)

    try:
        result = await breaker.call(my_async_func, arg1, arg2)
    except CircuitOpenError:
        # Use fallback
    except Exception:
        # Original error from my_async_func
"""

from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a call is attempted while the circuit is open."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Circuit '{name}' is OPEN — calls rejected until recovery timeout")
        self.name = name


class CircuitBreaker:
    """
    Async circuit breaker.

    Args:
        name:             Human-readable name for logging.
        failure_threshold: Number of consecutive failures before opening.
        recovery_timeout: Seconds to wait before probing recovery (HALF_OPEN).
    """

    def __init__(
        self,
        name: str = "circuit",
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ) -> None:
        self._name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: float = 0.0
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    async def call(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute `func(*args, **kwargs)` through the circuit breaker.

        Raises CircuitOpenError if the circuit is open and not yet recovered.
        Propagates the original exception on failure (after updating state).
        """
        await self._check_state()

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    async def _check_state(self) -> None:
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return
            if self._state == CircuitState.HALF_OPEN:
                # One probe is allowed; proceed
                return
            # OPEN — check if recovery timeout has elapsed
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info(
                    "Circuit '%s' → HALF_OPEN after %.0fs (probe allowed)",
                    self._name,
                    elapsed,
                )
            else:
                remaining = self._recovery_timeout - elapsed
                logger.debug(
                    "Circuit '%s' is OPEN — %.0fs until recovery probe",
                    self._name,
                    remaining,
                )
                raise CircuitOpenError(self._name)

    async def _on_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info("Circuit '%s' → CLOSED (probe succeeded)", self._name)
            self._state = CircuitState.CLOSED
            self._failure_count = 0

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self._failure_threshold:
                if self._state != CircuitState.OPEN:
                    logger.warning(
                        "Circuit '%s' → OPEN after %d consecutive failures",
                        self._name,
                        self._failure_count,
                    )
                self._state = CircuitState.OPEN
            else:
                logger.debug(
                    "Circuit '%s' failure %d/%d",
                    self._name,
                    self._failure_count,
                    self._failure_threshold,
                )

    def reset(self) -> None:
        """Manually reset the circuit to CLOSED state (useful in tests)."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
