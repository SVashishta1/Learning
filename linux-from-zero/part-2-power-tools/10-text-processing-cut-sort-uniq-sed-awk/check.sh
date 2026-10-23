#!/usr/bin/env bash
# check.sh - lesson 10: a quiz (answer it with cut, sort, uniq, awk) plus checks for Try this.
# Run it from the course folder with:
#   bash part-2-power-tools/10-text-processing-cut-sort-uniq-sed-awk/check.sh
# It only READS ~/linux-practice/10. (Scripting is explained in Part 3.)

p="$HOME/linux-practice/10"
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

# same FILE "expected text" -> succeeds if FILE has exactly these lines (extra spaces ignored)
same() {
  [ -f "$1" ] || return 1
  [ "$(tr -s ' \t' '  ' < "$1" | sed 's/^ //; s/ $//')" = "$2" ]
}

if [ ! -f "$p/access.log" ]; then
  echo "❌ $p/access.log does not exist. Run setup.sh first (see Run it, step 1)."
  exit 1
fi

echo "Lesson 10 quiz. Work in a second terminal, in ~/linux-practice/10."

ask "1. How many DIFFERENT IP addresses appear in access.log?" \
    "cut -d' ' -f1 access.log | sort -u | wc -l" \
    "5"
ask "2. Which IP address made the most requests?" \
    "cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head -n 1" \
    "203.0.113.7"
ask "3. How many requests got the status code 404?" \
    "awk '\$9 == 404' access.log | wc -l" \
    "38"
ask "4. Which path got the most 404s?" \
    "awk '\$9 == 404 {print \$7}' access.log | sort | uniq -c | sort -rn" \
    "/admin"
ask "5. How many units were sold in total in sales.csv?" \
    "awk -F, 'NR > 1 {sum += \$4} END {print sum}' sales.csv" \
    "78"

echo ""
echo "Try this:"

if same "$p/regions.txt" "$(printf 'east\nnorth\nsouth\nwest')"; then
  ok "1. regions.txt lists the 4 regions once each, A to Z"
else
  bad "1. regions.txt should hold east, north, south, west (one per line, no header)" "cut -d, -f2 sales.csv | tail -n +2 | sort -u > regions.txt"
fi

if same "$p/app.conf" "$(printf '# Settings for the chat API\nport = 8080\nmodel = claude-haiku-5-5\nfallback_model = claude-haiku-5-5\ndebug = false')"; then
  ok "2. app.conf was filled in from the template"
else
  bad "2. app.conf should have port = 8080 and both models = claude-haiku-5-5" "sed -e 's/{{PORT}}/8080/' -e 's/{{MODEL}}/claude-haiku-5-5/' app.conf.template > app.conf"
fi

if same "$p/revenue.txt" "$(printf 'east 8306\nwest 8134\nnorth 7438\nsouth 7174')"; then
  ok "3. revenue.txt has the revenue per region, biggest first"
else
  bad "3. revenue.txt should have 4 lines like 'east 8306', biggest first" "awk -F, 'NR > 1 {rev[\$2] += \$4 * \$5} END {for (r in rev) print r, rev[r]}' sales.csv | sort -k2 -nr > revenue.txt"
fi

echo ""
echo "Result: $passed of $total correct."
if [ "$passed" -eq "$total" ]; then
  echo "You can turn raw text into answers. On to lesson 11!"
else
  echo "Use the hints, then run the check again."
  exit 1
fi
