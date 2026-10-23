#!/usr/bin/env bash
# check.sh - lesson 03: a short quiz about paths and the treasure hunt.
# Run it from the course folder with:
#   bash part-1-first-steps/03-moving-around-the-filesystem/check.sh
# (You don't need to understand this file yet. Part 3 teaches scripting.)

practice="$HOME/linux-practice/03"
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

if [ ! -d "$practice/house" ]; then
  echo "❌ $practice/house does not exist. Run setup.sh first (see Run it, step 2)."
  exit 1
fi

echo "Lesson 03 quiz. Keep a second terminal open to explore in."

treasure="$practice/house/garden/shed/.secret-box/treasure.txt"

ask "1. What is the secret word in the treasure file?" \
    "follow the clues, starting with: cat ~/linux-practice/03/house/START-HERE.txt" \
    "penguin"
# The second right answer is the literal text "~/..." that you might type (not expanded on purpose).
# shellcheck disable=SC2088
ask "2. What is the ABSOLUTE path of the treasure file? (start with / or ~)" \
    "go to the treasure's folder and run pwd, then add /treasure.txt" \
    "$treasure" "~/linux-practice/03/house/garden/shed/.secret-box/treasure.txt"
ask "3. You are in ~/linux-practice/03/house/kitchen/fridge. Which cd command, using only .., takes you to the house folder?" \
    "each .. goes up one folder: fridge -> kitchen -> house" \
    "cd ../.." "cd ../../"
ask "4. Which top-level folder holds most system settings (config) files? (full path)" \
    "look at the table of important folders in How it works" \
    "/etc" "/etc/"
ask "5. What does 'cd -' do? Type a, b or c.  a) go home  b) go back to the previous folder  c) go to /" \
    "try it: cd /tmp, then cd ~, then cd - and watch the prompt" \
    "b" "b)"

echo ""
echo "Result: $passed of $total correct."
if [ "$passed" -eq "$total" ]; then
  echo "You can find your way around any Linux computer. On to lesson 04!"
else
  echo "Try the hints, then run the quiz again."
  exit 1
fi
