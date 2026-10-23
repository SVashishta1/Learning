#!/usr/bin/env bash
# setup.sh - lesson 02: builds your practice folder ~/linux-practice/02
# Safe: it only touches that one folder inside your home. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-1-first-steps/02-anatomy-of-a-command/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/02"      # the practice folder for this lesson
rm -rf "$practice"                      # delete an old copy, so you always start fresh
mkdir -p "$practice/photos"             # make the folder (and a photos folder inside it)
cd "$practice"                          # go there, so the files below land in it

# printf prints text exactly as written; \n means "new line"; > saves it into a file
printf 'Buy milk\nCall grandma\nLearn Linux\n' > notes.txt
printf 'apples\nbread\ncheese\n' > "shopping list.txt"        # a name WITH a space
printf 'You found the hidden treasure!\n' > .hidden-treasure.txt   # starts with . = hidden
printf 'theme=dark\nsound=off\n' > .settings                 # another hidden file
printf '# My practice folder\nFiles to explore with ls.\n' > README.md
printf 'pretend this is a photo of a cat\n' > photos/cat.jpg
printf 'pretend this is a photo of a dog\n' > photos/dog.jpg

# a bigger file: 2,000 numbered lines
i=1
while [ "$i" -le 2000 ]; do
  printf 'line %d: the quick brown fox jumps over the lazy dog\n' "$i"
  i=$((i + 1))
done > big-file.log

echo "Practice folder ready: $practice"
