"""We test WITHOUT the internet by faking the other API with httpx.MockTransport."""
import httpx
import pytest

from weather_client import WeatherClient, WeatherError


def fake_api(fail_times=0):
    state = {"fails": fail_times}

    def handler(request: httpx.Request):
        if state["fails"] > 0:
            state["fails"] -= 1
            return httpx.Response(503)
        if "geocoding" in request.url.host:
            if request.url.params["name"] == "Atlantis":
                return httpx.Response(200, json={})
            return httpx.Response(200, json={"results": [{"name": "Paris", "country": "France", "latitude": 48.8, "longitude": 2.3}]})
        return httpx.Response(200, json={"current": {"temperature_2m": 21.5, "wind_speed_10m": 9.0}})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_weather_and_cache():
    client = WeatherClient(http=fake_api())
    first = client.current("Paris")
    assert first["temperature_c"] == 21.5 and first["cached"] is False
    assert client.current("paris")["cached"] is True
    assert client.calls_made == 2          # second call came from the cache


def test_retries_then_succeeds():
    client = WeatherClient(http=fake_api(fail_times=2), retries=3)
    assert client.current("Paris")["city"] == "Paris"


def test_unknown_city():
    with pytest.raises(WeatherError, match="not found"):
        WeatherClient(http=fake_api()).current("Atlantis")
