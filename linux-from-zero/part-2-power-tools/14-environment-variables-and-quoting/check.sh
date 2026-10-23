#!/usr/bin/env bash
# check.sh - lesson 14: checks exported variables, your PATH, and your quoting.
# Run it from the course folder, in the SAME terminal where you did the lesson:
#   bash part-2-power-tools/14-environment-variables-and-quoting/check.sh
# It's a child process, so it only sees variables you EXPORTED. That's the point!

p="$HOME/linux-practice/14"
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

# ask_exact: like ask, but capitals COUNT ($HOME and $home are different variables!)
ask_exact() {
  question="$1"; hint="$2"; shift 2
  printf '\n%s\n> ' "$question"
  IFS= read -r answer || answer=""
  answer="$(printf '%s' "$answer" | sed 's/^ *//; s/ *$//')"
  for right in "$@"; do
    if [ "$answer" = "$right" ]; then
      ok "Correct: $answer"
      return
    fi
  done
  bad "Not quite (you typed: '$answer'). Capitals matter here." "$hint"
}

if [ ! -d "$p/bin" ]; then
  echo "❌ $p does not exist. Run setup.sh first (see Run it, step 1)."
  exit 1
fi

echo "Checking your environment ..."
echo ""
echo "Run it:"

if [ -n "${FAVORITE_COLOR:-}" ]; then
  ok "FAVORITE_COLOR is exported (I can see: $FAVORITE_COLOR)"
else
  bad "I can't see FAVORITE_COLOR" "export FAVORITE_COLOR=blue   (step 5). Run this check in the same terminal"
fi

case ":$PATH:" in
  *":$p/bin:"*) ok "your PATH includes ~/linux-practice/14/bin" ;;
  *) bad "your PATH doesn't include ~/linux-practice/14/bin" "export PATH=\"\$HOME/linux-practice/14/bin:\$PATH\"   (step 9)" ;;
esac

if command -v hello-tool >/dev/null 2>&1; then
  ok "hello-tool can be run by name from anywhere"
else
  bad "hello-tool is not found by name" "fix your PATH (step 9), then: which hello-tool"
fi

echo ""
echo "Try this:"
if [ -f "$p/greeting.txt" ] && grep -q "Hello, Alice." "$p/greeting.txt"; then
  ok "1. greeting.txt greets Alice (a one-off variable)"
else
  bad "1. greeting.txt should contain 'Hello, Alice.'" "cd ~/linux-practice/14 && GREETING_NAME=Alice hello-tool > greeting.txt"
fi

found_report=no
for f in "$p"/report\ 20[0-9][0-9].txt; do
  [ -f "$f" ] && found_report=yes
done
if [ "$found_report" = yes ]; then
  ok "2. 'report <year>.txt' exists (command substitution + quotes)"
else
  bad "2. no file like 'report 2026.txt'" "cd ~/linux-practice/14 && touch \"report \$(date +%Y).txt\""
fi

ask_exact "3. What does   echo '\$HOME'   print (with SINGLE quotes)?" \
    "single quotes keep everything exactly as typed" \
    "\$HOME"
ask "4. What does   echo \"\$((6 * 7)) apples\"   print?" \
    "\$(( )) does arithmetic, and double quotes still allow \$" \
    "42 apples"

echo ""
echo "Result: $passed of $total checks passed."
if [ "$passed" -eq "$total" ]; then
  echo "Your shell does exactly what you mean. On to lesson 15!"
else
  echo "Fix the ❌ lines, then run the check again (in the same terminal)."
  exit 1
fi
