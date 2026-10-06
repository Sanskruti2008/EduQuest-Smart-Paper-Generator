"""Bounded execution for resource-intensive paper generation."""

import os
import threading
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from typing import Any, Callable


def _positive_float(name: str, default: float) -> float:
    value = os.getenv(name, str(default))
    try:
        parsed = float(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


@dataclass(frozen=True)
class GenerationLimits:
    queue_timeout_seconds: float
    execution_timeout_seconds: float

    @classmethod
    def from_environment(cls) -> "GenerationLimits":
        return cls(
            queue_timeout_seconds=_positive_float(
                "PAPER_GENERATION_QUEUE_TIMEOUT_SECONDS", 10.0
            ),
            execution_timeout_seconds=_positive_float(
                "PAPER_GENERATION_TIMEOUT_SECONDS", 180.0
            ),
        )


class GenerationBusyError(RuntimeError):
    """Raised when the generation worker cannot accept another request."""


class GenerationTimeoutError(TimeoutError):
    """Raised when generation exceeds its configured execution limit."""


class GenerationExecutor:
    """Run one expensive generation at a time and bound waiting callers.

    A timed-out future is deliberately allowed to finish in the worker. The
    slot is released from its completion callback, preventing a timed-out
    request from starting an overlapping model-heavy generation.
    """

    def __init__(self, limits: GenerationLimits | None = None) -> None:
        self.limits = limits or GenerationLimits.from_environment()
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="eduquest-paper-generation",
        )
        self._slot = threading.BoundedSemaphore(1)

    def submit(self, operation: Callable[[], Any]) -> Any:
        acquired = self._slot.acquire(
            timeout=self.limits.queue_timeout_seconds
        )
        if not acquired:
            raise GenerationBusyError(
                "Paper generation is busy. Please retry shortly."
            )

        try:
            future: Future[Any] = self._executor.submit(operation)
        except Exception:
            self._slot.release()
            raise
        future.add_done_callback(lambda _: self._slot.release())
        try:
            return future.result(
                timeout=self.limits.execution_timeout_seconds
            )
        except TimeoutError as error:
            raise GenerationTimeoutError(
                "Paper generation exceeded the configured timeout."
            ) from error


generation_executor = GenerationExecutor()
