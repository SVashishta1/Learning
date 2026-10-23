#!/usr/bin/env bash
# setup.sh - prepares ~/linux-practice/21 for lesson 21. Safe to run again.
# It copies heartbeat.sh there, so cron and systemd use a fixed path that does not
# depend on where you keep this course. Run it with:  bash setup.sh

set -euo pipefail
cd "$(dirname "$0")"                       # the lesson folder, wherever it is

practice="$HOME/linux-practice/21"
mkdir -p "$practice"
cp heartbeat.sh "$practice/heartbeat.sh"   # copy the script into the practice folder
chmod +x "$practice/heartbeat.sh"          # make sure it is executable

echo "Ready: $practice/heartbeat.sh"
"$practice/heartbeat.sh"                    # run it once by hand to prove it works
echo "First line of the log:"
cat "$practice/heartbeat.log"
