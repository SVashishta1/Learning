#!/usr/bin/env bash
# quoting-demo.sh - why you should ALWAYS put "double quotes" around variables.
# Run it after setup.sh:  ./quoting-demo.sh

cd ~/linux-practice/17 || exit 1   # go to the practice folder; || exit 1 = stop if that fails (lesson 18)

file="my notes.txt"                # ONE file whose name contains a space

echo "--- Without quotes: cat \$file ---"
# shellcheck disable=SC2086        # (note for shellcheck: this mistake is on purpose, to show it)
cat $file                          # bash splits the value at the space: cat "my" "notes.txt" -> two wrong names

echo ""
echo "--- With quotes: cat \"\$file\" ---"
cat "$file"                        # the quotes keep it as one name: cat "my notes.txt" -> works
