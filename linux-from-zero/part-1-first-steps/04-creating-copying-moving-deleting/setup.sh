#!/usr/bin/env bash
# setup.sh - lesson 04: builds a messy "downloads" folder in ~/linux-practice/04 for you to tidy up
# Safe: it only touches that one folder inside your home. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-1-first-steps/04-creating-copying-moving-deleting/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/04"
rm -rf "$practice"                      # delete an old copy, so you always start fresh
mkdir -p "$practice/downloads/old-stuff"
cd "$practice/downloads"

# Pretend files: the content is just a short line of text, the NAME is what matters.
for name in holiday-01.jpg holiday-02.jpg holiday-03.jpg cat.png \
            invoice-march.pdf invoice-april.pdf cv.docx \
            song1.mp3 song2.mp3 temp-1.tmp temp-2.tmp temp-3.tmp; do
  printf 'pretend content of %s\n' "$name" > "$name"
done
printf 'pretend content of my essay.docx\n' > "my essay.docx"   # a name with a space
printf 'Remember: back up your files!\n' > notes.txt
printf 'junk\n' > old-stuff/junk1.txt
printf 'more junk\n' > old-stuff/junk2.txt

echo "Practice folder ready: $practice"
echo "Messy files are in: $practice/downloads"
