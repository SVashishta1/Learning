#!/usr/bin/env bash
# Builds a practice git repository for lesson 02 in ~/devops-practice/02/chatbot
# It already has a history and a branch that WILL clash (a merge conflict) with main,
# so you can practise fixing one safely.
# Run it with:  bash setup.sh
set -euo pipefail

PRACTICE="$HOME/devops-practice/02/chatbot"

if [ -e "$PRACTICE" ]; then
  echo "The folder $PRACTICE already exists, so I did not touch it."
  echo "To start again from zero, delete it first:  rm -rf ~/devops-practice/02"
  exit 1
fi

# The script's own saves are signed "Setup Script", so it works even before
# you set your own name with git config.
export GIT_AUTHOR_NAME="Setup Script" GIT_AUTHOR_EMAIL="setup@example.com"
export GIT_COMMITTER_NAME="Setup Script" GIT_COMMITTER_EMAIL="setup@example.com"

mkdir -p "$PRACTICE"
cd "$PRACTICE"
git init --quiet --initial-branch=main

# Save 1: the chatbot's settings.
cat > settings.py <<'EOF'
# settings.py - how our chatbot behaves.
MODEL = "claude-haiku-5-5"
SYSTEM_PROMPT = "You are a helpful assistant."
MAX_TOKENS = 300
EOF
git add settings.py
git commit --quiet -m "Add chatbot settings"

# Save 2: a README.
cat > README.md <<'EOF'
# Chatbot

Settings for a small support chatbot live in settings.py.
EOF
git add README.md
git commit --quiet -m "Add README"

# A teammate starts a branch and makes the bot friendlier...
git switch --quiet -c friendly-tone
sed 's/^SYSTEM_PROMPT = .*/SYSTEM_PROMPT = "You are a warm, friendly assistant who loves to help."/' settings.py > settings.tmp
mv settings.tmp settings.py
git commit --quiet -am "Make the assistant sound friendlier"

# ...while, on main, someone else changes THE SAME LINE differently.
git switch --quiet main
sed 's/^SYSTEM_PROMPT = .*/SYSTEM_PROMPT = "You are a helpful assistant. Keep answers short."/' settings.py > settings.tmp
mv settings.tmp settings.py
git commit --quiet -am "Ask for short answers"

echo "Practice repository created in: $PRACTICE"
echo "Branches: main (you are here) and friendly-tone."
echo "Next:  cd ~/devops-practice/02/chatbot"
