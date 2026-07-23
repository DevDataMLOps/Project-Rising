from __future__ import annotations

import threading
from collections import Counter
from time import perf_counter


class Metrics:
    """Small dependency-free Prometheus metrics registry for pilot operation."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: Counter[tuple[str, str, int]] = Counter()
        self._duration_seconds: Counter[tuple[str, str]] = Counter()
        self._started = perf_counter()

    def observe(self, method: str, path: str, status_code: int, duration: float) -> None:
        normalized_path = path if not path.startswith("/api/v1/countries/") else "/api/v1/countries/{country}/risk"
        with self._lock:
            self._requests[(method, normalized_path, status_code)] += 1
            self._duration_seconds[(method, normalized_path)] += duration

    def render(self) -> str:
        lines = [
            "# HELP rising_uptime_seconds Process uptime in seconds.",
            "# TYPE rising_uptime_seconds gauge",
            f"rising_uptime_seconds {perf_counter() - self._started:.6f}",
            "# HELP rising_http_requests_total HTTP requests by method, path, and status.",
            "# TYPE rising_http_requests_total counter",
        ]
        with self._lock:
            for (method, path, status), count in sorted(self._requests.items()):
                lines.append(
                    f'rising_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
                )
            lines.extend(
                [
                    "# HELP rising_http_request_duration_seconds_total Cumulative request duration.",
                    "# TYPE rising_http_request_duration_seconds_total counter",
                ]
            )
            for (method, path), duration in sorted(self._duration_seconds.items()):
                lines.append(
                    f'rising_http_request_duration_seconds_total{{method="{method}",path="{path}"}} {duration:.6f}'
                )
        return "\n".join(lines) + "\n"


metrics = Metrics()
