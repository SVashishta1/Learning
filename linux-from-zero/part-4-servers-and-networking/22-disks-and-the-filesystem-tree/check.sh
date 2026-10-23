#!/usr/bin/env bash
# check.sh - did you find and delete the space hog? (lesson 22)  Run it with:  ./check.sh

practice="$HOME/linux-practice/22"
pass=0
fail=0
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL  $1"; echo "        hint: $2"; fail=$((fail + 1)); }

echo "Checking lesson 22..."
[[ -d "$practice" ]] || { echo "  FAIL  $practice is missing: run bash setup.sh"; exit 1; }

if [[ ! -e "$practice/.cache/models/old-model.gguf" ]]; then
  ok "the 60 MB space hog is gone"
else
  bad "the space hog is still there" "du -ah ~/linux-practice/22 | sort -rh | head (the -a also shows files, even hidden ones)"
fi

if [[ -f "$practice/projects/notes.txt" ]]; then
  ok "projects/notes.txt is still there (you only deleted the right thing)"
else
  bad "projects/notes.txt was deleted" "run bash setup.sh to start again, and only delete the biggest item"
fi

# du -sm = summary size in megabytes; cut -f1 = only the number
size=$(du -sm "$practice" | cut -f1)
if (( size < 50 )); then
  ok "the practice folder is now $size MB (was about 95 MB)"
else
  bad "the practice folder is still $size MB" "find the biggest item with du"
fi

if [[ -d "$practice/mnt" ]] && mountpoint -q "$practice/mnt"; then   # mountpoint -q = is something mounted here?
  bad "the fake disk is still mounted on $practice/mnt" "sudo umount ~/linux-practice/22/mnt (Run it, step 15)"
else
  ok "no fake disk left mounted"
fi

echo ""
echo "Result: $pass passed, $fail failed."
(( fail == 0 )) && echo "All done. You can hunt down disk space like a sysadmin."
(( fail == 0 ))
