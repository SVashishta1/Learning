#!/usr/bin/env bash
# remove-cron.sh - removes ONLY the heartbeat line from your crontab; other lines are kept.
# Run it with:  ./remove-cron.sh

set -euo pipefail
script="$HOME/linux-practice/21/heartbeat.sh"

# Same idea as install-cron.sh: read the crontab, drop our line, install the rest.
crontab -l 2> /dev/null | grep -v -F "$script" | crontab - || true
echo "Removed the heartbeat job. Your crontab is now:"
crontab -l 2> /dev/null | grep . || echo "(empty)"   # grep . = print lines that have at least one character
