"""We test WITHOUT the internet by faking the other API with httpx.MockTransport."""
import httpx
import pytest
from fastapi.testclient import TestClient

import main
from weather_client import CityNotFound, WeatherClient, WeatherError


def fake_api(fail_times=0, fail_status=503):
    """A pretend Open-Meteo. It fails `fail_times` times with `fail_status`, then answers normally."""
    state = {"fails": fail_times}

    def handler(request: httpx.Request):
        if state["fails"] > 0:
            state["fails"] -= 1
            return httpx.Response(fail_status)
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
    with pytest.raises(CityNotFound, match="not found"):
        WeatherClient(http=fake_api()).current("Atlantis")


def test_gives_up_after_all_retries():
    client = WeatherClient(http=fake_api(fail_times=10), retries=2)
    with pytest.raises(WeatherError, match="503"):
        client.current("Paris")
    assert client.calls_made == 2          # tried exactly `retries` times


def test_4xx_is_not_retried():
    client = WeatherClient(http=fake_api(fail_times=1, fail_status=400), retries=3)
    with pytest.raises(WeatherError, match="400"):
        client.current("Paris")
    assert client.calls_made == 1          # our mistake: retrying would not help


def test_api_status_codes(monkeypatch):
    # Swap the real client inside main.py for one that talks to the fake API
    monkeypatch.setattr(main, "weather", WeatherClient(http=fake_api()))
    api = TestClient(main.app)
    assert api.get("/weather/Paris").json()["temperature_c"] == 21.5
    assert api.get("/weather/Atlantis").status_code == 404
    assert api.get("/stats").json()["cached_cities"] == ["paris"]

    monkeypatch.setattr(main, "weather", WeatherClient(http=fake_api(fail_times=10), retries=1))
    assert api.get("/weather/Paris").status_code == 502
