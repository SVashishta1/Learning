#!/usr/bin/env bash
# check.sh - "Predict the exit code" quiz for lesson 18.
# It shows you a command, you type the exit code you expect, then it RUNS the command
# and tells you if you were right. Run it with:  ./check.sh
# You need 7 out of 8 to pass.

cd "$(dirname "$0")" || exit 1     # dirname "$0" = the folder this script lives in; go there so ./ paths work

# The quiz questions. Each entry is a command written as text.
questions=(
  "true"
  "false"
  "ls /etc/hostname"
  "grep -q zebra /etc/passwd"
  "[[ 5 -gt 3 ]]"
  "[[ -d /etc/hostname ]]"
  "./check-file.sh"
  "no-such-command"
)

score=0
total=${#questions[@]}             # ${#array[@]} = how many items the list has

for cmd in "${questions[@]}"; do   # loop over every question (loops are lesson 19)
  echo ""
  echo "Command:  $cmd"
  read -r -p "Your guess for its exit code: " guess

  bash -c "$cmd" > /dev/null 2>&1  # bash -c "text" = run that text as a command; hide all output
  real=$?                          # save the real exit code before anything else changes $?

  if [[ "$guess" == "$real" ]]; then
    echo "  Right! It was $real."
    score=$(( score + 1 ))
  else
    echo "  Not quite: it was $real. (Look it up in the README's exit code table.)"
  fi
done

echo ""
echo "Score: $score / $total"
if (( score >= total - 1 )); then
  echo "PASS - you can read exit codes like a pro."
  exit 0
else
  echo "Not yet. Re-read 'How it works', run ./exit-codes.sh again, then retry."
  exit 1
fi
