#!/usr/bin/env bash
# setup.sh - creates the practice folder for lesson 17 (~/linux-practice/17). Safe to run again.
# Run it with:  bash setup.sh

practice="$HOME/linux-practice/17"         # where the practice files go
mkdir -p "$practice"                       # create it (no error if it already exists)

# Files whose names contain spaces: perfect for practising quotes.
echo "Buy milk. Call grandma. Learn bash variables." > "$practice/my notes.txt"
printf 'eggs\nbread\nmangoes\n' > "$practice/shopping list.txt"   # \n = new line, so 3 lines

echo "Practice folder ready: $practice"
ls -l "$practice"
