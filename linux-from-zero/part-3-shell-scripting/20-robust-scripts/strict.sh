#!/usr/bin/env bash
# strict.sh - shows what each part of "set -euo pipefail" catches, one at a time.
# Usage:  ./strict.sh error | unset | pipe
#   error = a command fails             -> set -e stops the script
#   unset = a variable name has a typo  -> set -u stops the script
#   pipe  = a pipeline hides a failure  -> set -o pipefail makes the failure count

set -euo pipefail          # the "strict mode" line. Put it at the top of every script you write.
# -e          = exit at once if a command fails (exit code not 0)
# -u          = treat using an unset (never created) variable as an error
# -o pipefail = a pipeline fails if ANY command in it fails, not only the last one

practice_dir="$HOME/linux-practice/20"
mode="${1:-}"              # ${1:-} = $1, or empty if missing (plain $1 would trip set -u!)

case "$mode" in
  error)
    echo "About to cd into a folder that does not exist..."
    cd "$practice_dir/no-such-folder"
    echo "You will never see this line."
    ;;
  unset)
    echo "About to use \$practice_dirr (typo)..."
    # shellcheck disable=SC2154            # (the typo is on purpose)
    echo "would run: rm -rf $practice_dirr/*"
    echo "You will never see this line."
    ;;
  pipe)
    echo "About to run: grep TODO missing-file | sort"
    grep "TODO" "$practice_dir/no-such-file.txt" | sort
    echo "You will never see this line."
    ;;
  *)
    echo "Usage: $0 error | unset | pipe" >&2
    exit 2
    ;;
esac
