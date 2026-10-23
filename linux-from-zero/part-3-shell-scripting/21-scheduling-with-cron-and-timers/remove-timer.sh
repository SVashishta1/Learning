#!/usr/bin/env bash
# remove-timer.sh - stops and removes the heartbeat user timer.
# Run it with:  ./remove-timer.sh

set -euo pipefail
unit_dir="$HOME/.config/systemd/user"

systemctl --user disable --now heartbeat.timer 2> /dev/null || true   # stop it and stop starting it
rm -f "$unit_dir/heartbeat.timer" "$unit_dir/heartbeat.service"
systemctl --user daemon-reload
echo "Heartbeat timer removed."
