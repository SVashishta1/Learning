#!/usr/bin/env bash
# check.sh - checks lesson 26 by running the security audit. Run it with:  sudo ./check.sh
# It passes when the five things you set up are in place. (Pending updates and reboots
# do not count against you here: they change every day.)

cd "$(dirname "$0")" || exit 1
report=$(./security-audit.sh)            # run the audit and keep its whole output
echo "$report"
echo ""
echo "Checking lesson 26..."

missing=0
for must in "ufw is active" "SSH passwords are off" "root cannot log in" \
            "fail2ban watches SSH" "automatic security updates are on"; do
  if grep -q "PASS  $must" <<< "$report"; then      # <<< = feed the text into grep
    echo "  PASS  $must"
  else
    echo "  FAIL  $must"
    missing=$(( missing + 1 ))
  fi
done

echo ""
if (( missing == 0 )); then
  echo "All done. This server is far harder to break into than a fresh one."
else
  echo "$missing item(s) missing. Follow the 'fix:' hints in the audit above."
fi
(( missing == 0 ))
