"""relief_tools.py: the "world" of the Marrow Valley flood (fictional) and the plain-Python tools agents use.

No AI in this file. Code is better than a model at: parsing file formats, maths, maps, stock counts and rules.
The agents (team.py) decide WHAT to do with these tools; this file makes sure the facts are right.
"""
import csv
import difflib
import email
import heapq
import json
import math
import re
from email import policy
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

NEED_TYPES = ["rescue", "medical", "water", "fuel", "food", "shelter", "blankets", "hygiene", "tarps"]
SEVERITY_WEIGHT = {"life_threatening": 100, "urgent": 30, "stable": 5}
NEED_WEIGHT = {"rescue": 3.0, "medical": 2.0, "water": 1.6, "fuel": 1.5, "food": 1.2, "shelter": 1.2,
               "blankets": 1.0, "hygiene": 0.7, "tarps": 0.6}
VULNERABLE_GROUPS = ["children", "elderly", "pregnant", "patients", "disabled"]
# Which depot item covers which need, and how much per person (simple planning standards for 2 days,
# inspired by the Sphere humanitarian standards: ~3 litres of drinking water per person per day).
PLANNING = {"water": ("water_l", 6.0), "food": ("food_ration", 2.0), "blankets": ("blanket", 1.0),
            "hygiene": ("hygiene_kit", 0.25), "tarps": ("tarp", 0.4), "medical": ("medical_kit", 0.2)}
NOT_STOCKED = {"rescue": "fire_rescue", "fuel": "valley_power", "shelter": "red_cross"}
INJECTION = re.compile(r"ignore (all )?(previous|prior) instructions|system override|you are now|new instructions",
                       re.IGNORECASE)
PHONE_OR_EMAIL = re.compile(r"\+?\d[\d \-]{6,}\d|[\w.+-]+@[\w-]+\.[\w.]+")


