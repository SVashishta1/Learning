#!/usr/bin/env bash
# install.sh - installs quote-server.py as a real systemd service called "quote".
# Needs root:  sudo ./install.sh        Undo with:  sudo ./uninstall.sh

set -euo pipefail
cd "$(dirname "$0")"                                  # work from the lesson folder

if [[ $EUID -ne 0 ]]; then                            # $EUID = your user ID; root's is 0
  echo "Please run with sudo:  sudo $0" >&2
  exit 1
fi
if [[ ! -d /run/systemd/system ]]; then
  echo "systemd is not running here (Docker or WSL without systemd). See 'Before you start'." >&2
  exit 1
fi

# 1. A system user for the service: no home folder, no login shell. id -u checks if it exists.
if ! id -u quote > /dev/null 2>&1; then
  useradd --system --no-create-home --shell /usr/sbin/nologin quote
  echo "created system user: quote"
fi

# 2. Put the program in /opt/quote. install = copy + set owner and permissions in one step.
install -d -m 755 /opt/quote                          # -d = make a directory
install -m 644 quote-server.py /opt/quote/quote-server.py

# 3. Put the unit file where systemd looks for admin-made units.
install -m 644 quote.service /etc/systemd/system/quote.service

# 4. Tell systemd to re-read unit files, then start the service now (--now) and at every boot (enable).
systemctl daemon-reload
systemctl enable --now quote.service

sleep 1                                               # give it a moment to start
systemctl status quote.service --no-pager --lines=5
