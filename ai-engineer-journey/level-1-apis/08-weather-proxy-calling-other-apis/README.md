# 1.8 · Weather proxy: calling other APIs like a pro

**What you build:** `/weather/Paris` → your API asks the free **Open-Meteo** API, adds a 10-minute **cache**, **retries** when the service hiccups, and returns clean errors.
**Like you're 10:** so far *you* were the restaurant. Now you're also a *customer* ordering from another restaurant. Good customers don't wait forever (timeout), ask again politely if the kitchen drops the plate (retry), and don't re-order the same dish every minute (cache).

**Why this matters:** in Level 7 you'll call LLM APIs. They are slow, sometimes overloaded (HTTP 429/529), and cost money per call. Every habit here applies directly.

## Run it
```bash
cd level-1-apis/08-weather-proxy-calling-other-apis
pip install -r requirements.txt
uvicorn main:app --reload
```
- http://127.0.0.1:8000/weather/Tokyo
- Call it again: `"cached": true`, and the answer comes back instantly.
- http://127.0.0.1:8000/stats shows how many real upstream calls were made.
- http://127.0.0.1:8000/weather/Atlantis returns a friendly 404.

Test (works offline, using a fake API): `pytest -v`

## Key ideas
| Habit | Code | Why |
|-------|------|-----|
| Timeout | `httpx.Client(timeout=5.0)` | a slow server shouldn't freeze you |
| Retry 5xx, not 4xx | `_get()` | 5xx = their problem (try again); 4xx = your problem (fix the request) |
| Exponential backoff | `0.2 * 2 ** attempt` | don't hammer a struggling server |
| Cache | `self.cache` | faster and cheaper, and kinder to the provider |
| Fake the network in tests | `httpx.MockTransport` | tests run offline, fast, and give the same result every time |

## Your turn
1. Add `/forecast/{city}?days=3` using Open-Meteo's `daily=temperature_2m_max` parameter.
2. Make the cache time configurable with an env var `CACHE_SECONDS`.
3. Make the API async (`httpx.AsyncClient`, `async def`) and fetch 5 cities at the same time with `asyncio.gather`.

## Watch
- HTTPX quickstart: https://www.python-httpx.org/quickstart/
- Caching explained: https://www.youtube.com/results?search_query=caching+explained+system+design+beginners
