#!/usr/bin/env bash
# security-audit.sh - a read-only security health check for an Ubuntu server. Changes nothing.
# Prints PASS / WARN for each check, then exits with the number of warnings (0 = all good).
# Usage:  sudo ./security-audit.sh     (without sudo some checks cannot look and will WARN)

set -uo pipefail                       # no -e: a failing check must not stop the audit

warns=0
pass() { echo "  PASS  $1"; }
warn() { echo "  WARN  $1"; echo "        fix: $2"; warns=$((warns + 1)); }

echo "Security audit of $(hostname) - $(date '+%F %H:%M')"
[[ $EUID -eq 0 ]] || echo "  (not running as root: some checks may wrongly WARN; use sudo)"

echo ""
echo "--- Firewall ---"
ufw_status=$(ufw status verbose 2> /dev/null)
if grep -q "Status: active" <<< "$ufw_status"; then
  pass "ufw is active"
  if grep -q "deny (incoming)" <<< "$ufw_status"; then
    pass "incoming connections are denied by default"
  else
    warn "incoming connections are NOT denied by default" "sudo ufw default deny incoming"
  fi
else
  warn "ufw firewall is not active" "sudo ./ufw-setup.sh"
fi

echo ""
echo "--- SSH server ---"
if command -v sshd > /dev/null; then
  # sshd -T = the settings really in force, after reading every config file (lowercase names)
  # sshd -T refuses to run if its empty runtime folder /run/sshd is missing (before the first login
  # on Ubuntu 24.04). Creating that empty folder is the only thing this audit ever changes.
  [[ -d /run/sshd || $EUID -ne 0 ]] || install -d -m 755 /run/sshd
  sshd_conf=$(sshd -T 2> /dev/null)
  setting() { awk -v k="$1" '$1 == k {print $2; exit}' <<< "$sshd_conf"; }
  if [[ "$(setting passwordauthentication)" == "no" ]]; then
    pass "SSH passwords are off (keys only)"
  else
    warn "SSH accepts passwords" "sudo ./apply-ssh-hardening.sh"
  fi
  if [[ "$(setting permitrootlogin)" == "no" ]]; then
    pass "root cannot log in over SSH"
  else
    warn "root may log in over SSH ($(setting permitrootlogin))" "sudo ./apply-ssh-hardening.sh"
  fi
else
  pass "no SSH server installed (nothing to harden)"
fi

echo ""
echo "--- Brute-force protection ---"
if systemctl is-active --quiet fail2ban 2> /dev/null; then
  pass "fail2ban is running"
  if fail2ban-client status sshd > /dev/null 2>&1; then
    pass "fail2ban watches SSH (jail 'sshd')"
  else
    warn "fail2ban has no 'sshd' jail" "sudo cp jail.local /etc/fail2ban/ && sudo systemctl restart fail2ban"
  fi
else
  warn "fail2ban is not running" "sudo apt install fail2ban, then Run it, step 10"
fi

echo ""
echo "--- Updates ---"
if grep -qs 'Unattended-Upgrade "1"' /etc/apt/apt.conf.d/20auto-upgrades; then   # -s = no error if missing
  pass "automatic security updates are on"
else
  warn "automatic security updates are off" "sudo apt install unattended-upgrades && sudo cp 20auto-upgrades /etc/apt/apt.conf.d/"
fi
# apt list --upgradable prints a header line, then one line per package that has an update
pending=$(apt list --upgradable 2> /dev/null | grep -c upgradable)
if (( pending == 0 )); then
  pass "no pending package updates"
else
  warn "$pending package update(s) waiting" "sudo apt update && sudo apt upgrade"
fi
if [[ -f /var/run/reboot-required ]]; then
  warn "a reboot is needed to finish updates (often a new kernel)" "sudo reboot (at a quiet time)"
else
  pass "no reboot required"
fi

echo ""
echo "--- Accounts and files ---"
# awk -F: = split /etc/passwd at ':'; $3 = user ID. Only root should have ID 0 (full power).
extra_root=$(awk -F: '$3 == 0 && $1 != "root" {print $1}' /etc/passwd)
if [[ -z "$extra_root" ]]; then
  pass "only 'root' has user ID 0"
else
  warn "other users with root power (UID 0): $extra_root" "investigate: this is a classic sign of a break-in"
fi
user_home=$(getent passwd "${SUDO_USER:-$USER}" | cut -d: -f6)
# find -perm -0002 = writable by everybody; -not -type l = ignore symbolic links
ww=$(find "$user_home" -xdev -perm -0002 -not -type l 2> /dev/null | head -n 5)
if [[ -z "$ww" ]]; then
  pass "no world-writable files in $user_home"
else
  warn "world-writable files in $user_home (anyone can change them): $(echo "$ww" | tr '\n' ' ')" "chmod o-w FILE"
fi

echo ""
echo "--- Open doors (programs listening on all addresses) ---"
# ss -tlnH = TCP, listening, numeric, no header. $4 = local address:port.
ss -tlnH | awk '$4 ~ /^(0\.0\.0\.0|\[::\]|\*):/ {print "  listening:", $4}' | sort -u
echo "  (each of these must be either needed and allowed by the firewall, or bound to 127.0.0.1)"

echo ""
if (( warns == 0 )); then
  echo "Result: all checks passed."
else
  echo "Result: $warns warning(s)."
fi
exit "$warns"
