#!/usr/bin/env bash
# net-info.sh - "where am I on the network?" in one screen. Changes nothing.
# Run it with:  ./net-info.sh

set -uo pipefail     # no -e: some of these commands may fail on some systems, and that is fine

echo "=== Computer name ==="
hostname                                        # this machine's name

echo ""
echo "=== My IP addresses (ip -brief address) ==="
# lo = loopback (127.0.0.1, "myself"); eth0 / ens3 / wlan0 = real network cards
ip -brief address

echo ""
echo "=== Default gateway: the router my traffic leaves through (ip route) ==="
ip route show default

echo ""
echo "=== DNS servers: who I ask to turn names into IP addresses ==="
if command -v resolvectl > /dev/null && resolvectl status > /dev/null 2>&1; then
  resolvectl status | grep -E "DNS Servers|Current DNS" | sort -u   # systemd-resolved (normal Ubuntu)
else
  grep '^nameserver' /etc/resolv.conf                               # the classic file (Docker, WSL)
fi

echo ""
echo "=== Programs listening for connections (ss) ==="
# -t TCP, -u UDP, -l listening only, -n numbers instead of names. (sudo ss -tulpn also shows the program.)
ss -tuln

echo ""
echo "=== My public IP (what websites see) ==="
# curl -s = silent, -m 5 = give up after 5 seconds. ifconfig.me replies with your public address.
curl -s -m 5 https://ifconfig.me || echo "(could not reach ifconfig.me)"
echo ""
