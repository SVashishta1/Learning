#!/usr/bin/env bash
# check.sh - checks the quote service from lesson 25.  Run it with:  ./check.sh  (no sudo needed)

pass=0
fail=0
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL  $1"; echo "        hint: $2"; fail=$((fail + 1)); }

echo "Checking lesson 25..."

if systemctl is-active --quiet quote; then             # --quiet = no output, only the exit code
  ok "quote.service is active (running)"
else
  bad "quote.service is not running" "sudo ./install.sh, then: systemctl status quote"
fi

if systemctl is-enabled --quiet quote 2> /dev/null; then
  ok "quote.service is enabled (starts at boot)"
else
  bad "quote.service is not enabled" "sudo systemctl enable quote"
fi

# MainPID = the process ID systemd is watching. ps -o user= prints only the user that owns it.
pid=$(systemctl show -p MainPID --value quote 2> /dev/null)
user=$(ps -o user= -p "${pid:-0}" 2> /dev/null | tr -d ' ')
if [[ "$user" == "quote" ]]; then
  ok "it runs as the unprivileged user 'quote' (PID $pid)"
else
  bad "it runs as '${user:-nobody}', expected 'quote'" "check User= in the unit file"
fi

if curl -fsS -m 3 http://127.0.0.1:8077/health | grep -q '"ok"'; then   # -f = fail on HTTP errors
  ok "GET /health answers ok on port 8077"
else
  bad "no answer on http://127.0.0.1:8077/health" "read the logs: journalctl -u quote -n 20"
fi

restarts=$(systemctl show -p NRestarts --value quote 2> /dev/null)     # how many automatic restarts
if (( ${restarts:-0} >= 1 )); then
  ok "systemd restarted it after a crash ($restarts time(s))"
else
  bad "no automatic restart seen yet" "Run it, step 8: sudo systemctl kill -s KILL quote"
fi

echo ""
echo "Result: $pass passed, $fail failed."
(( fail == 0 )) && echo "All done. You can run programs as proper services!"
(( fail == 0 ))
