#!/usr/bin/env bash
# setup.sh - lesson 10: builds data files to slice and summarise in ~/linux-practice/10
#   access.log         200 lines of web server log (who asked for what, and how it went)
#   sales.csv          a sales table (comma-separated)
#   names.txt          messy names (mixed case, extra spaces, repeats)
#   app.conf.template  a settings file with {{PLACEHOLDERS}} to fill in with sed
# Safe: it only touches ~/linux-practice/10. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-2-power-tools/10-text-processing-cut-sort-uniq-sed-awk/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/10"
rm -rf "$practice"                      # delete an old copy, so you always start fresh
mkdir -p "$practice"
cd "$practice"

# access.log in the classic web-server "combined" style, plus the response time in ms at the end.
# awk is used here as a tiny program to generate the same 200 lines for everyone.
awk 'BEGIN {
  split("203.0.113.7 198.51.100.23 192.0.2.44 203.0.113.99 198.51.100.5", ip, " ")
  split("/api/chat /api/embed /health /login /static/logo.png /api/chat /api/chat /admin", path, " ")
  for (i = 1; i <= 200; i++) {
    k = (i * 7 + int(i / 4)) % 20               # pick an IP, some more often than others
    if (k < 7) w = 1; else if (k < 12) w = 2; else if (k < 16) w = 3; else if (k < 19) w = 4; else w = 5
    p = path[(i * 5) % 8 + 1]
    status = 200
    if (p == "/admin" || i % 11 == 0) status = 404
    if (i % 17 == 0) status = 500
    method = (p == "/login" || p == "/api/embed") ? "POST" : "GET"
    t = 36000 + i * 13                          # seconds since midnight, from 10:00:13
    printf "%s - - [14/Mar/2026:%02d:%02d:%02d +0000] \"%s %s HTTP/1.1\" %d %d %d\n", \
      ip[w], int(t / 3600), int(t % 3600 / 60), t % 60, method, p, status, (i * 37) % 2000 + 100, (i * 53) % 900 + 20
  }
}' > access.log

cat > sales.csv <<'CSV'
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
CSV

printf '%s\n' "Alice" "bob" "  Carol" "ALICE" "dave  " "Bob" "alice" "Eve" > names.txt

cat > app.conf.template <<'TXT'
# Settings for the chat API
port = {{PORT}}
model = {{MODEL}}
fallback_model = {{MODEL}}
debug = false
TXT

echo "Practice folder ready: $practice"
