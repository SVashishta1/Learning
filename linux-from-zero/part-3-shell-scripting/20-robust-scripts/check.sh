#!/usr/bin/env bash
# check.sh - checks your work for lesson 20.  Run it with:  ./check.sh

cd "$(dirname "$0")" || exit 1           # run from the lesson folder so ./backup.sh is found
backups="$HOME/linux-practice/20/backups"
pass=0
fail=0
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL  $1"; echo "        hint: $2"; fail=$((fail + 1)); }

echo "Checking lesson 20..."

# 1. -h prints help and exits 0
if ./backup.sh -h | grep -q "Usage:"; then
  ok "backup.sh -h shows the help"
else
  bad "backup.sh -h did not show help" "is backup.sh executable? (chmod +x backup.sh)"
fi

# 2. A wrong option must fail with exit code 2
./backup.sh -z > /dev/null 2>&1
code=$?
if (( code == 2 )); then
  ok "a wrong option (-z) exits with code 2"
else
  bad "a wrong option exited with $code, expected 2" "look at the *) branch of the getopts case"
fi

# 3. A missing source folder must fail (non-zero)
if ! ./backup.sh -s /no/such/folder -d "$HOME/linux-practice/20/tmp-check" > /dev/null 2>&1; then
  ok "a missing source folder makes backup.sh fail"
else
  bad "backup.sh succeeded with a missing source folder" "the [[ -d \"\$source_dir\" ]] || die line"
fi

# 4. You made real backups, and old ones were rotated away
shopt -s nullglob
files=("$backups"/project-*.tar.gz)
if (( ${#files[@]} >= 1 && ${#files[@]} <= 3 )); then
  ok "${#files[@]} backup(s) in $backups (3 or fewer kept)"
else
  bad "found ${#files[@]} backups, expected 1 to 3" "Run it, steps 7-8: run ./backup.sh 4 times"
fi

# 5. The newest backup really contains the project
newest="${files[-1]:-}"                  # [-1] = the last item = the newest name
if [[ -n "$newest" ]] && tar -tzf "$newest" | grep -q "project/notes.md"; then
  ok "the newest backup contains project/notes.md"
else
  bad "could not find project/notes.md in the newest backup" "run bash setup.sh, then ./backup.sh"
fi

echo ""
echo "Result: $pass passed, $fail failed."
(( fail == 0 )) && echo "All done. Your scripts are robust now!"
(( fail == 0 ))
