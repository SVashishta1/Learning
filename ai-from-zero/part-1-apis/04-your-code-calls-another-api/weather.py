# Your code is now the CUSTOMER: it calls someone else's API (Open-Meteo, free, no key needed).
# This is exactly how you'll talk to AI models later: send a request, get JSON back.
import sys

import httpx

city = sys.argv[1] if len(sys.argv) > 1 else "London"

# Step 1: ask the "geocoding" API where the city is (latitude/longitude)
place = httpx.get("https://geocoding-api.open-meteo.com/v1/search",
                  params={"name": city, "count": 1}, timeout=10).json()
if not place.get("results"):
    sys.exit(f"Couldn't find a city called {city}")
spot = place["results"][0]

# Step 2: ask the weather API for that location
weather = httpx.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
    "latitude": spot["latitude"], "longitude": spot["longitude"],
    "current": "temperature_2m,wind_speed_10m",
    "daily": "temperature_2m_max,temperature_2m_min", "forecast_days": 3,
}).json()

print(f"📍 {spot['name']}, {spot.get('country', '')}")
print(f"🌡️  Now: {weather['current']['temperature_2m']}°C, wind {weather['current']['wind_speed_10m']} km/h")
for day, hi, lo in zip(weather["daily"]["time"], weather["daily"]["temperature_2m_max"], weather["daily"]["temperature_2m_min"]):
    print(f"   {day}: {lo}°C to {hi}°C")
