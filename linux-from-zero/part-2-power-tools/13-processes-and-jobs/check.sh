#!/usr/bin/env bash
# check.sh - lesson 13: checks you cleaned up your practice processes, plus a short quiz on signals.
# Run it from the course folder with:
#   bash part-2-power-tools/13-processes-and-jobs/check.sh
# It only LOOKS (with pgrep). It never stops anything for you.

p="$HOME/linux-practice/13"
passed=0
total=0

ok()  { passed=$((passed + 1)); total=$((total + 1)); printf '✅ %s\n' "$1"; }
bad() { total=$((total + 1)); printf '❌ %s\n   hint: %s\n' "$1" "$2"; }

# ask "question" "hint" "right answer" ["another right answer" ...]
# Reads one line from you, ignores capitals and extra spaces, and compares.
ask() {
  question="$1"; hint="$2"; shift 2
  printf '\n%s\n> ' "$question"
  IFS= read -r answer || answer=""
  answer="$(printf '%s' "$answer" | tr '[:upper:]' '[:lower:]' | sed 's/^ *//; s/ *$//')"
  for right in "$@"; do
    right="$(printf '%s' "$right" | tr '[:upper:]' '[:lower:]')"
    if [ "$answer" = "$right" ]; then
      ok "Correct: $answer"
      return
    fi
  done
  bad "Not quite (you typed: '$answer')" "$hint"
}

if [ ! -f "$p/counter.sh" ]; then
  echo "❌ $p does not exist. Run setup.sh first (see Run it, step 1)."
  exit 1
fi

echo "Checking your processes ..."
echo ""
echo "Clean-up:"
for prog in counter.sh polite-server.sh stubborn.sh hog.sh; do
  # pgrep -u finds processes of this user; -f matches the whole command line
  if pgrep -u "$(id -u)" -f "$prog" >/dev/null; then
    bad "$prog is still running" "pgrep -af $prog shows its PID; stop it with: pkill -f $prog   (stubborn.sh needs: pkill -9 -f stubborn.sh)"
  else
    ok "$prog is not running"
  fi
done

echo ""
echo "Try this:"
if [ -f "$p/counter.log" ] && [ "$(grep -c '^count' "$p/counter.log")" -ge 3 ]; then
  ok "1. counter.log was written by a nohup background job"
else
  bad "1. counter.log should have at least 3 'count' lines" "cd ~/linux-practice/13 && nohup ./counter.sh > counter.log 2>&1 &   wait 5 seconds, then pkill -f counter.sh"
fi

echo ""
echo "Quiz:"
ask "2. Which signal NUMBER can never be caught or ignored (the 'force kill')?" \
    "kill -l lists all signals with their numbers" \
    "9" "sigkill" "kill"
ask "3. Which signal does a plain 'kill PID' send? (name or number)" \
    "the polite one: look at what polite-server.sh traps" \
    "term" "sigterm" "15"
ask "4. Which keys pause a running foreground job so you can type 'bg'?" \
    "the same keys printed '[1]+ Stopped' in Run it" \
    "ctrl+z" "ctrl-z" "ctrl z" "^z"

echo ""
echo "Result: $passed of $total checks passed."
if [ "$passed" -eq "$total" ]; then
  echo "You're in control of every process. On to lesson 14!"
else
  echo "Fix the ❌ lines, then run the check again."
  exit 1
fi
