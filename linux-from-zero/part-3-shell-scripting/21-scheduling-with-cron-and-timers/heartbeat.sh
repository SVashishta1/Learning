#!/usr/bin/env bash
# heartbeat.sh - writes one line about the computer's health into a log file.
# Scheduled every minute by cron or a systemd timer, it builds a little health diary.
# Usage: heartbeat.sh [LOGFILE]     (default: ~/linux-practice/21/heartbeat.log)

set -euo pipefail                                  # strict mode (lesson 20)

# Scheduled jobs start with a tiny PATH, so we set a sensible one ourselves.
export PATH="/usr/local/bin:/usr/bin:/bin"

log_file="${1:-$HOME/linux-practice/21/heartbeat.log}"
mkdir -p "$(dirname "$log_file")"                  # make sure the log's folder exists

now=$(date "+%Y-%m-%d %H:%M:%S")                   # e.g. 2026-10-22 09:05:01
load=$(cut -d ' ' -f 1-3 /proc/loadavg)            # the 1, 5 and 15 minute load averages (lesson 27)
disk=$(df --output=pcent / | tail -n 1 | tr -d ' ') # how full the main disk is, e.g. 42%

# Who started us? cron and systemd set different things, which helps you see which one ran.
if [[ -n "${INVOCATION_ID:-}" ]]; then             # systemd sets INVOCATION_ID for every run
  by="systemd"
elif [[ -t 1 ]]; then                              # -t 1 = "output goes to a terminal" = you ran it by hand
  by="you"
else
  by="cron"                                        # no terminal and not systemd: almost surely cron
fi

echo "$now  load: $load  disk: $disk  started by: $by" >> "$log_file"   # >> = add one line to the end

# Keep the log small: if it has more than 1000 lines, keep only the newest 1000.
if (( $(wc -l < "$log_file") > 1000 )); then
  tail -n 1000 "$log_file" > "$log_file.tmp" && mv "$log_file.tmp" "$log_file"
fi
