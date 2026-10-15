import subprocess
import sys
from pathlib import Path

import incident_team as it
from fake_llm import FakeClient, text_reply, tool_reply

if not (it.DATA / "app.log").exists():
    subprocess.run([sys.executable, str(Path(it.__file__).with_name("make_incident.py"))], check=True)


def test_tools_on_generated_incident():
    assert "QueuePool" in it.search_logs("QueuePool", 4)
    assert it.search_logs("QueuePool", 4).count("\n") == 5          # header + 2 first + "..." + 2 last
    assert "v2.13.0" in it.recent_deploys()                          # the last good version is in the history
    assert "v2.14.0" in it.recent_deploys()
    assert it.search_runbooks("database connection pool exhausted").startswith("[database_connection_pool_exhausted.md]")


class RoleFake(FakeClient):
    """Replies based on which agent is calling (parallel threads make order unpredictable)."""
    def _create(self, **kw):
        self.calls.append(kw)
        s, n_msgs = kw["system"], len(kw["messages"])
        if "execute exactly" in s and n_msgs == 1:
            return tool_reply("rollback_deploy", {"service": "checkout-api", "to_version": "v2.13.0", "reason": "leak"})
        if "postmortems" in s:
            return text_reply("# Postmortem\nRolled back checkout-api.")
        return text_reply("done")


def test_full_response_needs_human_approval_for_rollback():
    approvals = []
    fake = RoleFake(parsed=[
        it.TriageResult(severity="SEV1", affected_services=["checkout-api"], customer_impact="checkout failing", first_hypothesis="db pool"),
        it.Decision(root_cause="connection leak in v2.14.0", confidence="high", action="rollback_deploy",
                    service="checkout-api", to_version="v2.13.0", reasoning="runbook step 1")])
    it.ACTIONS_TAKEN.clear()
    report, agents = it.respond("checkout errors", client=fake, verbose=False,
                                approver=lambda agent, tool, args: approvals.append(tool) or True)
    assert approvals == ["rollback_deploy"]
    assert it.ACTIONS_TAKEN == ["ROLLBACK checkout-api -> v2.13.0 (leak)"]
    assert report.startswith("# Postmortem") and len(agents) == 6