# ------------------------------------------------------------------ reading the inbox (5 file formats)
def read_inbox(folder: Path = DATA / "field_reports") -> list[dict]:
    """Turns every file in the folder into a list of plain items: {id, source, format, sender, time, text}."""
    items = []

    def add(source, fmt, text, sender="", time=""):
        items.append({"id": f"R{len(items) + 1}", "source": source, "format": fmt,
                      "sender": sender, "time": time, "text": text.strip()})

    for path in sorted(folder.iterdir()):
        if path.suffix == ".txt" and path.name.startswith("sms"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#"):
                    time, sender, message = [p.strip() for p in line.split("|", 2)]
                    add(path.name, "sms", message, sender, time)
        elif path.suffix == ".txt":                                   # radio log: "HHMM caller: message"
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#"):
                    hhmm, rest = line.split(" ", 1)
                    caller, message = rest.split(":", 1)
                    add(path.name, "radio", f"{caller.strip()}: {message.strip()}", caller.strip(), hhmm)
        elif path.suffix == ".csv":
            with path.open(encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    needs = ", ".join(n for n in row["needs"].split(";") if n)
                    add(path.name, "csv",
                        f"Shelter census: {row['shelter']} has {row['people']} people "
                        f"({row['children']} children, {row['elderly']} elderly). Needs: {needs}. Notes: {row['notes']}",
                        row["shelter"], row["time"])
        elif path.suffix == ".json":
            survey = json.loads(path.read_text(encoding="utf-8"))
            for obs in survey["observations"]:
                x, y = obs["grid"]
                add(path.name, "drone", f"Drone survey at grid {x},{y} (confidence {obs['confidence']}): "
                                        f"{obs['observation']}", survey["mission"], survey["time"])
        elif path.suffix == ".eml":
            msg = email.message_from_string(path.read_text(encoding="utf-8"), policy=policy.default)
            body = msg.get_body(preferencelist=("plain",)).get_content()
            add(path.name, "email", f"Email, subject '{msg['subject']}': {' '.join(body.split())}",
                msg["from"], msg["date"])
    return items


# ------------------------------------------------------------------ the world (one per mission)
class World:
    def __init__(self, scenario: dict | None = None):
        scenario = scenario or {}
        self.scenario = scenario
        everything = read_inbox()
        self.inbox = [r for r in everything if r["id"] not in scenario.get("drop_reports", [])]
        for k, extra in enumerate(scenario.get("extra_reports", []), 1):      # ids continue after the files' ids
            self.inbox.append({"id": f"R{len(everything) + k}", "source": "extra", "format": "sms",
                               "sender": extra.get("sender", "unknown"), "time": extra.get("time", ""),
                               "text": extra["text"]})
        with (DATA / "gazetteer.csv").open(encoding="utf-8") as f:
            self.places = {r["place"]: {"x": float(r["x_km"]), "y": float(r["y_km"]), "kind": r["kind"],
                                        "population": int(r["population"]),
                                        "aliases": [a for a in r["aliases"].split(";") if a]} for r in csv.DictReader(f)}
        with (DATA / "roads.csv").open(encoding="utf-8") as f:
            self.roads = [{"a": r["from"], "b": r["to"], "km": float(r["km"]), "status": r["status"]}
                          for r in csv.DictReader(f)]
        for key, status in scenario.get("road_status", {}).items():       # e.g. {"Kestrel Bridge|Riverside": "flooded"}
            a, b = key.split("|")
            for road in self.roads:
                if {road["a"], road["b"]} == {a, b}:
                    road["status"] = status
        depot = json.loads((DATA / "depot.json").read_text(encoding="utf-8"))
        self.depot = depot["depot"]
        self.items = depot["items"]
        for item, qty in scenario.get("stock", {}).items():
            self.items[item]["stock"] = qty
        self.fleet = {v["id"]: v for v in depot["fleet"]}
        self.partners = depot["partners"]
        self.incidents: dict[str, dict] = {}
        self.needs: dict[str, dict] = {}
        self.drafts: dict[str, dict] = {}
        self.outbox: list[str] = []          # what was "sent" after approval (simulated)
        self.departed: list[dict] = []       # vehicles that actually left (simulated)

    # ---------- intake ----------
    def report(self, report_id: str) -> dict:
        for r in self.inbox:
            if r["id"] == report_id:
                return r
        raise KeyError(f"No report {report_id}. Use list_inbox to see the ids.")

    def record_incident(self, report_ids, place_text, people, needs, vulnerable, severity, language,
                        summary_en, suspicious=False) -> dict:
        for rid in report_ids:
            self.report(rid)                                    # raises if an id is wrong
        bad = [n for n in needs if n not in NEED_TYPES]
        if bad:
            raise ValueError(f"Unknown need types {bad}. Use only: {NEED_TYPES}")
        incident = {"id": f"I{len(self.incidents) + 1}", "report_ids": list(report_ids), "place_text": place_text,
                    "place": None, "people": people, "needs": sorted(set(needs)),
                    "vulnerable": sorted(set(vulnerable)), "severity": severity, "languages": [language],
                    "summary_en": summary_en, "suspicious": suspicious or any(
                        INJECTION.search(self.report(r)["text"]) for r in report_ids), "merged_into": None}
        self.incidents[incident["id"]] = incident
        return incident

    def active_incidents(self) -> list[dict]:
        return [i for i in self.incidents.values() if not i["merged_into"]]

    # ---------- geo ----------
    def geocode(self, place_text: str) -> dict:
        """Place name, alias, small typo, a place name inside a sentence, or 'grid x,y' -> a known place."""
        t = place_text.strip().lower()
        grid = re.search(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", t)
        if grid:
            x, y = float(grid.group(1)), float(grid.group(2))
            name, dist = min(((n, math.dist((x, y), (p["x"], p["y"]))) for n, p in self.places.items()),
                             key=lambda pair: pair[1])
            if dist <= 1.5:
                return {"place": name, "method": "grid", "confidence": round(1 - dist / 3, 2), "km_off": round(dist, 2)}
            return {"place": None, "method": "grid", "note": f"nearest is {name}, {dist:.1f} km away (too far)"}
        names = {n.lower(): n for n in self.places}
        for n, p in self.places.items():
            for alias in [n] + p["aliases"]:
                names[alias.lower()] = n
        if t in names:
            return {"place": names[t], "method": "exact", "confidence": 1.0}
        close = difflib.get_close_matches(t, list(names), n=1, cutoff=0.8)
        if close:
            return {"place": names[close[0]], "method": "fuzzy", "confidence": 0.8, "matched": close[0]}
        inside = [alias for alias in sorted(names, key=len, reverse=True) if re.search(rf"\b{re.escape(alias)}\b", t)]
        if inside:
            return {"place": names[inside[0]], "method": "contains", "confidence": 0.7, "matched": inside[0]}
        return {"place": None, "method": "none", "candidates": difflib.get_close_matches(t, list(names), n=3, cutoff=0.4)}

    def set_location(self, incident_id: str, place: str) -> dict:
        if place not in self.places:
            raise ValueError(f"{place!r} is not in the gazetteer. Known places: {list(self.places)}")
        inc = self.incidents[incident_id]
        inc["place"] = place
        return {"incident_id": incident_id, "place": place, "x": self.places[place]["x"], "y": self.places[place]["y"]}

    def merge(self, keep_id: str, merge_ids: list[str], reason: str) -> dict:
        keep = self.incidents[keep_id]
        for mid in merge_ids:
            other = self.incidents[mid]
            if mid == keep_id or other["merged_into"]:
                raise ValueError(f"{mid} cannot be merged (same incident or already merged)")
            keep["report_ids"] += other["report_ids"]
            keep["needs"] = sorted(set(keep["needs"]) | set(other["needs"]))
            keep["vulnerable"] = sorted(set(keep["vulnerable"]) | set(other["vulnerable"]))
            keep["languages"] = sorted(set(keep["languages"]) | set(other["languages"]))
            keep["people"] = max([p for p in (keep["people"], other["people"]) if p is not None], default=None)
            keep["suspicious"] = keep["suspicious"] or other["suspicious"]
            if SEVERITY_WEIGHT[other["severity"]] > SEVERITY_WEIGHT[keep["severity"]]:
                keep["severity"] = other["severity"]
            keep["place"] = keep["place"] or other["place"]
            other["merged_into"] = keep_id
        return {"kept": keep_id, "merged": merge_ids, "reason": reason, "incident": keep}

    def route(self, start: str, end: str, vehicle_type: str) -> dict | None:
        """Shortest path (Dijkstra). Trucks use open roads only; boats can also use flooded ones."""
        allowed = {"open"} if vehicle_type == "truck" else {"open", "flooded"}
        graph: dict[str, list] = {}
        for r in self.roads:
            if r["status"] in allowed:
                graph.setdefault(r["a"], []).append((r["b"], r["km"]))
                graph.setdefault(r["b"], []).append((r["a"], r["km"]))
        queue, seen = [(0.0, start, [start])], set()
        while queue:
            km, node, path = heapq.heappop(queue)
            if node == end:
                return {"path": path, "km": round(km, 1)}
            if node in seen:
                continue
            seen.add(node)
            for nxt, d in graph.get(node, []):
                if nxt not in seen:
                    heapq.heappush(queue, (km + d, nxt, path + [nxt]))
        return None

    def access(self, place: str) -> dict:
        out = {"place": place}
        for vtype, speed in (("truck", 30), ("boat", 12)):
            r = self.route(self.depot, place, vtype)
            out[vtype] = None if r is None else {**r, "hours": round(r["km"] / speed, 2)}
        unknown = [f"{r['a']}-{r['b']}" for r in self.roads if r["status"] == "unknown" and place in (r["a"], r["b"])]
        if unknown:
            out["unknown_roads"] = unknown
        return out

    # ---------- needs ----------
    def score_needs(self) -> dict:
        """One row per (incident, need). Score = severity x need weight x people factor x vulnerability."""
        self.needs.clear()
        rows, excluded = [], []
        for inc in self.active_incidents():
            if inc["suspicious"]:
                excluded.append({"incident_id": inc["id"], "reason": "looks like instructions, not a field report"})
                continue
            if not inc["place"]:
                if inc["needs"]:
                    excluded.append({"incident_id": inc["id"], "reason": "no location yet"})
                continue
            people = inc["people"] if inc["people"] is not None else 10
            people_factor = 1 + math.log2(1 + people)
            vulnerability = 1 + 0.25 * len([v for v in inc["vulnerable"] if v in VULNERABLE_GROUPS])
            for need in inc["needs"]:
                score = SEVERITY_WEIGHT[inc["severity"]] * NEED_WEIGHT[need] * people_factor * vulnerability
                rows.append({"incident_id": inc["id"], "place": inc["place"], "need": need, "people": people,
                             "people_estimated": inc["people"] is None, "severity": inc["severity"],
                             "vulnerable": inc["vulnerable"], "score": round(score, 1),
                             "why_score": f"{inc['severity']} x {need} x {people} people"
                                          + (f" x vulnerable: {', '.join(inc['vulnerable'])}" if inc["vulnerable"] else "")})
        rows.sort(key=lambda r: -r["score"])
        for i, row in enumerate(rows, 1):
            row["need_id"] = f"N{i}"
            self.needs[row["need_id"]] = row
        return {"ranked": rows, "excluded": excluded}

    # ---------- logistics ----------
    def reserved(self, actions) -> dict:
        """Stock already promised to dispatches that are pending or approved (not rejected)."""
        used: dict[str, int] = {}
        for a in actions:
            if a.kind == "dispatch" and a.status in {"pending", "approved"}:
                for item, qty in a.args["items"].items():
                    used[item] = used.get(item, 0) + qty
        return used

    def available_stock(self, actions) -> dict:
        used = self.reserved(actions)
        return {k: {"available": v["stock"] - used.get(k, 0), "unit_kg": v["unit_kg"], "label": v["label"]}
                for k, v in self.items.items()}

    def fleet_status(self, actions) -> list[dict]:
        busy = {a.args["vehicle_id"]: a.id for a in actions if a.kind == "dispatch" and a.status in {"pending", "approved", "executed"}}
        return [{**v, "assigned_to": busy.get(v["id"])} for v in self.fleet.values()]

    def suggest_load(self, need_ids: list[str]) -> dict:
        items, not_stocked, notes = {}, [], []
        for nid in need_ids:
            if nid not in self.needs:
                raise KeyError(f"No need {nid}. Ask the needs agent to score needs first.")
            n = self.needs[nid]
            if n["need"] in PLANNING:
                item, per_person = PLANNING[n["need"]]
                qty = max(1, math.ceil(n["people"] * per_person))
                if self.places[n["place"]]["kind"] == "clinic" and item == "medical_kit":
                    qty = max(qty, 3)                         # clinics get a few kits even for small numbers
                items[item] = max(items.get(item, 0), qty)
                if n["people_estimated"]:
                    notes.append(f"{nid}: number of people unknown, planned for 10")
            else:
                not_stocked.append({"need_id": nid, "need": n["need"], "partner": NOT_STOCKED.get(n["need"])})
        weight = sum(q * self.items[i]["unit_kg"] for i, q in items.items())
        return {"items": items, "weight_kg": round(weight, 1), "not_stocked": not_stocked, "notes": notes}

    def check_dispatch(self, vehicle_id, destination, items, need_ids, actions) -> dict:
        """Every rule a human logistician would check. Raises ValueError with a clear reason."""
        if vehicle_id not in self.fleet:
            raise ValueError(f"No vehicle {vehicle_id}. Fleet: {list(self.fleet)}")
        if any(v["id"] == vehicle_id and v["assigned_to"] for v in self.fleet_status(actions)):
            raise ValueError(f"{vehicle_id} already has a trip in this plan")
        vehicle = self.fleet[vehicle_id]
        r = self.route(self.depot, destination, vehicle["type"])
        if r is None:
            raise ValueError(f"No {vehicle['type']} route from {self.depot} to {destination} (roads flooded or unknown)")
        stock = self.available_stock(actions)
        for item, qty in items.items():
            if item not in stock:
                raise ValueError(f"Unknown item {item}. Items: {list(stock)}")
            if qty <= 0:
                raise ValueError(f"Quantity for {item} must be positive")
            if qty > stock[item]["available"]:
                raise ValueError(f"Not enough {item}: asked {qty}, only {stock[item]['available']} available")
        weight = sum(q * self.items[i]["unit_kg"] for i, q in items.items())
        if weight > vehicle["capacity_kg"]:
            raise ValueError(f"Load {weight:.0f} kg is over {vehicle_id}'s capacity of {vehicle['capacity_kg']} kg")
        for nid in need_ids:
            if nid not in self.needs:
                raise ValueError(f"No need {nid}")
            if self.needs[nid]["place"] != destination:
                raise ValueError(f"{nid} is at {self.needs[nid]['place']}, not {destination}")
        return {"route": r, "weight_kg": round(weight, 1),
                "eta_hours": round(r["km"] / vehicle["speed_kmh"], 2)}

    def depart(self, vehicle_id, destination, items, route) -> str:
        """Runs only after human approval: takes the stock out and sends the vehicle (simulated)."""
        for item, qty in items.items():
            if qty > self.items[item]["stock"]:
                raise ValueError(f"Stock changed: only {self.items[item]['stock']} {item} left")
        for item, qty in items.items():
            self.items[item]["stock"] -= qty
        self.departed.append({"vehicle_id": vehicle_id, "destination": destination, "items": items})
        return f"(simulated) {vehicle_id} left {self.depot} for {destination} via {' > '.join(route['path'])}"

    # ---------- comms ----------
    def draft_alert(self, area: str, language: str, text: str) -> dict:
        if area not in self.places:
            raise ValueError(f"Unknown area {area!r}")
        problems = []
        if len(text) > 160:
            problems.append(f"too long ({len(text)} characters; an SMS alert must be 160 or fewer)")
        if PHONE_OR_EMAIL.search(text):
            problems.append("contains a phone number or email address (never share private contact details)")
        if problems:
            raise ValueError("Alert not saved: " + "; ".join(problems))
        draft = {"draft_id": f"D{len(self.drafts) + 1}", "area": area, "language": language, "text": text,
                 "chars": len(text)}
        self.drafts[draft["draft_id"]] = draft
        return draft

    def map_data(self, actions) -> dict:
        """Everything the web page needs to draw the map."""
        return {"places": [{"name": n, **{k: p[k] for k in ("x", "y", "kind")}} for n, p in self.places.items()],
                "roads": [{**r, "ax": self.places[r["a"]]["x"], "ay": self.places[r["a"]]["y"],
                           "bx": self.places[r["b"]]["x"], "by": self.places[r["b"]]["y"]} for r in self.roads],
                "needs": list(self.needs.values()),
                "dispatches": [{"action_id": a.id, "status": a.status, **a.args} for a in actions if a.kind == "dispatch"]}
