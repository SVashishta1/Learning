# 1.8 · Weather proxy: calling other APIs (timeouts, retries, caching)

**What you'll build:** `/weather/Tokyo` → your API asks the free **Open-Meteo** API for the current weather, keeps answers in a 10-minute **cache**, **retries** when the service hiccups, never waits forever (**timeout**), and returns clean errors.
**Like you're 10:** so far *you* were the restaurant. Now you're also a *customer* ordering from another restaurant. Good customers don't wait forever (timeout), ask again politely if the kitchen drops the plate (retry), and don't re-order the same dish every minute (cache).
**Time:** ~1.5 h · **Builds on:** [1.7 · Dockerize & deploy](../07-dockerize-and-deploy-to-the-cloud) · **Needs:** internet access (Open-Meteo is free, no API key)

## Why this matters
In Level 7 you'll call LLM APIs like Claude's. They are slow (seconds per answer), sometimes overloaded (HTTP 429/529), and cost money per call. The habits in this project (timeouts, retries with backoff, caching, clear errors, and tests that fake the network) are exactly what keeps AI apps fast, cheap and reliable. Official SDKs do some of this for you, but you need to understand it to configure and debug it.

## What you'll learn
- **API client:** code that *calls* another API (here with `httpx`), instead of answering calls.
- **Timeout:** the maximum time to wait for an answer before giving up.
- **Retry with exponential backoff:** try again after server errors (5xx), waiting longer each time; never retry your own mistakes (4xx).
- **Cache:** remember recent answers so repeat questions are instant and free.
- **Mocking the network:** `httpx.MockTransport` fakes the other API, so tests run offline and give the same result every time.

## Before you start
```bash
cd level-1-apis/08-weather-proxy-calling-other-apis
pip install -r requirements.txt
```
- `fastapi`, `uvicorn[standard]`: web framework and server.
- `httpx`: the HTTP client that calls Open-Meteo (and fakes it in tests).
- `pytest`, `httpx2`: run the tests (`httpx2` is what newer FastAPI versions use for `TestClient`).

No API key needed: Open-Meteo is free for non-commercial use. The tests don't need internet at all.

## Run it
1. Start the server: `uvicorn main:app --reload`
2. Open:
   - http://127.0.0.1:8000/weather/Tokyo
   - the same URL again (look at `"cached"`)
   - http://127.0.0.1:8000/stats
   - http://127.0.0.1:8000/weather/Atlantis
3. Run the tests: `pytest -v`

