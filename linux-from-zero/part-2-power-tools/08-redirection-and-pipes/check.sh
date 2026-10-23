#!/usr/bin/env bash
# check.sh - lesson 08: checks the files you created with > >> 2> 2>&1 and tee.
# Run it from the course folder with:
#   bash part-2-power-tools/08-redirection-and-pipes/check.sh
# It only READS ~/linux-practice/08. (Scripting is explained in Part 3.)

p="$HOME/linux-practice/08"
passed=0
total=0

ok()  { passed=$((passed + 1)); total=$((total + 1)); printf '✅ %s\n' "$1"; }
bad() { total=$((total + 1)); printf '❌ %s\n   hint: %s\n' "$1" "$2"; }

# lines FILE -> number of lines in FILE (0 if missing)
lines() { if [ -f "$1" ]; then wc -l < "$1" | tr -d ' '; else echo 0; fi; }
# count FILE TEXT -> how many lines of FILE contain TEXT (0 if missing)
count() { if [ -f "$1" ]; then grep -c -- "$2" "$1"; else echo 0; fi; }

if [ ! -f "$p/noisy.sh" ]; then
  echo "❌ $p/noisy.sh does not exist. Run setup.sh first (see Run it, step 1)."
  exit 1
fi

echo "Checking ~/linux-practice/08 ..."
echo ""
echo "Run it:"

if [ -f "$p/files.txt" ] && grep -q "animals.txt" "$p/files.txt"; then
  ok "files.txt holds the output of ls (step 3)"
else
  bad "files.txt missing or doesn't list animals.txt" "ls > files.txt"
fi

if [ "$(lines "$p/diary.txt")" -eq 2 ]; then
  ok "diary.txt has exactly 2 lines, thanks to >> (step 4)"
else
  bad "diary.txt should have 2 lines (it has $(lines "$p/diary.txt"))" "echo \"first entry\" > diary.txt   then   echo \"second entry\" >> diary.txt"
fi

if [ "$(lines "$p/errors.txt")" -eq 2 ] && [ "$(count "$p/errors.txt" ERROR)" -eq 2 ]; then
  ok "errors.txt holds only the 2 ERROR lines (step 8)"
else
  bad "errors.txt should hold exactly the 2 ERROR lines" "bash noisy.sh 2> errors.txt"
fi

if [ "$(count "$p/out.txt" OK)" -eq 3 ] && [ "$(lines "$p/out.txt")" -eq 3 ] \
   && [ "$(count "$p/err.txt" ERROR)" -eq 2 ] && [ "$(lines "$p/err.txt")" -eq 2 ]; then
  ok "out.txt has the 3 OK lines and err.txt the 2 ERROR lines (step 9)"
else
  bad "out.txt / err.txt are not split correctly" "bash noisy.sh > out.txt 2> err.txt"
fi

if [ "$(lines "$p/all.txt")" -eq 5 ]; then
  ok "all.txt has all 5 lines (step 10)"
else
  bad "all.txt should have all 5 lines (it has $(lines "$p/all.txt"))" "bash noisy.sh > all.txt 2>&1   (order matters!)"
fi

if [ "$(count "$p/run.log" OK)" -ge 3 ]; then
  ok "run.log was saved by tee (step 13)"
else
  bad "run.log should have (at least) the 3 OK lines" "bash noisy.sh | tee run.log"
fi

echo ""
echo "Try this:"

if [ -f "$p/sorted-animals.txt" ] && [ "$(sort "$p/animals.txt")" = "$(cat "$p/sorted-animals.txt")" ]; then
  ok "1. sorted-animals.txt is animals.txt sorted A to Z"
else
  bad "1. sorted-animals.txt is missing or not sorted" "sort < animals.txt > sorted-animals.txt"
fi

if [ -f "$p/error-count.txt" ] && [ "$(tr -d ' \n' < "$p/error-count.txt")" = "3" ]; then
  ok "2. error-count.txt says 3"
else
  bad "2. error-count.txt should contain just the number 3" "grep ERROR server.log | wc -l > error-count.txt"
fi

if [ "$(lines "$p/quiet.txt")" -eq 6 ] && [ "$(count "$p/quiet.txt" OK)" -eq 6 ]; then
  ok "3. quiet.txt has 6 OK lines and no errors"
else
  bad "3. quiet.txt should have 6 OK lines (it has $(lines "$p/quiet.txt") lines)" "run twice: bash noisy.sh 2> /dev/null >> quiet.txt"
fi

echo ""
echo "Result: $passed of $total checks passed."
if [ "$passed" -eq "$total" ]; then
  echo "You can send any output anywhere. On to lesson 09!"
else
  echo "Fix the ❌ lines (run setup.sh to start over), then run the check again."
  exit 1
fi
