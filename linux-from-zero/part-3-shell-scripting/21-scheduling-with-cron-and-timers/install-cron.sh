#!/usr/bin/env bash
# install-cron.sh - adds the heartbeat job to YOUR crontab (runs every minute).
# Safe to run twice: it removes its own old line before adding it again.
# Run it with:  ./install-cron.sh      Undo with:  ./remove-cron.sh

set -euo pipefail

script="$HOME/linux-practice/21/heartbeat.sh"     # the copy made by setup.sh
log="$HOME/linux-practice/21/cron.log"            # where cron's output and errors will go

[[ -x "$script" ]] || { echo "Missing $script - run: bash setup.sh" >&2; exit 1; }

line="* * * * * $script >> $log 2>&1"             # minute hour day month weekday  command

# 1. crontab -l prints your current crontab (it fails if you have none yet, hence || true).
# 2. grep -v drops any old heartbeat line (grep -v = keep lines that do NOT match).
# 3. echo adds the new line.
# 4. crontab - (dash) installs whatever comes in through the pipe as your new crontab.
{
  crontab -l 2> /dev/null | grep -v -F "$script" || true
  echo "$line"
} | crontab -

echo "Installed. Your crontab is now:"
crontab -l
