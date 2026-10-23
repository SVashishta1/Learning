#!/usr/bin/env bash
# uninstall.sh - removes the quote service, its files and its user.  Run with:  sudo ./uninstall.sh

set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Please run with sudo:  sudo $0" >&2; exit 1; }

systemctl disable --now quote.service 2> /dev/null || true   # stop it, and stop starting it at boot
rm -f /etc/systemd/system/quote.service /etc/quote.env
rm -rf /etc/systemd/system/quote.service.d                   # drop-in overrides, if you made any
systemctl daemon-reload
systemctl reset-failed quote.service 2> /dev/null || true    # forget any old "failed" state
rm -rf /opt/quote
userdel quote 2> /dev/null || true
echo "quote service removed."
