"""Tests for resilience.py. Run from the lesson folder:  pytest -q gateway"""
import pytest

from resilience import CircuitBreaker, CircuitOpenError, backoff_delay, retry_call


class FakeClock:
    """A clock we can move forward by hand, so tests don't really wait."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def flaky(fail_times):
    """A function that raises ConnectionError `fail_times` times, then returns 'ok'."""
    calls = {"n": 0}

    def func():
        calls["n"] += 1
        if calls["n"] <= fail_times:
            raise ConnectionError("boom")
        return "ok"

    return func, calls


def test_backoff_grows_but_stays_under_the_cap():
    for _ in range(200):
        assert 0 <= backoff_delay(1, base=0.2, cap=2.0) <= 0.2
        assert 0 <= backoff_delay(3, base=0.2, cap=2.0) <= 0.8
        assert 0 <= backoff_delay(10, base=0.2, cap=2.0) <= 2.0  # 0.2 * 512 would be 102 s


def test_retry_succeeds_after_two_failures():
    func, calls = flaky(fail_times=2)
    waits = []
    assert retry_call(func, attempts=3, sleep=waits.append) == "ok"
    assert calls["n"] == 3
    assert len(waits) == 2  # waited before try 2 and before try 3


def test_retry_gives_up_and_raises_the_last_error():
    func, calls = flaky(fail_times=10)
    with pytest.raises(ConnectionError):
        retry_call(func, attempts=3, sleep=lambda s: None)
    assert calls["n"] == 3


def test_retry_does_not_retry_other_errors():
    calls = {"n": 0}

    def bad_input():
        calls["n"] += 1
        raise ValueError("your question is empty")  # retrying won't fix this

    with pytest.raises(ValueError):
        retry_call(bad_input, attempts=3, retry_on=(ConnectionError,), sleep=lambda s: None)
    assert calls["n"] == 1


def test_breaker_opens_after_threshold_and_fails_fast():
    clock = FakeClock()
    breaker = CircuitBreaker("llm", failure_threshold=3, reset_after=15, clock=clock)
    func, calls = flaky(fail_times=100)
    for _ in range(3):
        with pytest.raises(ConnectionError):
            breaker.call(func)
    assert breaker.state == "open"
    with pytest.raises(CircuitOpenError):
        breaker.call(func)
    assert calls["n"] == 3  # the 4th call never reached the service


def test_breaker_half_open_success_closes_it():
    clock = FakeClock()
    breaker = CircuitBreaker("llm", failure_threshold=1, reset_after=15, clock=clock)
    with pytest.raises(ConnectionError):
        breaker.call(flaky(fail_times=1)[0])
    assert breaker.state == "open"
    clock.now = 16  # 16 "seconds" later
    assert breaker.call(lambda: "ok") == "ok"
    assert breaker.state == "closed" and breaker.failures == 0


def test_breaker_half_open_failure_opens_it_again():
    clock = FakeClock()
    breaker = CircuitBreaker("llm", failure_threshold=1, reset_after=15, clock=clock)
    func, _ = flaky(fail_times=100)
    with pytest.raises(ConnectionError):
        breaker.call(func)
    clock.now = 16
    with pytest.raises(ConnectionError):
        breaker.call(func)  # the trial call fails...
    assert breaker.state == "open"  # ...so the breaker opens again
    with pytest.raises(CircuitOpenError):
        breaker.call(func)


def test_success_resets_the_failure_count():
    breaker = CircuitBreaker("rag", failure_threshold=3)
    with pytest.raises(ConnectionError):
        breaker.call(flaky(fail_times=1)[0])
    breaker.call(lambda: "ok")
    assert breaker.failures == 0 and breaker.state == "closed"


def test_breaker_ignores_errors_that_are_not_failures():
    breaker = CircuitBreaker("llm", failure_threshold=1, failure_on=(ConnectionError,))

    def bad_request():
        raise ValueError("our mistake, not the service's")

    with pytest.raises(ValueError):
        breaker.call(bad_request)
    assert breaker.state == "closed"
