#!/usr/bin/env bash
# check.sh - checks that a scheduler (cron or a systemd timer) is really running your job.
# Run it with:  ./check.sh   (wait 2-3 minutes after installing, so some runs have happened)

log="$HOME/linux-practice/21/heartbeat.log"
pass=0
fail=0
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL  $1"; echo "        hint: $2"; fail=$((fail + 1)); }

echo "Checking lesson 21..."

# 1. Is the job scheduled in at least one of the two ways?
in_cron=no
in_timer=no
crontab -l 2> /dev/null | grep -q "linux-practice/21/heartbeat.sh" && in_cron=yes
systemctl --user is-active --quiet heartbeat.timer 2> /dev/null && in_timer=yes
if [[ "$in_cron" == yes || "$in_timer" == yes ]]; then
  ok "heartbeat is scheduled (cron: $in_cron, systemd timer: $in_timer)"
else
  bad "heartbeat is not scheduled" "run ./install-cron.sh (or ./install-timer.sh)"
fi

# 2. Did a scheduler (not you) actually run it?
# grep -c counts matching lines; || true stops a "0 found" from counting as an error.
auto_runs=$(grep -c -E "started by: (cron|systemd)" "$log" 2> /dev/null || true)
if (( ${auto_runs:-0} >= 2 )); then
  ok "$auto_runs automatic runs found in heartbeat.log"
else
  bad "only ${auto_runs:-0} automatic run(s) in $log (need 2)" \
      "wait 2 minutes; if still nothing, read ~/linux-practice/21/cron.log and 'If something goes wrong'"
fi

# 3. Show the newest lines so you can see it working
echo ""
echo "Newest log lines:"
tail -n 3 "$log" 2> /dev/null | sed 's/^/    /'      # sed adds 4 spaces in front of each line

echo ""
echo "Result: $pass passed, $fail failed."
(( fail == 0 )) && echo "All done. Remember to remove the every-minute job: ./remove-cron.sh or ./remove-timer.sh"
(( fail == 0 ))
