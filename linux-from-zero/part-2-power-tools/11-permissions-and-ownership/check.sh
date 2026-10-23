#!/usr/bin/env bash
# check.sh - lesson 11: checks the permissions you set in ~/linux-practice/11
# Run it from the course folder with:
#   bash part-2-power-tools/11-permissions-and-ownership/check.sh
# It only LOOKS at the files. (Scripting is explained in Part 3.)

p="$HOME/linux-practice/11"
passed=0
total=0

ok()  { passed=$((passed + 1)); total=$((total + 1)); printf '✅ %s\n' "$1"; }
bad() { total=$((total + 1)); printf '❌ %s\n   hint: %s\n' "$1" "$2"; }

# mode FILE -> the permission number like 644 (GNU stat on Linux, BSD stat on a Mac)
mode() { stat -c %a "$1" 2>/dev/null || stat -f %Lp "$1" 2>/dev/null; }

# expect FILE NUMBER "what it means" "hint"
expect() {
  m="$(mode "$1")"
  if [ "$m" = "$2" ]; then
    ok "$(basename "$1") is $2 ($3)"
  else
    bad "$(basename "$1") is ${m:-missing}, should be $2 ($3)" "$4"
  fi
}

if [ ! -d "$p" ]; then
  echo "❌ $p does not exist. Run setup.sh first (see Run it, step 1)."
  exit 1
fi

echo "Checking permissions in ~/linux-practice/11 ..."
echo ""
echo "Run it:"
expect "$p/hello.sh" 755 "everyone may run it, only you may change it" "chmod u+x,go+x hello.sh   or   chmod 755 hello.sh"
expect "$p/diary.txt" 600 "only you may read and write" "chmod go-r diary.txt   or   chmod 600 diary.txt"
expect "$p/public-notes.txt" 644 "everyone may read, only you may write" "chmod 644 public-notes.txt"
expect "$p/private" 700 "only you may enter and list it" "chmod 700 private"
expect "$p/locked-folder" 755 "you can enter it again" "chmod 755 locked-folder"

echo ""
echo "Try this:"
if [ -f "$p/report.txt" ] && [ "$(mode "$p/report.txt")" = "600" ]; then
  ok "1. report.txt was born private (600)"
else
  bad "1. report.txt should exist with 600" "( umask 077; touch report.txt )   then   ls -l report.txt"
fi

all_x=yes
for t in backup deploy cleanup; do
  [ -x "$p/tools/$t.sh" ] || all_x=no
done
if [ "$all_x" = yes ]; then
  ok "2. all three tools/*.sh scripts are executable"
else
  bad "2. some tools/*.sh scripts are not executable" "chmod u+x tools/*.sh"
fi

if [ -g "$p/shared" ]; then
  ok "3. shared/ has the setgid bit (new files get the folder's group)"
else
  bad "3. shared/ has no setgid bit" "chmod g+s shared   then   ls -ld shared   (look for the s)"
fi

echo ""
echo "Result: $passed of $total checks passed."
if [ "$passed" -eq "$total" ]; then
  echo "You speak rwx fluently. On to lesson 12!"
else
  echo "Fix the ❌ lines (setup.sh starts you over), then run the check again."
  exit 1
fi
