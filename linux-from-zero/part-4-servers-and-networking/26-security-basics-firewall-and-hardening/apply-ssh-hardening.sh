#!/usr/bin/env bash
# apply-ssh-hardening.sh - installs 01-hardening.conf for sshd, SAFELY:
#   1. refuses unless the user who ran sudo already has an SSH key installed (or you would be locked out)
#   2. tests the new config with "sshd -t" before using it, and rolls back if the test fails
#   3. reloads sshd (existing sessions stay open), then shows the settings now in force
# Usage:  sudo ./apply-ssh-hardening.sh

set -euo pipefail
cd "$(dirname "$0")"
[[ $EUID -eq 0 ]] || { echo "Please run with sudo:  sudo $0" >&2; exit 1; }

# $SUDO_USER = the user who typed "sudo". getent passwd ... | cut -d: -f6 = that user's home folder.
user="${SUDO_USER:-root}"
home=$(getent passwd "$user" | cut -d: -f6)
keys="$home/.ssh/authorized_keys"

if [[ ! -s "$keys" ]]; then                                 # -s = exists and is not empty
  echo "STOP: $keys is missing or empty." >&2
  echo "Passwords are about to be switched off. Install your key first (lesson 24: ssh-copy-id)." >&2
  exit 1
fi
echo "OK: $user has $(grep -c . "$keys") key(s) in $keys"

dropin="/etc/ssh/sshd_config.d/01-hardening.conf"
install -m 644 01-hardening.conf "$dropin"

[[ -d /run/sshd ]] || install -d -m 755 /run/sshd    # sshd -t needs this (empty) runtime folder
if sshd -t; then                                           # -t = test the config, change nothing
  echo "OK: sshd -t says the configuration is valid"
else
  rm -f "$dropin"                                          # roll back
  echo "STOP: the configuration has an error, so the change was removed." >&2
  exit 1
fi

# Ubuntu calls the service "ssh"; some other systems call it "sshd". reload = re-read config, keep sessions.
systemctl reload ssh 2> /dev/null || systemctl reload sshd 2> /dev/null || true

echo ""
echo "Settings now in force (sshd -T prints the effective configuration):"
sshd -T | grep -E '^(permitrootlogin|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|maxauthtries|logingracetime|x11forwarding) '
echo ""
echo "IMPORTANT: keep this session open, and test a NEW login in another terminal before logging out."
