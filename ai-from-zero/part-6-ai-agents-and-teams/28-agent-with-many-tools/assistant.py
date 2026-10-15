# An agent with 4 tools + Claude's built-in web search. It picks the right tools for each question.
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from agent import run_agent, tool


def calculate(expression):
    if not set(expression) <= set("0123456789+-*/(). "):
        return "Error: only numbers and + - * / ( ) are allowed"
    result = eval(expression)                           # eval() runs the text as Python maths: "2*3" -> 6
    return str(round(result, 10))                       # hide tiny computer rounding errors like 12.499999999999998


def get_weather(city):
    # Open-Meteo is a free weather service (no key needed). Step 1: find the city's position on the map.
    found = httpx.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=10).json()
    if not found.get("results"):
        return f"I couldn't find a city called {city}"
    place = found["results"][0]
    # Step 2: ask for the current temperature at that position.
    now = httpx.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
        "latitude": place["latitude"], "longitude": place["longitude"], "current": "temperature_2m"}).json()["current"]
    return f"{place['name']}: {now['temperature_2m']}°C"


def get_time(timezone):
    return datetime.now(ZoneInfo(timezone)).strftime("%A %H:%M")


def save_note(text):
    with open("notes.txt", "a", encoding="utf-8") as f:       # "a" = add to the end, don't overwrite
        f.write(f"- {text}\n")
    return "Saved to notes.txt"


tools = [
    tool(calculate, "Exact arithmetic. Use for any maths.", {"expression": ("string", "e.g. 12 * (3 + 4)")}),
    tool(get_weather, "Current temperature in a city.", {"city": ("string", "City name")}),
    tool(get_time, "Current local time in a timezone.", {"timezone": ("string", "e.g. Asia/Tokyo, Europe/Paris, America/New_York")}),
    tool(save_note, "Save a short note for the user to read later.", {"text": ("string", "The note")}),
]

question = " ".join(sys.argv[1:]) or ("Is it warmer in Rome or Oslo right now, and by how many degrees? "
                                      "Also find one interesting AI news story from this week and save it as a note.")
print(run_agent(question, tools, web_search=True, system="You are a helpful assistant. Use tools instead of guessing."))
