#!/usr/bin/env bash
# check.sh - checks your work for lesson 17.  Run it with:  ./check.sh
# (It uses if/[[ ]] from lesson 18 and functions from lesson 19. The comments explain each part.)

practice="$HOME/linux-practice/17"
pass=0
fail=0
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }                         # helper: report a pass
bad() { echo "  FAIL  $1"; echo "        hint: $2"; fail=$((fail + 1)); }  # helper: report a fail + hint

echo "Checking lesson 17..."

# 1. Did backup-file.sh make a backup of "my notes.txt"?
# compgen -G "pattern" prints the files that match a pattern; it fails if nothing matches.
if compgen -G "$practice/my notes.txt.bak-*" > /dev/null; then
  ok "a backup of 'my notes.txt' exists"
else
  bad "no backup of 'my notes.txt' found" "Run it, step 7: ./backup-file.sh ~/linux-practice/17/\"my notes.txt\""
fi

# 2-5. Does your hello-name.sh work?
script="$practice/hello-name.sh"
if [[ ! -x "$script" ]]; then                       # -x = exists and is executable
  bad "hello-name.sh is missing or not executable" "Run it, steps 9-10 (nano, then chmod +x)"
else
  ok "hello-name.sh exists and is executable"

  # $( ... | head -n 1) = run it and keep only the first line of what it prints
  out=$("$script" Priya | head -n 1)
  if [[ "$out" == "Hello, Priya!" ]]; then
    ok "hello-name.sh Priya  ->  $out"
  else
    bad "hello-name.sh Priya printed: '$out'" "the first line should be exactly: Hello, Priya!  (use \"\$1\")"
  fi

  out=$("$script" | head -n 1)                     # no arguments at all
  if [[ "$out" == "Hello, friend!" ]]; then
    ok "hello-name.sh (no name)  ->  $out"
  else
    bad "hello-name.sh with no name printed: '$out'" "use a default: name=\"\${1:-friend}\""
  fi

  out=$("$script" "Mary Ann" | head -n 1)          # one argument that contains a space
  if [[ "$out" == "Hello, Mary Ann!" ]]; then
    ok "hello-name.sh \"Mary Ann\"  ->  $out"
  else
    bad "hello-name.sh \"Mary Ann\" printed: '$out'" "put double quotes around variables: \"\$1\""
  fi

  out=$("$script" a b c | tail -n 1)              # tail -n 1 = keep only the last line
  if [[ "$out" == *3* ]]; then                     # *3* = "contains a 3 somewhere"
    ok "hello-name.sh counts its arguments ($out)"
  else
    bad "hello-name.sh a b c should report 3 arguments" "the last line should use \$#"
  fi
fi

echo ""
echo "Result: $pass passed, $fail failed."
[[ $fail -eq 0 ]] && echo "All done. Variables and arguments: mastered!"
[[ $fail -eq 0 ]]                                  # the script's exit code: 0 if no fails, 1 otherwise
