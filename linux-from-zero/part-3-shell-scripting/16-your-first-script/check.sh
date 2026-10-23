#!/usr/bin/env bash
# check.sh - checks your work for lesson 16.
# Run it from the lesson folder with:  ./check.sh
# (Do not worry about how every line works yet. You will learn
#  if, functions and $((...)) in lessons 17-19. Comments explain each part.)

practice="$HOME/linux-practice/16"   # the practice folder from setup.sh
pass=0                                # counter: how many checks passed
fail=0                                # counter: how many checks failed

# ok and bad are small helper "functions" (named mini-scripts, lesson 19).
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }                       # print PASS and add 1 to pass
bad() { echo "  FAIL  $1"; echo "        hint: $2"; fail=$((fail + 1)); } # print FAIL, a hint, add 1 to fail

echo "Checking lesson 16..."

# 1-4. Did you write your own script, with a shebang, executable, and working?
mine="$practice/my-first.sh"
if [[ ! -f "$mine" ]]; then                      # -f = "is a regular file that exists"; ! = NOT
  bad "my-first.sh is missing" "follow Run it, steps 7-9: nano ~/linux-practice/16/my-first.sh"
else
  ok "my-first.sh exists"

  if [[ "$(head -c 2 "$mine")" == "#!" ]]; then  # head -c 2 = the first 2 characters of the file
    ok "my-first.sh starts with #!"
  else
    bad "my-first.sh has no shebang on line 1" "make line 1 exactly: #!/usr/bin/env bash"
  fi

  if [[ -x "$mine" ]]; then                      # -x = "I am allowed to execute it"
    ok "my-first.sh is executable"
  else
    bad "my-first.sh is not executable" "run: chmod +x ~/linux-practice/16/my-first.sh"
  fi

  if [[ -x "$mine" ]] && "$mine" > /dev/null 2>&1; then   # run it, hide its output, did it succeed?
    ok "my-first.sh runs successfully"
  else
    bad "my-first.sh does not run cleanly" "run it yourself (~/linux-practice/16/my-first.sh) and read the error"
  fi
fi

# 5. Did you fix broken.sh?
broken="$practice/broken.sh"
if [[ -x "$broken" ]] && ! grep -q $'\r' "$broken" && "$broken" > /dev/null 2>&1; then
  # $'\r' is bash's way to write the invisible carriage-return character; grep -q searches silently
  ok "broken.sh is fixed (executable, Unix line endings, runs)"
else
  bad "broken.sh is still broken" "follow Run it, steps 13-15 (chmod +x, then sed -i 's/\\r\$//')"
fi

# 6. Can you run morning-report from anywhere?
if command -v morning-report > /dev/null 2>&1; then   # command -v finds a command in your PATH
  ok "morning-report is on your PATH"
else
  bad "morning-report is not on your PATH" "follow Run it, steps 10-12 (copy to ~/bin, add ~/bin to PATH)"
fi

echo ""
echo "Result: $pass passed, $fail failed."
if [[ $fail -eq 0 ]]; then                      # -eq = "numbers are equal"
  echo "All done. You can write and run scripts!"
else
  exit 1                                        # exit code 1 = "something failed" (lesson 18)
fi
