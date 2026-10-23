"""load.py: send many questions to the Ask API so the dashboards have something to show.

Run:  python load.py            (200 requests, 4 at a time)
      python load.py 1000 8     (1000 requests, 8 at a time)
Uses only Python's standard library.
"""

import json
import random
import sys
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

URL = "http://localhost:8000/ask"
QUESTIONS = [
    "How long does shipping take?",
    "Can I get a refund?",
    "What does the warranty cover on parts?",
    "When is support open?",
    "Do you sell bikes on the moon?",
]


def send_one(_: int) -> str:
    body = json.dumps({"question": random.choice(QUESTIONS)}).encode()
    request = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return str(response.status)
    except urllib.error.HTTPError as error:  # the server answered with an error code (e.g. 502)
        return str(error.code)
    except (urllib.error.URLError, ConnectionError, TimeoutError):  # nobody answered (properly)
        return "no connection"


def main() -> None:
    total = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    parallel = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    print(f"Sending {total} requests, {parallel} at a time, to {URL} ...")
    with ThreadPoolExecutor(max_workers=parallel) as pool:  # several "users" at once
        results = Counter(pool.map(send_one, range(total)))
    for status, count in sorted(results.items()):
        print(f"  status {status}: {count}")


if __name__ == "__main__":
    main()
