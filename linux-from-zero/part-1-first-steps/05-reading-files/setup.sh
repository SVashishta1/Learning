#!/usr/bin/env bash
# setup.sh - lesson 05: builds files to read in ~/linux-practice/05
#   app.log     a server log (120 lines)        poem.txt   a short poem
#   sales.csv   a small table (comma separated) story.txt  a long story (300 lines)
#   mystery1/2/3  files without a helpful name   grow.sh    writes to growing.log every second
# Safe: it only touches that one folder inside your home. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-1-first-steps/05-reading-files/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/05"
rm -rf "$practice"                      # delete an old copy, so you always start fresh
mkdir -p "$practice"
cd "$practice"

# --- app.log: one line every 30 seconds from 09:00:00, the same for everyone ---
i=0
while [ "$i" -lt 120 ]; do
  secs=$((i * 30))                                       # seconds since 09:00:00
  time="$(printf '%02d:%02d:%02d' $((9 + secs / 3600)) $((secs % 3600 / 60)) $((secs % 60)))"
  if [ $((i % 10)) -eq 9 ]; then
    printf '2026-03-14 %s ERROR payment-service: card declined for order %d\n' "$time" $((1000 + i))
  elif [ $((i % 7)) -eq 6 ]; then
    printf '2026-03-14 %s WARN  api: slow response (%d ms) on /search\n' "$time" $((800 + i * 3))
  else
    printf '2026-03-14 %s INFO  api: GET /products/%d 200\n' "$time" $((i % 13 + 1))
  fi
  i=$((i + 1))
done > app.log

# --- poem.txt ---
cat > poem.txt <<'EOF'
The terminal is quiet, the cursor blinks slow,
it waits for a word, for a place it should go.
I type in a command and I press on the key,
and the computer, politely, replies back to me.
A folder, a file, a log full of lines,
each one has a story, a time and some signs.
So read them with care, from the head to the tail,
and the server will tell you the end of the tale.
EOF

# --- sales.csv: CSV = "comma-separated values", a table in plain text ---
cat > sales.csv <<'EOF'
date,region,product,units,price
2026-03-01,north,laptop,3,999
2026-03-01,south,phone,10,499
2026-03-02,east,tablet,4,329
2026-03-02,north,phone,7,499
2026-03-03,west,laptop,2,999
2026-03-03,south,headphones,15,79
2026-03-04,east,phone,6,499
2026-03-04,west,tablet,5,329
2026-03-05,north,headphones,12,79
2026-03-05,south,laptop,1,999
2026-03-06,east,laptop,4,999
2026-03-06,west,phone,9,499
EOF

# --- story.txt: 300 lines, with one special word hidden on line 217 ---
i=1
while [ "$i" -le 300 ]; do
  if [ "$i" -eq 217 ]; then
    printf 'And there, behind the server rack, slept a tiny dragon.\n'
  else
    printf 'The knight walked on through the long, long data centre.\n'
  fi
  i=$((i + 1))
done > story.txt

# --- mystery files: their names don't say what they are ---
# mystery1: the first bytes of a PNG picture (\211 etc. are byte values written in octal)
printf '\211PNG\r\n\032\n\000\000\000\rIHDR\000\000\000\020\000\000\000\020\010\006\000\000\000\037\363\377a' > mystery1
# mystery2: a compressed (gzip) text file
printf 'This text was hidden inside a compressed file.\n' | gzip -n > mystery2
# mystery3: plain text
printf 'Just plain text, nothing scary.\n' > mystery3

# --- grow.sh: adds a line to growing.log every second, 30 times (for tail -f) ---
cat > grow.sh <<'EOF'
#!/usr/bin/env bash
# Writes one new line to growing.log every second, 30 times, then stops.
# Run it with:  bash grow.sh &      (the & lets it run in the background, lesson 13)
cd "$(dirname "$0")"
n=1
while [ "$n" -le 30 ]; do
  echo "$(date +%H:%M:%S) visitor number $n arrived" >> growing.log
  n=$((n + 1))
  sleep 1
done
EOF

echo "Practice folder ready: $practice"
