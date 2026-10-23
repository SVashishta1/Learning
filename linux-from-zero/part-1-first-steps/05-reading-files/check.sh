#!/usr/bin/env bash
# check.sh - lesson 05: a short quiz. Find each answer by reading the files in ~/linux-practice/05.
# Run it from the course folder with:
#   bash part-1-first-steps/05-reading-files/check.sh
# (You don't need to understand this file yet. Part 3 teaches scripting.)

practice="$HOME/linux-practice/05"
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

if [ ! -f "$practice/app.log" ]; then
  echo "❌ $practice/app.log does not exist. Run setup.sh first (see Run it, step 2)."
  exit 1
fi

echo "Lesson 05 quiz. Keep a second terminal open in ~/linux-practice/05."

ask "1. How many lines does app.log have?" \
    "wc -l app.log" \
    "120"
ask "2. What time is on the LAST line of app.log? (like 09:15:00)" \
    "tail -n 1 app.log" \
    "09:59:30"
ask "3. How many words are in poem.txt?" \
    "wc -w poem.txt" \
    "79"
ask "4. What kind of file is mystery1? (one word, the first word 'file' says after the colon)" \
    "file mystery1" \
    "png"
ask "5. On which line number of story.txt is the word 'dragon'?" \
    "less -N story.txt, then type /dragon and press Enter (or: cat -n story.txt and scroll)" \
    "217"

echo ""
echo "Result: $passed of $total correct."
if [ "$passed" -eq "$total" ]; then
  echo "You can read any file, big or small. On to lesson 06!"
else
  echo "Try the hints, then run the quiz again."
  exit 1
fi
