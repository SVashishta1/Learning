#!/usr/bin/env bash
# setup.sh - lesson 14: builds practice files in ~/linux-practice/14
#   bin/hello-tool   a tiny program you'll make findable through PATH
#   show-env.sh      prints a variable, to prove which variables reach child programs
#   my file.txt      a file with a space in its name (for quoting practice)
# Safe: it only touches ~/linux-practice/14. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-2-power-tools/14-environment-variables-and-quoting/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/14"
rm -rf "$practice"                      # delete an old copy, so you always start fresh
mkdir -p "$practice/bin"
cd "$practice"

cat > bin/hello-tool <<'SCRIPT'
#!/usr/bin/env bash
# A tiny "installed program". It greets GREETING_NAME if that variable is set.
echo "hello-tool: I was found through your PATH!"
echo "Hello, ${GREETING_NAME:-stranger}."
SCRIPT
chmod +x bin/hello-tool

cat > show-env.sh <<'SCRIPT'
#!/usr/bin/env bash
# A child program: it can only see variables that were EXPORTED by the shell that started it.
echo "show-env.sh sees FAVORITE_COLOR='${FAVORITE_COLOR}'"
SCRIPT

printf 'This file has a space in its name.\n' > "my file.txt"
printf 'Another normal file.\n' > notes.txt

echo "Practice folder ready: $practice"
