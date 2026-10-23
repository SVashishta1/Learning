"""End to end in FAKE mode: the whole team, the evals, and the web API."""
from fastapi.testclient import TestClient

from app import app
from evals.run_evals import run
from team import run_relief_mission


def test_full_mission_waits_for_approval_then_executes_only_approved():
    m = run_relief_mission()
    world = m.state["world"]
    assert m.status == "awaiting_approval" and len(m.actions) >= 6
    assert set(m.reports) == {"intake", "geo", "needs", "logistics", "comms", "coordinator"}
    water_before = world.items["water_l"]["stock"]
    first_dispatch = next(a for a in m.actions if a.kind == "dispatch")
    m.decide(first_dispatch.id, True, by="Test officer")
    m.execute_approved()
    assert len(world.departed) == 1 and world.outbox == []              # only the one approved trip happened
    assert world.items["water_l"]["stock"] == water_before - first_dispatch.args["items"].get("water_l", 0)


def test_golden_set_passes_in_fake_mode():
    for row in run():
        failed = [k for k, ok in row["checks"].items() if not ok]
        assert not failed, (row["id"], failed)


def test_web_api_flow():
    c = TestClient(app)
    assert c.get("/").status_code == 200 and "relief command center" in c.get("/").text
    assert "bridge_out" in c.get("/api/scenarios").json()
    mid = c.post("/api/missions", json={"scenario": "baseline"}).json()["id"]
    import time
    for _ in range(50):
        m = c.get(f"/api/missions/{mid}").json()
        if m["status"] != "running":
            break
        time.sleep(0.1)
    assert m["status"] == "awaiting_approval" and m["map"]["needs"]
    alert = next(a for a in m["actions"] if a["kind"] == "public_alert")
    assert c.post(f"/api/missions/{mid}/actions/{alert['id']}", json={"approve": True, "by": ""}).status_code == 400
    assert c.post(f"/api/missions/{mid}/actions/{alert['id']}", json={"approve": True, "by": "Ana"}).json()["status"] == "approved"
    done = c.post(f"/api/missions/{mid}/execute").json()
    assert done[0]["status"] == "executed"
    assert len(c.get(f"/api/missions/{mid}").json()["outbox"]) == 1
