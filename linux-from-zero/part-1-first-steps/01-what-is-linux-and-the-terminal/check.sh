#!/usr/bin/env bash
# check.sh - lesson 01: is your practice computer ready for this course?
# Run it from the course folder with:
#   bash part-1-first-steps/01-what-is-linux-and-the-terminal/check.sh
# It only LOOKS at your computer. The one thing it creates is the empty
# practice folder ~/linux-practice that later lessons use.
# (You don't need to understand this file yet. Part 3 teaches scripting.)

passed=0   # how many checks passed
total=0    # how many checks ran

# ok "message"          -> prints a green tick and counts a pass
# bad "message" "hint"  -> prints a red cross and a hint on how to fix it
ok()  { passed=$((passed + 1)); total=$((total + 1)); printf '✅ %s\n' "$1"; }
bad() { total=$((total + 1)); printf '❌ %s\n   hint: %s\n' "$1" "$2"; }

echo "Checking your practice computer..."
echo ""

# 1. Which operating system? uname -s prints "Linux" on Linux/WSL and "Darwin" on a Mac.
os="$(uname -s)"
if [ "$os" = "Linux" ]; then
  ok "You are on Linux ($(uname -r))"
elif [ "$os" = "Darwin" ]; then
  ok "You are on macOS. Look out for the 'On a Mac' notes in each lesson."
else
  bad "Unknown system: $os" "use WSL2 Ubuntu, a Mac, Linux, or the Docker ubuntu:24.04 option from lesson 01"
fi

# 2. Are you a normal user? Root (user number 0) can break things, and hides permission lessons.
if [ "$(id -u)" -ne 0 ]; then
  ok "You are a normal user: $(whoami)"
else
  bad "You are logged in as root (the all-powerful admin)" "in Docker, run: su - ubuntu   (lesson 01, Option D, step 6)"
fi

# 3. Can you write in your home folder? Make the practice folder used by later lessons.
if mkdir -p "$HOME/linux-practice" 2>/dev/null && [ -w "$HOME/linux-practice" ]; then
  ok "Practice folder ready: $HOME/linux-practice"
else
  bad "Cannot create $HOME/linux-practice" "check that HOME is your own folder: echo \$HOME"
fi

# 4. Are the tools this course uses installed? command -v prints where a command lives (or nothing).
missing=""
for tool in ls cat grep nano vim less man git curl tree file; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    missing="$missing $tool"
  fi
done
if [ -z "$missing" ]; then
  ok "All course tools are installed (ls cat grep nano vim less man git curl tree file)"
else
  bad "Missing tools:$missing" "Ubuntu/WSL/Docker: sudo apt update && sudo apt install -y$missing   Mac: see lesson 01, Option B"
fi

# 5. GNU tools (Linux) or BSD tools (Mac)? GNU ls understands --version, BSD ls does not.
if ls --version >/dev/null 2>&1; then
  ok "Your tools are the GNU (Linux) versions, the same as the lessons show"
else
  ok "Your tools are the BSD (macOS) versions: a few options differ, each lesson tells you which"
fi

echo ""
echo "Result: $passed of $total checks passed."
if [ "$passed" -eq "$total" ]; then
  echo "You're ready for lesson 02."
else
  echo "Fix the ❌ lines above, then run this check again."
  exit 1
fi
