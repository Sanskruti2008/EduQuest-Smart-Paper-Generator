import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from services.generation_executor import (
    GenerationBusyError,
    GenerationExecutor,
    GenerationLimits,
    GenerationTimeoutError,
)


def test_generation_executor_returns_result():
    executor = GenerationExecutor(
        GenerationLimits(queue_timeout_seconds=0.1, execution_timeout_seconds=1)
    )

    assert executor.submit(lambda: "complete") == "complete"


def test_generation_executor_rejects_when_queue_is_full():
    executor = GenerationExecutor(
        GenerationLimits(queue_timeout_seconds=0.01, execution_timeout_seconds=1)
    )
    blocker = ThreadPoolExecutor(max_workers=1)
    running = blocker.submit(executor.submit, lambda: time.sleep(0.2))

    try:
        with pytest.raises(GenerationBusyError):
            executor.submit(lambda: "not-started")
    finally:
        running.result(timeout=1)
        blocker.shutdown(wait=True)


def test_generation_executor_times_out():
    executor = GenerationExecutor(
        GenerationLimits(queue_timeout_seconds=0.1, execution_timeout_seconds=0.01)
    )

    with pytest.raises(GenerationTimeoutError):
        executor.submit(lambda: time.sleep(0.05))
