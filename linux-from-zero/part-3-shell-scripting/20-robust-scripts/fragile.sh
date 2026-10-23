#!/usr/bin/env bash
# fragile.sh - a script WITHOUT safety settings. Watch it carry on after every mistake.
# It only PRINTS the dangerous command, it never runs it. Run it with:  ./fragile.sh

practice_dir="$HOME/linux-practice/20"

echo "Step 1: go into a folder that does not exist"
# shellcheck disable=SC2164                  # (shellcheck WOULD warn here: "use cd ... || exit". Mistake on purpose.)
cd "$practice_dir/no-such-folder"           # fails... but bash just carries on in the WRONG folder
echo "        still running, now in: $(pwd)"

echo "Step 2: use a variable with a typo (practice_dirr instead of practice_dir)"
# shellcheck disable=SC2154                  # (note for shellcheck: the typo is on purpose)
echo "        would run: rm -rf $practice_dirr/*"   # the empty typo turns this into rm -rf /* !!!

echo "Step 3: a pipeline whose first command fails"
grep "TODO" "$practice_dir/no-such-file.txt" | sort
echo "        exit code of the pipeline: $? (looks like success!)"

echo "Step 4: the script reaches the end and reports success"
echo "        All good! (it is not...)"
