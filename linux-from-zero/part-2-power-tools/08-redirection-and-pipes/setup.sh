#!/usr/bin/env bash
# setup.sh - lesson 08: builds files for practising redirection and pipes in ~/linux-practice/08
#   noisy.sh     a pretend AI server that prints normal messages AND error messages
#   animals.txt  a list with repeats (for sort and uniq)
#   server.log   a short log with INFO and ERROR lines
# Safe: it only touches that one folder inside your home. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-2-power-tools/08-redirection-and-pipes/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/08"
rm -rf "$practice"                      # delete an old copy, so you always start fresh
mkdir -p "$practice"
cd "$practice"

# noisy.sh: 3 normal lines go to "standard output", 2 error lines go to "standard error" (>&2)
cat > noisy.sh <<'SCRIPT'
#!/usr/bin/env bash
# A pretend AI server start-up. Normal messages go to stdout, problems go to stderr.
echo "OK: loaded 3 models"
echo "ERROR: model 'giant' not found" >&2
echo "OK: server ready on port 8000"
echo "ERROR: GPU not available, using CPU" >&2
echo "OK: answered 42 questions"
SCRIPT

printf '%s\n' zebra cat dog cat elephant ant dog cat bee fox > animals.txt

cat > server.log <<'LOG'
2026-03-14 10:00:01 INFO  started
2026-03-14 10:00:05 INFO  GET /health 200
2026-03-14 10:00:09 ERROR GET /chat 500 model timeout
2026-03-14 10:00:12 INFO  GET /chat 200
2026-03-14 10:00:15 INFO  GET /chat 200
2026-03-14 10:00:20 ERROR GET /chat 500 model timeout
2026-03-14 10:00:24 INFO  GET /health 200
2026-03-14 10:00:31 ERROR GET /upload 413 file too large
2026-03-14 10:00:40 INFO  GET /chat 200
2026-03-14 10:00:45 INFO  stopped
LOG

echo "Practice folder ready: $practice"
