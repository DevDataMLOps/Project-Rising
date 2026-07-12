from __future__ import annotations


DEFAULT_RETRY_DELAYS_SECONDS = [
    5,
    15,
    45,
    120,
    300,
]


def calculate_retry_delay(
    retry_count: int,
    retry_delays: list[int] | None = None,
) -> int:
    """
    Return the retry delay for the next attempt.
    """
    if retry_count < 0:
        raise ValueError("retry_count cannot be negative.")

    schedule = retry_delays or DEFAULT_RETRY_DELAYS_SECONDS
    index = min(retry_count, len(schedule) - 1)

    return schedule[index]


def should_retry(
    retry_count: int,
    max_retries: int = 5,
) -> bool:
    """
    Decide whether a failed event should be retried.
    """
    if retry_count < 0:
        raise ValueError("retry_count cannot be negative.")

    return retry_count < max_retries


def increment_retry_count(
    event: dict,
) -> dict:
    """
    Return a copy of an event with retry_count increased by one.
    """
    updated_event = event.copy()
    updated_event["retry_count"] = int(
        updated_event.get("retry_count", 0)
    ) + 1

    return updated_event
