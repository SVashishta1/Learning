#!/usr/bin/env bash
# check.sh - lesson 04: checks that you tidied the downloads folder (Run it) and did the Try this exercises.
# Run it from the course folder with:
#   bash part-1-first-steps/04-creating-copying-moving-deleting/check.sh
# It only LOOKS at ~/linux-practice/04. It never changes anything.
# (You don't need to understand this file yet. Part 3 teaches scripting.)

p="$HOME/linux-practice/04"
passed=0
total=0

ok()  { passed=$((passed + 1)); total=$((total + 1)); printf '✅ %s\n' "$1"; }
bad() { total=$((total + 1)); printf '❌ %s\n   hint: %s\n' "$1" "$2"; }

# all_files_exist file1 file2 ... -> succeeds only if every file exists
all_files_exist() {
  for f in "$@"; do
    [ -f "$f" ] || return 1
  done
}

# any_tmp_left -> succeeds if any *.tmp file is still in downloads
any_tmp_left() {
  for f in "$p"/downloads/*.tmp; do
    [ -e "$f" ] && return 0
  done
  return 1
}

if [ ! -d "$p" ]; then
  echo "❌ $p does not exist. Run setup.sh first (see Run it, step 2)."
  exit 1
fi

echo "Checking ~/linux-practice/04 ..."
echo ""
echo "Run it:"

if [ -d "$p/organized/pictures" ] && [ -d "$p/organized/documents" ] && [ -d "$p/organized/music" ]; then
  ok "organized/ has pictures, documents and music folders"
else
  bad "organized/pictures, documents or music is missing" "mkdir -p organized/{pictures,documents,music}  (step 5)"
fi

if [ -f "$p/organized/README.txt" ]; then
  ok "organized/README.txt exists"
else
  bad "organized/README.txt is missing" "touch organized/README.txt  (step 6)"
fi

if all_files_exist "$p"/organized/pictures/holiday-0{1,2,3}.jpg "$p/organized/pictures/cat.png"; then
  ok "the 3 holiday photos and cat.png are in organized/pictures"
else
  bad "some pictures are not in organized/pictures" "mv downloads/*.jpg downloads/*.png organized/pictures/  (step 8)"
fi

if all_files_exist "$p/organized/documents/invoice-march.pdf" "$p/organized/documents/invoice-april.pdf" \
   && { [ -f "$p/organized/documents/my essay.docx" ] || [ -f "$p/organized/documents/my-essay.docx" ]; }; then
  ok "the invoices and the essay are in organized/documents"
else
  bad "some documents are not in organized/documents" "mv downloads/*.pdf downloads/*.docx organized/documents/  (step 9)"
fi

if [ -f "$p/organized/documents/cv-2026.docx" ] && [ ! -e "$p/organized/documents/cv.docx" ]; then
  ok "cv.docx was renamed to cv-2026.docx"
else
  bad "organized/documents/cv-2026.docx not found (or cv.docx still there)" "mv organized/documents/cv.docx organized/documents/cv-2026.docx  (step 10)"
fi

if all_files_exist "$p/organized/music/song1.mp3" "$p/organized/music/song2.mp3"; then
  ok "both songs are in organized/music"
else
  bad "songs are not in organized/music" "mv downloads/*.mp3 organized/music/  (step 11)"
fi

if [ -f "$p/downloads/notes.txt" ] && [ -f "$p/organized/documents/notes.txt" ]; then
  ok "notes.txt was COPIED (it's in downloads AND organized/documents)"
else
  bad "notes.txt should be in both downloads and organized/documents" "cp downloads/notes.txt organized/documents/  (step 12)"
fi

if any_tmp_left; then
  bad "temp .tmp files are still in downloads" "rm downloads/temp-?.tmp  (step 13)"
else
  ok "the .tmp files are deleted"
fi

if [ ! -e "$p/downloads/old-stuff" ]; then
  ok "downloads/old-stuff is deleted"
else
  bad "downloads/old-stuff still exists" "rm -r downloads/old-stuff  (step 15)"
fi

if [ -f "$p/organized-backup/pictures/cat.png" ] && [ -f "$p/organized-backup/music/song1.mp3" ]; then
  ok "organized-backup is a full copy of organized"
else
  bad "organized-backup is missing or incomplete" "cp -r organized organized-backup  (step 16)"
fi

echo ""
echo "Try this:"

if [ -d "$p/projects/2026/jan" ] && [ -d "$p/projects/2026/feb" ] && [ -d "$p/projects/2026/mar" ]; then
  ok "1. projects/2026/jan, feb and mar exist"
else
  bad "1. projects/2026/{jan,feb,mar} not found" "mkdir -p projects/2026/{jan,feb,mar}"
fi

if all_files_exist "$p"/phone-upload/holiday-0{1,2,3}.jpg && [ -f "$p/organized/pictures/holiday-01.jpg" ]; then
  ok "2. the holiday photos were copied to phone-upload (originals kept)"
else
  bad "2. phone-upload/ should hold copies of the 3 holiday photos" "mkdir phone-upload && cp organized/pictures/holiday-*.jpg phone-upload/"
fi

if [ -f "$p/organized/documents/my-essay.docx" ] && [ ! -e "$p/organized/documents/my essay.docx" ]; then
  ok "3. 'my essay.docx' was renamed to my-essay.docx"
else
  bad "3. organized/documents/my-essay.docx not found" "mv \"organized/documents/my essay.docx\" organized/documents/my-essay.docx"
fi

echo ""
echo "Result: $passed of $total checks passed."
if [ "$passed" -eq "$total" ]; then
  echo "Tidy! You can create, copy, move and delete like a pro."
else
  echo "Fix the ❌ lines (each hint shows a command), then run the check again."
  exit 1
fi
