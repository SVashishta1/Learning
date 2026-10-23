"""Three small tools that stop one sick service from making the whole app sick.

  retry_call()    try again after a short, growing, random wait (backoff + jitter)
  CircuitBreaker  after several failures in a row, stop calling for a while ("open"), then test carefully
  (timeouts live in main.py, on the HTTP client)

No web framework in here, so it is easy to test: see test_resilience.py.
"""
import random
import threading
import time


class CircuitOpenError(Exception):
    """Raised instead of calling a service whose circuit breaker is open."""


def backoff_delay(attempt: int, base: float, cap: float) -> float:
    """How long to wait before retry number `attempt` (1, 2, 3...).

    Exponential backoff: base, 2*base, 4*base ... but never more than `cap`.
    Full jitter: pick a random time between 0 and that number, so many clients
    that failed at the same moment do NOT all retry at the same moment.
    """
    ceiling = min(cap, base * (2 ** (attempt - 1)))
    return random.uniform(0, ceiling)


def retry_call(func, *, attempts=3, base=0.2, cap=2.0, retry_on=(Exception,), sleep=time.sleep, on_retry=None):
    """Call func(). If it raises one of `retry_on`, wait and try again, up to `attempts` times in total."""
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except retry_on as e:
            if attempt == attempts:
                raise  # out of tries: let the caller see the last error
            delay = backoff_delay(attempt, base, cap)
            if on_retry:
                on_retry(attempt, delay, e)
            sleep(delay)


class CircuitBreaker:
    """Like the fuse box in a house.

    closed    = normal. Calls go through. Count failures in a row.
    open      = too many failures. Fail FAST without calling, for `reset_after` seconds.
    half_open = the wait is over. Let ONE trial call through:
                success -> closed again, failure -> open again.
    """

    def __init__(self, name: str, failure_threshold: int = 3, reset_after: float = 15.0,
                 failure_on=(Exception,), clock=time.monotonic):
        self.name = name
        self.failure_on = failure_on  # which errors count as "the service is sick"
        self.failure_threshold = failure_threshold
        self.reset_after = reset_after
        self.clock = clock  # a function that returns "now"; tests pass a fake clock
        self.state = "closed"
        self.failures = 0
        self.opened_at = 0.0
        self._lock = threading.Lock()  # FastAPI runs requests in several threads at once

    def call(self, func):
        with self._lock:
            if self.state == "open":
                if self.clock() - self.opened_at >= self.reset_after:
                    self.state = "half_open"  # time to test the water: THIS call is the trial
                else:
                    raise CircuitOpenError(f"{self.name} circuit is open, not calling it")
            elif self.state == "half_open":
                # Another request is already doing the trial call. Don't pile on.
                raise CircuitOpenError(f"{self.name} circuit is half-open, trial call in progress")
        try:
            result = func()
        except self.failure_on:
            self._record_failure()
            raise
        except Exception:
            self._record_success()  # the service answered; the problem was our request, not its health
            raise
        self._record_success()
        return result

    def _record_failure(self):
        with self._lock:
            self.failures += 1
            if self.state == "half_open" or self.failures >= self.failure_threshold:
                self.state = "open"
                self.opened_at = self.clock()

    def _record_success(self):
        with self._lock:
            self.state = "closed"
            self.failures = 0

    def status(self) -> dict:
        return {"state": self.state, "failures_in_a_row": self.failures}
