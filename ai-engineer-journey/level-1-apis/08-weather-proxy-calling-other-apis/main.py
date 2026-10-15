"""Project 1.8: our API calls ANOTHER API (Open-Meteo) and adds caching + friendly errors."""
from fastapi import FastAPI, HTTPException

from weather_client import CityNotFound, WeatherClient, WeatherError

app = FastAPI(title="Weather proxy")
weather = WeatherClient()


@app.get("/weather/{city}")
def get_weather(city: str):
    try:
        return weather.current(city)
    except CityNotFound as e:
        raise HTTPException(404, str(e))     # 404 = no such city
    except WeatherError as e:
        raise HTTPException(502, str(e))     # 502 = "the service behind me failed"


@app.get("/stats")
def stats():
    return {"upstream_calls": weather.calls_made, "cached_cities": list(weather.cache)}
