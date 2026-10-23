#!/usr/bin/env bash
# loops.sh - the four kinds of loops you will use 99% of the time.
# Run it after setup.sh:  ./loops.sh

echo "== 1. for: go through a list of words =="
for fruit in apple banana cherry; do     # each time round, $fruit holds the next word
  echo "I like $fruit"
done                                     # done = end of the loop body

echo ""
echo "== 2. for: go through files that match a pattern =="
for file in ~/linux-practice/19/downloads/*.txt; do   # *.txt = every name ending in .txt
  [[ -e "$file" ]] || continue           # if nothing matched, skip (the pattern stays as literal text)
  echo "Found a text file: $(basename "$file")"       # basename = the name without the folders
done

echo ""
echo "== 3. for: count with numbers =="
for i in {1..5}; do                      # {1..5} = 1 2 3 4 5 (a "brace expansion")
  echo -n "$i "                          # -n = do not start a new line after this echo
done
echo ""                                  # now finish the line
for (( i = 10; i > 0; i -= 3 )); do      # C-style: start at 10; keep going while i > 0; subtract 3 each time
  echo -n "$i "
done
echo ""

echo ""
echo "== 4. while: repeat as long as a test succeeds =="
count=1
while (( count <= 3 )); do               # keep going while count is 3 or less
  echo "Lap $count"
  count=$(( count + 1 ))                 # IMPORTANT: change something, or the loop never ends
done

echo ""
echo "== 5. while read: go through a file line by line =="
# IFS= keeps spaces at the start of lines, -r keeps backslashes. < file feeds the file into the loop.
while IFS= read -r server; do
  [[ -z "$server" || "$server" == \#* ]] && continue   # skip empty lines and lines starting with #
  echo "Would check server: $server"
done < ~/linux-practice/19/servers.txt

echo ""
echo "== 6. until: repeat until a test succeeds (the opposite of while) =="
tries=0
until (( tries == 3 )); do
  tries=$(( tries + 1 ))
  echo "Try number $tries"
done

echo ""
echo "== 7. break and continue =="
for n in 1 2 3 4 5 6 7 8 9; do
  if (( n % 2 == 0 )); then continue; fi # continue = skip the rest of THIS round, go to the next
  if (( n > 7 )); then break; fi         # break = leave the loop completely
  echo -n "$n "
done
echo ""
