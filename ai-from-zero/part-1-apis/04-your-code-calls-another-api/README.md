# 04 · Your code calls another API

**What it does:** asks a free weather service for live weather and a 3-day forecast for any city.

## Run it
```bash
cd part-1-apis/04-your-code-calls-another-api
python weather.py Tokyo
python weather.py "New York"
```

## The idea in one sentence
So far *you* built APIs; now your code *uses* one: `httpx.get(address, params=...)` sends the request and `.json()` turns the answer into Python data.

Talking to an AI like Claude in Part 4 works exactly the same way: send a request, get JSON back.

## Try this
1. Open this in your browser to see the raw JSON your code receives: https://api.open-meteo.com/v1/forecast?latitude=48.85&longitude=2.35&current=temperature_2m
2. Change `forecast_days` to 7.
3. Make it loop over a list of 3 cities and print which one is warmest.
