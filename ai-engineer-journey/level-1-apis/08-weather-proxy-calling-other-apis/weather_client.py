"""A careful API *client*. Calling someone else's API is exactly what you'll do with LLM APIs later,
so learn the good habits now: timeouts, retries with backoff, caching, and clear errors."""
import time

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"   # free, no API key needed


class WeatherError(Exception):
    pass


class WeatherClient:
    def __init__(self, http: httpx.Client | None = None, cache_seconds: int = 600, retries: int = 3):
        # timeout=5: never let a slow server freeze your app forever
        self.http = http or httpx.Client(timeout=5.0)
        self.cache_seconds = cache_seconds
        self.retries = retries
        self.cache: dict[str, tuple[float, dict]] = {}
        self.calls_made = 0   # handy for seeing the cache work

    def _get(self, url: str, params: dict) -> dict:
        for attempt in range(1, self.retries + 1):
            try:
                self.calls_made += 1
                r = self.http.get(url, params=params)
                if r.status_code >= 500:            # server hiccup -> worth retrying
                    raise httpx.HTTPStatusError("server error", request=r.request, response=r)
                r.raise_for_status()                 # 4xx -> our mistake, don't retry
                return r.json()
            except (httpx.TransportError, httpx.HTTPStatusError) as e:
                is_client_error = isinstance(e, httpx.HTTPStatusError) and e.response.status_code < 500
                if is_client_error or attempt == self.retries:
                    raise WeatherError(f"Weather service failed: {e}") from e
                time.sleep(0.2 * 2 ** attempt)       # exponential backoff: 0.4s, 0.8s, ...
        raise WeatherError("unreachable")

    def current(self, city: str) -> dict:
        key = city.strip().lower()
        hit = self.cache.get(key)
        if hit and time.time() - hit[0] < self.cache_seconds:
            return {**hit[1], "cached": True}

        places = self._get(GEOCODE_URL, {"name": city, "count": 1}).get("results") or []
        if not places:
            raise WeatherError(f"City '{city}' not found")
        p = places[0]
        data = self._get(FORECAST_URL, {"latitude": p["latitude"], "longitude": p["longitude"],
                                        "current": "temperature_2m,wind_speed_10m"})
        result = {"city": p["name"], "country": p.get("country"),
                  "temperature_c": data["current"]["temperature_2m"],
                  "wind_kmh": data["current"]["wind_speed_10m"], "cached": False}
        self.cache[key] = (time.time(), result)
        return result