### What you should see
Your numbers will be different (it's the real weather right now):
```
GET /weather/Tokyo      {"city":"Tokyo","country":"Japan","temperature_c":18.3,"wind_kmh":7.2,"cached":false}
GET /weather/Tokyo      {"city":"Tokyo","country":"Japan","temperature_c":18.3,"wind_kmh":7.2,"cached":true}
GET /stats              {"upstream_calls":2,"cached_cities":["tokyo"]}
GET /weather/Atlantis   {"detail":"City 'Atlantis' not found"}          (status 404)
```
The first Tokyo call needed **two** upstream calls (find the city's coordinates, then get the weather). The second answer came from the cache: instant, and `upstream_calls` stayed at 2.

`pytest -v` (no internet needed):
```
test_weather.py::test_weather_and_cache PASSED                           [ 16%]
test_weather.py::test_retries_then_succeeds PASSED                       [ 33%]
test_weather.py::test_unknown_city PASSED                                [ 50%]
test_weather.py::test_gives_up_after_all_retries PASSED                  [ 66%]
test_weather.py::test_4xx_is_not_retried PASSED                          [ 83%]
test_weather.py::test_api_status_codes PASSED                            [100%]

============================== 6 passed in 2.42s ===============================
```
The tests take about 2 seconds because the retry tests really wait (0.4 s, then 0.8 s) between attempts.

## How it works
```
GET /weather/Tokyo ──► main.py ──► WeatherClient.current("Tokyo")
                                     ├─ in cache and < 10 min old? ──► return it ("cached": true)
                                     ├─ _get(GEOCODE_URL)  ──► Open-Meteo: "Tokyo" → lat 35.69, lon 139.69
                                     ├─ _get(FORECAST_URL) ──► Open-Meteo: current temperature + wind
                                     └─ save in cache, return ("cached": false)
_get(): try ──► 5xx or network error? wait 0.4 s, 0.8 s ... and retry ──► still failing? WeatherError
            └─► 4xx? WeatherError at once (retrying won't fix our mistake)
```
**`weather_client.py`**
1. `WeatherError` means "the weather service failed"; `CityNotFound` is a more specific kind of it. `main.py` turns them into different status codes.
2. `WeatherClient.__init__` creates `httpx.Client(timeout=5.0)`, so no request can hang for more than 5 seconds. You can pass in your own `http` client: that's how the tests inject a fake one. `self.cache` maps a city name to `(time saved, result)`.
3. `_get(url, params)` loops `for attempt in range(1, self.retries + 1)`. A 5xx status is turned into an `httpx.HTTPStatusError`; `r.raise_for_status()` raises for 4xx. In the `except`, a 4xx (client error) or the last attempt gives up with a `WeatherError`. Otherwise it sleeps `0.2 * 2 ** attempt` seconds (0.4, 0.8, 1.6, ...): **exponential backoff**, so a struggling server gets more breathing room each time.
4. `current(city)` normalises the key (`"  Paris "` and `"paris"` share a cache entry), returns a fresh cache hit, otherwise geocodes the city (`CityNotFound` if there are no results), fetches the forecast, keeps only the fields we need, and saves it in the cache.

**`main.py`**
5. One `WeatherClient` is created when the app starts, so the cache is shared by all requests. `get_weather` maps `CityNotFound` → **404** and any other `WeatherError` → **502 Bad Gateway** ("the service behind me failed"). `/stats` shows `calls_made` and the cached city names.

**`test_weather.py`**
6. `fake_api(fail_times, fail_status)` builds an `httpx.Client` whose `MockTransport` handler answers like Open-Meteo would. It can fail a set number of times first. The tests check caching, retrying after 503s, giving up after all retries, *not* retrying a 400, and the API's 404/502 status codes (with `monkeypatch` swapping the fake client into `main.py`).

## If something goes wrong
- **Every city returns 502 `Weather service failed: ... ConnectError`** → your computer can't reach Open-Meteo (offline, firewall, or a company proxy). The tests still pass offline; try another network to see real weather.
- **`502 ... ReadTimeout`** → Open-Meteo took more than 5 seconds. Try again; that's the timeout doing its job instead of freezing your app.
- **A city you know returns 404** → the geocoder needs the city's name, not a country or a street. Try the English name, and for spaces use `%20` in the browser (`/weather/New%20York`) or just type the space.
- **The temperature never changes** → you're seeing the cache for 10 minutes (`"cached": true`). Restart the server or wait.
- **Tests fail with `ModuleNotFoundError: No module named 'weather_client'`** → run `pytest` from inside this folder.

## Try this
1. Make the cache time configurable with an environment variable `CACHE_SECONDS` (default 600).
   <details><summary>Solution</summary>

   In `main.py`:
   ```python
   import os
   weather = WeatherClient(cache_seconds=int(os.getenv("CACHE_SECONDS", "600")))
   ```
   Run `CACHE_SECONDS=5 uvicorn main:app --reload` (PowerShell: `$env:CACHE_SECONDS="5"` first) and watch `"cached"` flip back to `false` after 5 seconds.
   </details>
2. Add `/forecast/{city}?days=3` that returns the daily maximum temperatures, using Open-Meteo's `daily=temperature_2m_max` parameter.
   <details><summary>Solution</summary>

   Add a method to `WeatherClient` (no caching, to keep it short):
   ```python
   def forecast(self, city: str, days: int = 3) -> dict:
       places = self._get(GEOCODE_URL, {"name": city, "count": 1}).get("results") or []
       if not places:
           raise CityNotFound(f"City '{city}' not found")
       p = places[0]
       data = self._get(FORECAST_URL, {"latitude": p["latitude"], "longitude": p["longitude"],
                                       "daily": "temperature_2m_max", "forecast_days": days,
                                       "timezone": "auto"})
       return {"city": p["name"], "days": data["daily"]["time"], "max_c": data["daily"]["temperature_2m_max"]}
   ```
   And a route in `main.py` with the same `try/except` as `get_weather`, using `days: int = Query(3, ge=1, le=16)` (import `Query` from `fastapi`).
   </details>
3. Write a test proving the cache **expires**: with `cache_seconds=0`, two calls for Paris should make 4 upstream calls.
   <details><summary>Solution</summary>

   ```python
   def test_cache_expires():
       client = WeatherClient(http=fake_api(), cache_seconds=0)
       client.current("Paris")
       assert client.current("Paris")["cached"] is False
       assert client.calls_made == 4
   ```
   With 0 seconds, every entry is already too old, so each call geocodes and fetches again.
   </details>

## Check yourself
1. Why retry a 503 but not a 400?
2. What does exponential backoff do, and why is it kinder than retrying immediately?
3. What could go wrong if there were no timeout?
4. How can the tests check retries and errors without internet access?

<details><summary>Answers</summary>

1. 5xx errors are the server's problem and are often temporary (overloaded, restarting), so trying again can work. 4xx errors mean our request is wrong; sending the same wrong request again will fail the same way.
2. It waits longer after each failure (0.4 s, 0.8 s, 1.6 s...). A struggling server gets time to recover instead of being hammered by instant retries from every client.
3. If the other server hangs, your request would hang too, tying up your server until users give up. A timeout fails fast with a clear error.
4. `httpx.MockTransport` replaces the network with a Python function that returns whatever responses the test wants (success, 503s, empty results), and `WeatherClient` accepts that fake client through its `http` argument.
</details>

## Learn more (optional)
- HTTPX quickstart: https://www.python-httpx.org/quickstart/
- Open-Meteo API docs (all the weather variables you can ask for): https://open-meteo.com/en/docs
- Caching explained: https://www.youtube.com/results?search_query=caching+explained+system+design+beginners
- Exponential backoff and jitter: https://www.youtube.com/results?search_query=exponential+backoff+retry+explained

## Next
→ [2.1 · One neuron learns y = 2x](../../level-2-neural-nets-from-scratch/01-one-neuron-learns-y-equals-2x)
