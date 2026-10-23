#!/usr/bin/env bash
# check.sh - lesson 06: a quiz you can only pass by LOOKING THINGS UP (man, --help, help).
# Run it from the course folder with:
#   bash part-1-first-steps/06-getting-help/check.sh
# (You don't need to understand this file yet. Part 3 teaches scripting.)

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

# ask_exact: like ask, but capitals COUNT (options like -S and -s are different!)
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

echo "Lesson 06 quiz. Look each answer up in a second terminal; don't guess!"

ask_exact "1. Which ls option sorts by file size, largest first? (like -x)" \
    "man ls, then type /size and press Enter; press n for the next match" \
    "-S" "--sort=size"
ask "2. Which manual SECTION number is about file formats and config files?" \
    "man man, then search /sections (or look at the table in How it works)" \
    "5"
ask "3. cd is a shell builtin, so 'man cd' doesn't help. Which command shows cd's help? (two words)" \
    "builtins have their own help command" \
    "help cd"
ask_exact "4. Which cp option asks before overwriting a file? (like -x)" \
    "cp --help, or man cp and search /overwrite" \
    "-i" "--interactive"
ask "5. Which command finds manual pages by a keyword in their description? (either name)" \
    "it's 'man' with one option, or a separate command that means 'appropriate'" \
    "man -k" "apropos"
ask "6. In a SYNOPSIS line like 'ls [OPTION]... [FILE]...', what do the square brackets mean? a) required b) optional c) repeat it" \
    "read the 'Reading a SYNOPSIS' table in How it works" \
    "b" "b)" "optional"

echo ""
echo "Result: $passed of $total correct."
if [ "$passed" -eq "$total" ]; then
  echo "You can teach yourself any command now. On to lesson 07!"
else
  echo "Look up the ones you missed, then run the quiz again."
  exit 1
fi
