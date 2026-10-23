#!/usr/bin/env bash
# setup.sh - lesson 13: builds small practice programs in ~/linux-practice/13
#   counter.sh         counts up once a second (for background jobs and nohup)
#   polite-server.sh   a pretend server that shuts down cleanly when asked (signal TERM)
#   stubborn.sh        ignores polite stop requests; only kill -9 stops it
#   hog.sh             keeps one CPU core busy for 60 seconds (to spot it in top)
# Safe: it only touches ~/linux-practice/13. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-2-power-tools/13-processes-and-jobs/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/13"
rm -rf "$practice"                      # delete an old copy, so you always start fresh
mkdir -p "$practice"
cd "$practice"

cat > counter.sh <<'SCRIPT'
#!/usr/bin/env bash
# Prints "count 1", "count 2", ... once a second. Stops by itself after 300 seconds.
n=1
while [ "$n" -le 300 ]; do
  echo "count $n"
  n=$((n + 1))
  sleep 1
done
SCRIPT

cat > polite-server.sh <<'SCRIPT'
#!/usr/bin/env bash
# A pretend server. When it receives the TERM signal (plain "kill"), it cleans up and exits.
# "trap COMMANDS SIGNAL" means: when SIGNAL arrives, run COMMANDS.
trap 'echo "polite-server: got TERM, saving work and shutting down cleanly"; exit 0' TERM
echo "polite-server: running with PID $$ (stop me with: kill $$)"
while true; do
  sleep 1
done
SCRIPT

cat > stubborn.sh <<'SCRIPT'
#!/usr/bin/env bash
# Ignores Ctrl+C (INT) and plain kill (TERM). Only "kill -9" (KILL) can stop it.
trap 'echo "stubborn: ha! I ignore TERM"' TERM
trap 'echo "stubborn: ha! I ignore Ctrl+C"' INT
echo "stubborn: running with PID $$"
while true; do
  sleep 1
done
SCRIPT

cat > hog.sh <<'SCRIPT'
#!/usr/bin/env bash
# Keeps one CPU core busy for 60 seconds, then stops by itself.
end=$((SECONDS + 60))
while [ "$SECONDS" -lt "$end" ]; do
  :   # ":" is a command that does nothing, as fast as it can
done
SCRIPT

chmod +x counter.sh polite-server.sh stubborn.sh hog.sh
echo "Practice folder ready: $practice"
