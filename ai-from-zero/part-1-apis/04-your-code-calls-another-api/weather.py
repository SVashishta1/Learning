# Your code is now the CUSTOMER: it calls someone else's API (Open-Meteo, free, no key needed).
# This is exactly how you'll talk to AI models later: send a request, get JSON back.
# Usage: python weather.py Tokyo
import sys

import httpx

city = sys.argv[1] if len(sys.argv) > 1 else "London"


def get_json(url, params):
    """Send a GET request to url and turn the JSON answer into Python data (dicts and lists)."""
    try:
        response = httpx.get(url, params=params, timeout=10)    # wait at most 10 seconds for an answer
        response.raise_for_status()                              # stop if the server answered with an error (e.g. 500)
    except httpx.HTTPError as error:                             # no internet, timeout, server error...
        sys.exit(f"Couldn't get an answer from {url}\nReason: {error}\nCheck your internet connection and try again.")
    return response.json()


# Step 1: ask the "geocoding" API where the city is (latitude/longitude)
place = get_json("https://geocoding-api.open-meteo.com/v1/search", {"name": city, "count": 1})
if not place.get("results"):
    sys.exit(f"Couldn't find a city called {city}")
spot = place["results"][0]

# Step 2: ask the weather API for that location
weather = get_json("https://api.open-meteo.com/v1/forecast", {
    "latitude": spot["latitude"], "longitude": spot["longitude"],
    "current": "temperature_2m,wind_speed_10m",
    "daily": "temperature_2m_max,temperature_2m_min", "forecast_days": 3,
})

print(f"📍 {spot['name']}, {spot.get('country', '')}")
print(f"🌡️  Now: {weather['current']['temperature_2m']}°C, wind {weather['current']['wind_speed_10m']} km/h")
for day, hi, lo in zip(weather["daily"]["time"], weather["daily"]["temperature_2m_max"], weather["daily"]["temperature_2m_min"]):
    print(f"   {day}: {lo}°C to {hi}°C")
