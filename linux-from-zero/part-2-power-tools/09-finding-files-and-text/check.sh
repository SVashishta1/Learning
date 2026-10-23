#!/usr/bin/env bash
# check.sh - lesson 09: a quiz (answer with find and grep) plus checks for the Try this exercises.
# Run it from the course folder with:
#   bash part-2-power-tools/09-finding-files-and-text/check.sh
# It only READS ~/linux-practice/09. (Scripting is explained in Part 3.)

practice="$HOME/linux-practice/09"
p="$practice/project"
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

if [ ! -d "$p" ]; then
  echo "❌ $p does not exist. Run setup.sh first (see Run it, step 1)."
  exit 1
fi

echo "Lesson 09 quiz. Work in a second terminal, in ~/linux-practice/09/project."

ask "1. How many .py files are in the project (all folders)?" \
    "find . -name \"*.py\" | wc -l" \
    "5"
ask "2. Which file is bigger than 1 MB? (just its name)" \
    "find . -size +1M" \
    "big-dataset.csv"
ask "3. How many lines of logs/app-2026-03-14.log contain ERROR (capitals)?" \
    "grep -c ERROR logs/app-2026-03-14.log" \
    "5"
ask "4. Which file holds the API key? (its name)" \
    "grep -r API_KEY .   (the file is hidden!)" \
    ".env" "./.env"
ask "5. On which line number of src/app.py is the TODO?" \
    "grep -n TODO src/app.py" \
    "4"

echo ""
echo "Try this:"
py="$practice/py-files.txt"
if [ -f "$py" ] && [ "$(grep -c '\.py$' "$py")" -eq 5 ]; then
  ok "1. py-files.txt lists the 5 .py files"
else
  bad "1. py-files.txt should list the 5 .py files" "cd ~/linux-practice/09/project && find . -name \"*.py\" > ../py-files.txt"
fi

todo="$practice/todo-report.txt"
if [ -f "$todo" ] && [ "$(wc -l < "$todo" | tr -d ' ')" -eq 3 ] && grep -q ':[0-9][0-9]*:' "$todo"; then
  ok "2. todo-report.txt has the 3 TODO lines (any case) with line numbers"
else
  bad "2. todo-report.txt should have 3 lines like src/app.py:4:# TODO..." "grep -rni todo --include=\"*.py\" . > ../todo-report.txt"
fi

if [ ! -e "$p/logs/old/app-2020-01-10.log" ] && [ -f "$p/logs/app-2026-03-14.log" ]; then
  ok "3. the old 2020 log is deleted and the new log is kept"
else
  bad "3. delete ONLY logs older than a year" "find logs -name \"*.log\" -mtime +365 (look first!), then add -delete"
fi

echo ""
echo "Result: $passed of $total correct."
if [ "$passed" -eq "$total" ]; then
  echo "You can find anything, anywhere. On to lesson 10!"
else
  echo "Use the hints, then run the check again. (setup.sh starts you over.)"
  exit 1
fi
