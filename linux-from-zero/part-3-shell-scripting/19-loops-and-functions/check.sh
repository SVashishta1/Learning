#!/usr/bin/env bash
# check.sh - checks that you organized the practice downloads folder (lesson 19).
# Run it with:  ./check.sh

dl="$HOME/linux-practice/19/downloads"
pass=0
fail=0
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL  $1"; echo "        hint: $2"; fail=$((fail + 1)); }

echo "Checking lesson 19..."

if [[ ! -d "$dl" ]]; then
  echo "  FAIL  $dl is missing. Run: bash setup.sh"
  exit 1
fi

# 1. No loose files should be left directly inside downloads.
loose=$(find "$dl" -mindepth 1 -maxdepth 1 -type f | wc -l)   # -type f = files only
if (( loose == 0 )); then
  ok "no loose files left in downloads/"
else
  bad "$loose loose file(s) still in downloads/" "run ./organize.sh (after a --dry-run)"
fi

# 2. Every expected file must be in the right folder. Each entry is "folder/file name".
expected=(
  "images/photo1.JPG" "images/holiday photo.png" "images/cat.gif"
  "audio/song.mp3" "documents/report.pdf" "documents/notes.txt" "documents/README.md"
  "data/sales.csv" "data/config.json" "archives/backup.zip"
  "code/install.sh" "code/train.py" "models/tinyllama.Q4_K_M.gguf" "other/mystery.xyz"
)
missing=0
for item in "${expected[@]}"; do         # loop over every expected path
  if [[ ! -f "$dl/$item" ]]; then
    echo "        missing: $item"
    missing=$(( missing + 1 ))
  fi
done
if (( missing == 0 )); then
  ok "all ${#expected[@]} files are in the right folders"
else
  bad "$missing file(s) are not where expected" "run: bash setup.sh   then   ./organize.sh"
fi

echo ""
echo "Result: $pass passed, $fail failed."
(( fail == 0 )) && echo "All done. Your loops and functions work!"
(( fail == 0 ))
