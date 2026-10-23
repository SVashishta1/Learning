#!/usr/bin/env bash
# backup-file.sh - makes a time-stamped copy of a file, so you can undo mistakes.
# Usage:  ./backup-file.sh FILE
# Example: ./backup-file.sh "my notes.txt"  ->  my notes.txt.bak-20261022-091500

# ${1:?message} means: "use $1; if it is missing or empty, print message and STOP the script".
file="${1:?Usage: ./backup-file.sh FILE   (give me the file to back up)}"

stamp=$(date +%Y%m%d-%H%M%S)     # e.g. 20261022-091500 (year month day - hour minute second)
copy="$file.bak-$stamp"           # the new name: the old name + .bak- + the stamp

cp -- "$file" "$copy"             # -- = "no more options after this", so a file named -x is still a file
                                  # the quotes keep names with spaces in one piece
echo "Backed up '$file' to '$copy'"
