#!/usr/bin/env bash
# install-timer.sh - installs the heartbeat as a systemd USER timer (no sudo needed).
# Needs a Linux that runs systemd (Ubuntu, a VM, WSL2 with systemd switched on).
# Run it with:  ./install-timer.sh      Undo with:  ./remove-timer.sh

set -euo pipefail
cd "$(dirname "$0")"                                # work from the lesson folder

[[ -x "$HOME/linux-practice/21/heartbeat.sh" ]] || { echo "Run: bash setup.sh first" >&2; exit 1; }

# Is systemd running at all? (/run/systemd/system only exists when it is.)
if [[ ! -d /run/systemd/system ]]; then
  echo "systemd is not running here (common in Docker and older WSL). Use cron instead: ./install-cron.sh" >&2
  exit 1
fi

unit_dir="$HOME/.config/systemd/user"               # where YOUR personal units live
mkdir -p "$unit_dir"
cp systemd/heartbeat.service systemd/heartbeat.timer "$unit_dir/"

systemctl --user daemon-reload                      # tell systemd to re-read unit files
systemctl --user enable --now heartbeat.timer       # enable = start at every login; --now = and start it now
systemctl --user restart heartbeat.timer            # if it was already running, restart it so changes apply

echo ""
systemctl --user list-timers heartbeat.timer --no-pager
