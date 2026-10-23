#!/usr/bin/env bash
# check-file.sh - tells you what kind of thing a path is, using if / elif / else.
# Usage:  ./check-file.sh PATH
# Exit codes: 0 = it exists, 1 = it does not exist, 2 = you forgot the PATH

# If no argument was given ($# is 0), explain how to use the script and stop with code 2.
if [[ $# -eq 0 ]]; then                    # -eq = numbers are equal
  echo "Usage: $0 PATH" >&2                # >&2 = print to the ERROR stream (stderr), not normal output
  exit 2                                   # exit = stop the script now, with this exit code
fi

target="$1"                                # the path to check, in quotes because it may contain spaces

if [[ ! -e "$target" ]]; then              # -e = exists; ! = NOT, so "if it does NOT exist"
  echo "'$target' does not exist."
  exit 1
elif [[ -d "$target" ]]; then              # elif = "else, if ...": -d = is a directory (folder)
  count=$(find "$target" -mindepth 1 -maxdepth 1 | wc -l)   # count the items directly inside it
  echo "'$target' is a folder with $count items."
elif [[ -f "$target" ]]; then              # -f = is a regular file
  echo "'$target' is a file."
  if [[ -s "$target" ]]; then              # -s = has a size greater than zero
    echo "  It is $(stat -c %s "$target") bytes."   # stat -c %s = print only the size in bytes
  else
    echo "  It is EMPTY."
  fi
  # Three quick yes/no checks in a row, using && (AND) and || (OR):
  [[ -r "$target" ]] && echo "  You can read it."    || echo "  You can NOT read it."
  [[ -w "$target" ]] && echo "  You can change it."  || echo "  You can NOT change it."
  [[ -x "$target" ]] && echo "  You can run it."     || echo "  You can NOT run it."
else
  echo "'$target' exists but is something special (a device, socket or pipe)."
fi

exit 0                                     # we got here, so it exists: success
