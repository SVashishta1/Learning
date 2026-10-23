#!/usr/bin/env bash
# check.sh - lesson 02: a short quiz. Find each answer with a command, then type it in.
# Run it from the course folder with:
#   bash part-1-first-steps/02-anatomy-of-a-command/check.sh
# (You don't need to understand this file yet. Part 3 teaches scripting.)

practice="$HOME/linux-practice/02"
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
    if [ "$answer" = "$right" ]; then
      ok "Correct: $answer"
      return
    fi
  done
  bad "Not quite (you typed: '$answer')" "$hint"
}

if [ ! -d "$practice" ]; then
  echo "❌ $practice does not exist. Run setup.sh first (see Run it, step 2)."
  exit 1
fi

echo "Lesson 02 quiz. Keep a second terminal open to run commands in."

ask "1. How many HIDDEN files are in ~/linux-practice/02? (names starting with a dot; don't count . and ..)" \
    "ls -a ~/linux-practice/02 shows hidden files" \
    "2" "two"
ask "2. How many bytes is notes.txt?" \
    "ls -l ~/linux-practice/02/notes.txt: the size is the number just before the date" \
    "34"
ask "3. Which file in ~/linux-practice/02 is the biggest? (type its name)" \
    "ls -lS ~/linux-practice/02 sorts by size, biggest first" \
    "big-file.log"
ask "4. Is cd a shell builtin or a program file on disk? (type: builtin or file)" \
    "type cd" \
    "builtin" "shell builtin" "a shell builtin"
ask "5. What is the full path of the ls program file?" \
    "type -a ls   or   which ls" \
    "/usr/bin/ls" "/bin/ls"

echo ""
echo "Result: $passed of $total correct."
if [ "$passed" -eq "$total" ]; then
  echo "You can read any command now. On to lesson 03!"
else
  echo "Try the hints, then run the quiz again."
  exit 1
fi
