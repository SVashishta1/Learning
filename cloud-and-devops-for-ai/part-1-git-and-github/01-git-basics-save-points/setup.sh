#!/usr/bin/env bash
# Creates a small practice project for lesson 01 in ~/devops-practice/01/mood-app
# It is NOT a git repository yet: you turn it into one in the lesson.
# Run it with:  bash setup.sh
set -euo pipefail

PRACTICE="$HOME/devops-practice/01/mood-app"

if [ -e "$PRACTICE" ]; then
  echo "The folder $PRACTICE already exists, so I did not touch it."
  echo "To start again from zero, delete it first:  rm -rf ~/devops-practice/01"
  exit 1
fi

mkdir -p "$PRACTICE/__pycache__"
cd "$PRACTICE"

# 1. The program: guesses if a sentence sounds happy or sad.
cat > mood.py <<'EOF'
# mood.py - guesses if a sentence sounds happy or sad.
import sys

HAPPY_WORDS = ["good", "great", "love", "happy"]
SAD_WORDS = ["bad", "awful", "hate", "sad"]


def guess_mood(sentence):
    score = 0
    for word in sentence.lower().split():
        if word in HAPPY_WORDS:
            score = score + 1
        if word in SAD_WORDS:
            score = score - 1
    if score > 0:
        return "happy"
    if score < 0:
        return "sad"
    return "not sure"


if __name__ == "__main__":
    sentence = " ".join(sys.argv[1:]) or "I love this great course"
    print(sentence, "->", guess_mood(sentence))
EOF

# 2. A short description of the project.
cat > README.md <<'EOF'
# Mood app

A tiny program that guesses if a sentence sounds happy or sad.

Run it:  python3 mood.py I love pizza
EOF

# 3. A pretend secret. Real projects keep API keys in a file like this.
#    It must NEVER be saved in git (you will make git ignore it).
echo "ANTHROPIC_API_KEY=sk-ant-this-is-not-a-real-key" > .env

# 4. Junk that programs create on their own: never worth saving.
printf 'pretend compiled python\n' > __pycache__/mood.cpython-312.pyc
printf '2026-01-01 12:00:00 started\n2026-01-01 12:00:01 finished\n' > debug.log

echo "Practice project created in: $PRACTICE"
echo "Next:  cd ~/devops-practice/01/mood-app"
