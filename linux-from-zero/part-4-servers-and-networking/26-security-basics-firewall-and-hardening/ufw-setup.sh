#!/usr/bin/env bash
# ufw-setup.sh - switches on a simple, safe firewall with ufw ("uncomplicated firewall").
#   - block every incoming connection by default
#   - allow outgoing connections (updates, API calls)
#   - allow SSH (with rate limiting), so you do not lock yourself out
#   - with --web: also allow HTTP (80) and HTTPS (443) for a web server
# Usage:  sudo ./ufw-setup.sh [--web]

set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Please run with sudo:  sudo $0 $*" >&2; exit 1; }
command -v ufw > /dev/null || { echo "ufw is missing: sudo apt install ufw" >&2; exit 1; }

web="no"
[[ "${1:-}" == "--web" ]] && web="yes"

# Which port does sshd listen on? (usually 22). sshd -T prints the effective settings.
[[ -d /run/sshd ]] || install -d -m 755 /run/sshd    # sshd -T needs this (empty) runtime folder
ssh_port=$(sshd -T 2> /dev/null | awk '$1 == "port" {print $2; exit}') || true   # || true: no sshd = use 22
ssh_port="${ssh_port:-22}"
echo "SSH port detected: $ssh_port"

ufw default deny incoming        # nobody may connect in, unless a rule below allows it
ufw default allow outgoing       # this server may connect out (apt, pip, the Claude API...)

# "limit" = allow, but block an IP for a while if it opens 6+ connections in 30 seconds (slows guessers).
# Allow SSH BEFORE enabling, or an SSH session could be cut off and you would be locked out.
ufw limit "$ssh_port/tcp" comment 'SSH'

if [[ "$web" == "yes" ]]; then
  ufw allow 80/tcp comment 'HTTP'
  ufw allow 443/tcp comment 'HTTPS'
fi

ufw --force enable               # --force = do not ask "this may disrupt SSH, proceed?"
ufw status verbose
