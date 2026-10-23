#!/usr/bin/env bash
# check.sh - lesson 07: checks the edits you made with nano and vim.
# Run it from the course folder with:
#   bash part-1-first-steps/07-editing-files-with-nano-and-vim/check.sh
# It only READS your files in ~/linux-practice/07. It never changes them.
# (You don't need to understand this file yet. grep comes in lesson 09, scripting in Part 3.)

p="$HOME/linux-practice/07"
list="$p/shopping-list.txt"
conf="$p/app.conf"
passed=0
total=0

ok()  { passed=$((passed + 1)); total=$((total + 1)); printf '✅ %s\n' "$1"; }
bad() { total=$((total + 1)); printf '❌ %s\n   hint: %s\n' "$1" "$2"; }

# has_line FILE "exact line" -> succeeds if FILE contains exactly that whole line
has_line() { grep -qxF -- "$2" "$1" 2>/dev/null; }
# has_text FILE "text" -> succeeds if FILE contains the text anywhere
has_text() { grep -qF -- "$2" "$1" 2>/dev/null; }

if [ ! -f "$list" ] || [ ! -f "$conf" ]; then
  echo "❌ The practice files are missing. Run setup.sh first (see Run it, step 2)."
  exit 1
fi

echo "Checking your edits in ~/linux-practice/07 ..."
echo ""
echo "nano (shopping-list.txt):"

if has_line "$list" "- apples" && ! has_text "$list" "aples"; then
  ok "'aples' is fixed to 'apples'"
else
  bad "the line '- apples' is not there yet" "nano shopping-list.txt, Ctrl+W aples Enter, then fix it (Run it, step 5)"
fi

if has_line "$list" "- bread" && ! has_line "$list" "- bred"; then
  ok "'bred' is fixed to 'bread'"
else
  bad "the line '- bread' is not there yet" "Run it, step 6"
fi

if ! has_text "$list" "chocolate"; then
  ok "the chocolate cake line is gone"
else
  bad "the chocolate cake line is still there" "put the cursor on it and press Ctrl+K (Run it, step 7)"
fi

if has_line "$list" "- bananas"; then
  ok "'- bananas' was added"
else
  bad "no line '- bananas'" "Alt+/ jumps to the end, then type it (Run it, step 8). Save with Ctrl+O, Enter"
fi

echo ""
echo "vim (app.conf):"

if has_line "$conf" "port = 8080"; then
  ok "port is 8080"
else
  bad "port is not 8080" "vim app.conf, /8000 Enter, cw8080 Esc (Run it, step 13)"
fi

if has_line "$conf" "debug = false"; then
  ok "debug is false"
else
  bad "debug is not false" "/true Enter, cwfalse Esc (Run it, step 14)"
fi

if ! has_text "$conf" "delete_me"; then
  ok "the delete_me line is gone"
else
  bad "the delete_me line is still there" "/delete_me Enter, dd (Run it, step 15)"
fi

if has_line "$conf" "workers = 4"; then
  ok "'workers = 4' was added"
else
  bad "no line 'workers = 4'" "G, o, type it, Esc, :wq Enter (Run it, steps 16-17)"
fi

echo ""
echo "Try this:"

if [ -f "$p/haiku.txt" ] && [ "$(grep -c . "$p/haiku.txt")" -eq 3 ]; then
  ok "1. haiku.txt has 3 lines"
else
  bad "1. haiku.txt with exactly 3 (non-empty) lines not found" "nano haiku.txt, type 3 lines, Ctrl+O Enter, Ctrl+X"
fi

if has_line "$conf" "model = large"; then
  ok "2. model is large"
else
  bad "2. model is not large" "in vim: :%s/small/large/ Enter, then :wq Enter"
fi

if [ "$(tail -n 1 "$conf")" = "# reviewed" ]; then
  ok "3. the last line of app.conf is '# reviewed'"
else
  bad "3. the last line of app.conf is not '# reviewed'" "in vim: G (go to last line), o (open a line below), type it, Esc, :wq"
fi

echo ""
echo "Result: $passed of $total checks passed."
if [ "$passed" -eq "$total" ]; then
  echo "You can edit files in any terminal, even over SSH. Part 1 done!"
else
  echo "Fix the ❌ lines, then run the check again. (setup.sh starts you over.)"
  exit 1
fi
