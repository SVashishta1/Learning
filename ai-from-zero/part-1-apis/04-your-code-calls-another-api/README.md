# 04 · Your code calls another API

**What you'll build:** a small program that asks a free weather service for the live weather and a 3-day forecast for any city you name.
**Time:** ~30 min · **Builds on:** [03 · An API that saves to a database](../03-api-that-saves-to-a-database) · **Needs:** an internet connection (no API key: Open-Meteo is free)

Like you're 10: so far you built the restaurant. Now you're the customer, ordering from someone else's restaurant.

## Why this matters
So far *you* built APIs. Most real programs also *use* other people's APIs: for payments, maps, weather, and above all AI. Talking to Claude in Part 4 works exactly like this lesson: your code sends a request with some inputs, and gets JSON back. Once you can call one API, you can call almost any of them.

## What you'll learn
- **API client**: code that sends requests to someone else's API. `httpx` is the client library used here.
- **Query parameters from code**: `params={"name": "Tokyo"}` builds the `?name=Tokyo` part of the address for you.
- **Parsing JSON**: `.json()` turns the API's text answer into Python dictionaries and lists you can pick values out of.
- **Chaining APIs**: using the answer from one API (where is Tokyo?) as the input to the next (what's the weather there?).
- **Handling failures**: the internet is unreliable, so good code checks for errors and timeouts.

## Before you start
- Venv on, and this part's install line done (skip if done already):
  ```bash
  pip install fastapi "uvicorn[standard]" httpx
  ```
  This lesson only uses `httpx`: it sends web requests from Python.
- No API key needed. You do need internet access.

## Run it
1. From the course folder (`ai-from-zero`):
   ```bash
   cd part-1-apis/04-your-code-calls-another-api
   python weather.py Tokyo
   ```
2. Try a city with a space in its name. The quotes keep the two words together as one input:
   ```bash
   python weather.py "New York"
   ```
3. Run it with no city (it uses London), and with a made-up one:
   ```bash
   python weather.py
   python weather.py Xyzzyqqq
   ```

### What you should see
The numbers are live, so yours will differ:
```
📍 Tokyo, Japan
🌡️  Now: 18.4°C, wind 7.9 km/h
   2026-10-15: 15.2°C to 21.3°C
   2026-10-16: 16.1°C to 22.0°C
   2026-10-17: 14.7°C to 19.8°C
```
For the made-up city:
```
Couldn't find a city called Xyzzyqqq
```
Check the first line: the API found the right country. The next lines are today's temperature and wind, then the lowest and highest temperature for 3 days. If your internet is off, you get a friendly message starting `Couldn't get an answer from https://geocoding-api.open-meteo.com/v1/search` instead of a crash.

## How it works
```
weather.py ──"where is Tokyo?"──▶ geocoding API ──▶ {"results": [{"latitude": 35.69, "longitude": 139.69, ...}]}
weather.py ──"weather at 35.69, 139.69?"──▶ forecast API ──▶ {"current": {...}, "daily": {...}}
weather.py ──▶ prints a short report
```
1. `city = sys.argv[1] if len(sys.argv) > 1 else "London"`: `sys.argv` is the list of words you typed after `python`. `sys.argv[0]` is `weather.py`, `sys.argv[1]` is the city. If you typed no city, it uses `"London"`.
2. `get_json(url, params)` is a small helper used for both API calls:
   - `httpx.get(url, params=params, timeout=10)` sends a GET request, exactly like your browser visiting an address. `timeout=10` means "give up after 10 seconds instead of waiting forever".
   - `response.raise_for_status()` turns an error answer from the server (like code 500) into a Python error.
   - `except httpx.HTTPError` catches any network problem (no internet, timeout, server error) and exits with a clear message instead of a long traceback.
   - `response.json()` turns the JSON text into Python data.
3. **Step 1** calls the geocoding API (`geocoding-api.open-meteo.com/v1/search`) with `{"name": city, "count": 1}` ("find this name, give me the best match"). If `"results"` is missing, no city matched, so `sys.exit(...)` prints a message and stops. Otherwise `spot` is the first match, a dictionary with `name`, `country`, `latitude` and `longitude`.
4. **Step 2** calls the forecast API (`api.open-meteo.com/v1/forecast`) with the latitude and longitude, plus which data you want: `current` temperature and wind, and `daily` max/min temperatures for `forecast_days: 3`. The API's documentation lists these names; you can't guess them.
5. The `print` lines dig into the answer with square brackets: `weather["current"]["temperature_2m"]` means "in the `current` part, take `temperature_2m`".
6. `zip(...)` walks through three lists side by side (dates, highs, lows), so each loop turn gets one day's date, high and low.

## If something goes wrong
- **`Couldn't get an answer from ... Reason: ...ConnectError...` or `...ConnectTimeout...`** → no internet, or a firewall/VPN is blocking it. Check you can open https://open-meteo.com in your browser, then run it again.
- **`Couldn't find a city called ...`** → check the spelling, or try the English name ("Munich", not "München" usually works best). For two-word cities, use quotes: `"New York"`.
- **`ModuleNotFoundError: No module named 'httpx'`** → switch your venv on and run the pip line.
- **`KeyError: 'temperature_2m'` after you changed the code** → you asked the API for something different from what you read. The names in `params` (like `"current": "temperature_2m,wind_speed_10m"`) must match the names you read in the `print` lines.
- **It finds the wrong place** (a smaller town with the same name) → `"count": 1` takes only the top match. To see the other matches, change it to `"count": 5` and add `print(place["results"])` after Step 1.

## Try this
1. Open this address in your browser to see the raw JSON your code receives: https://api.open-meteo.com/v1/forecast?latitude=48.85&longitude=2.35&current=temperature_2m . Find the temperature in it.
2. Get a 7-day forecast instead of 3 days.
3. Make a new file `warmest.py` in this folder that gets the current temperature for 3 cities and prints which one is warmest right now.

<details><summary>Hints and solutions</summary>

1. You'll see something like `{"latitude":48.86,"longitude":2.34,...,"current_units":{...,"temperature_2m":"°C"},"current":{"time":"...","interval":900,"temperature_2m":12.3}}`. The temperature is inside `"current"`. That's why the code says `weather["current"]["temperature_2m"]`.
2. In `weather.py`, change `"forecast_days": 3` to `"forecast_days": 7`. The loop prints however many days come back, so nothing else changes.
3. Put the two API calls in a function, then loop over the cities:
   ```python
   import sys

   import httpx


   def get_json(url, params):
       try:
           response = httpx.get(url, params=params, timeout=10)
           response.raise_for_status()
       except httpx.HTTPError as error:
           sys.exit(f"Couldn't get an answer from {url}\nReason: {error}")
       return response.json()


   def temperature_now(city):
       place = get_json("https://geocoding-api.open-meteo.com/v1/search", {"name": city, "count": 1})
       spot = place["results"][0]
       weather = get_json("https://api.open-meteo.com/v1/forecast", {
           "latitude": spot["latitude"], "longitude": spot["longitude"], "current": "temperature_2m"})
       return weather["current"]["temperature_2m"]


   cities = ["Tokyo", "London", "New York"]
   temperatures = {}
   for city in cities:
       temperatures[city] = temperature_now(city)
       print(f"{city}: {temperatures[city]}°C")

   warmest = max(temperatures, key=temperatures.get)     # the city with the biggest temperature
   print(f"Warmest right now: {warmest}")
   ```
   Run it with `python warmest.py`.
</details>

## Check yourself
1. Why does the program call two different APIs instead of one?
2. What does `.json()` do to the API's answer?
3. What would happen without `timeout=10` if the weather service never answered?
4. How is this lesson connected to talking to an AI like Claude later?

<details><summary>Answers</summary>

1. The weather API needs a latitude and longitude, not a city name. The geocoding API turns the name into those numbers first.
2. It turns the JSON text into Python data (dictionaries and lists), so you can pick values out with `["..."]`.
3. The program could hang, waiting for a very long time. The timeout makes it give up after 10 seconds and show an error.
4. It's the same pattern: send a request with inputs (your message), get JSON back (the AI's reply), and pick the parts you need out of it.
</details>

## Learn more (optional)
- Open-Meteo API documentation (all the weather values you can ask for): https://open-meteo.com/en/docs
- httpx quickstart: https://www.python-httpx.org/quickstart/
- Video: search YouTube for "Python requests API tutorial" (httpx works the same way as the `requests` library shown in most videos).

## Next
→ [05 · Put your API on the internet](../05-put-your-api-on-the-internet)
