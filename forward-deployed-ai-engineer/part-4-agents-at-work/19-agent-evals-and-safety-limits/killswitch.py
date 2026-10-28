"""killswitch.py: stop every agent in this folder, right now, without deploying anything.

python killswitch.py on       # create the KILL_SWITCH file: agents stop before their next step
python killswitch.py off      # remove it
python killswitch.py status
In production the switch is a shared flag (a database row, a feature flag, an environment variable) that
operations staff can flip; the agent loop checks it before every model call and every tool call.
"""
import sys

from limits import KILL_SWITCH, kill_switch_on

command = sys.argv[1] if len(sys.argv) > 1 else "status"
if command == "on":
    KILL_SWITCH.write_text("Agents stopped by an operator.\n")
elif command == "off":
    KILL_SWITCH.unlink(missing_ok=True)
elif command != "status":
    raise SystemExit("Use: python killswitch.py on | off | status")
print(f"Kill switch is {'ON: agents will stop' if kill_switch_on() else 'off'}")
