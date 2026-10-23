# preflight.py: the pilot's checklist before take-off. Run it 30 minutes before every demo.
#
#   python preflight.py                         (checks http://127.0.0.1:8000)
#   python preflight.py --url http://10.0.0.5:8000
#
# It calls the running app exactly like the browser does, runs every sample, and tells you
# what will happen on stage: live answers, fallbacks, or slow replies.
import argparse
import sys

import httpx

SLOW_SECONDS = 10      # more than this feels painfully long in front of an audience


def check(base_url, client=None):
    """Return (problems, lines): problems is a list of things to fix, lines is the report to print."""
    client = client or httpx.Client(base_url=base_url, timeout=60)
    problems, lines = [], []
    try:
        health = client.get("/api/health").json()
    except httpx.HTTPError as error:
        return [f"App not reachable at {base_url}: {error}"], []
    lines.append(f"App is up: mode={health['demo_mode']} provider={health['provider']} model={health['model']}")
    if health["demo_mode"] != "live":
        problems.append("DEMO_MODE is not 'live': the audience will only see recorded answers")

    for sample in client.get("/api/samples").json():
        result = client.post("/api/draft", json={"email": sample["email"], "sample_id": sample["id"]}).json()
        lines.append(f"  {sample['id']:<10} mode={result['mode']:<11} {result['seconds']:>5} s  "
                     f"tracking={result['tracking']}")
        if sample["id"] not in health["recorded"]:
            problems.append(f"{sample['id']}: no recorded backup answer")
        if result["mode"] in ("fallback", "unavailable"):
            problems.append(f"{sample['id']}: live AI failed ({result['note']})")
        if result["seconds"] > SLOW_SECONDS:
            problems.append(f"{sample['id']}: slow ({result['seconds']} s). Warm up or use a faster model")
    return problems, lines


def main():
    parser = argparse.ArgumentParser(description="Check the demo app before going on stage.")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    problems, lines = check(args.url)
    print("\n".join(lines))
    if problems:
        print("\nFix before the demo:")
        print("\n".join(f"  - {p}" for p in problems))
        sys.exit(1)
    print("\nAll green. Good luck!")


if __name__ == "__main__":
    main()
