import pytest

from streaming.retry_handler import (
    calculate_retry_delay,
    increment_retry_count,
    should_retry,
)


def test_calculate_retry_delay_uses_backoff_schedule():
    assert calculate_retry_delay(0) == 5
    assert calculate_retry_delay(1) == 15
    assert calculate_retry_delay(2) == 45
    assert calculate_retry_delay(3) == 120
    assert calculate_retry_delay(4) == 300
    assert calculate_retry_delay(10) == 300


def test_should_retry_stops_at_max_retries():
    assert should_retry(retry_count=0, max_retries=5) is True
    assert should_retry(retry_count=4, max_retries=5) is True
    assert should_retry(retry_count=5, max_retries=5) is False


def test_increment_retry_count_returns_updated_copy():
    event = {"event_id": "event-1", "retry_count": 2}

    updated_event = increment_retry_count(event)

    assert updated_event["retry_count"] == 3
    assert event["retry_count"] == 2


def test_negative_retry_count_is_rejected():
    with pytest.raises(ValueError):
        calculate_retry_delay(-1)

    with pytest.raises(ValueError):
        should_retry(-1)
