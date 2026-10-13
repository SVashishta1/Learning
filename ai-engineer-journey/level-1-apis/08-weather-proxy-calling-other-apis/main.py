"""Project 1.8: our API calls ANOTHER API (Open-Meteo) and adds caching + friendly errors."""
from fastapi import FastAPI, HTTPException

from weather_client import WeatherClient, WeatherError

app = FastAPI(title="Weather proxy")
weather = WeatherClient()


@app.get("/weather/{city}")
def get_weather(city: str):
    try:
        return weather.current(city)
    except WeatherError as e:
        status = 404 if "not found" in str(e) else 502   # 502 = "the service behind me failed"
        raise HTTPException(status, str(e))


@app.get("/stats")
def stats():
    return {"upstream_calls": weather.calls_made, "cached_cities": list(weather.cache)}
