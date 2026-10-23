#!/usr/bin/env bash
# Builds a "pretend GitHub" on your own computer for lesson 03, so you can practise
# push, clone and pull before (or without) a GitHub account.
#   ~/devops-practice/03/pretend-github/mood-app.git  <- plays the role of GitHub (a "bare" repo)
#   ~/devops-practice/03/you/mood-app                 <- your project, with 1 save, no remote yet
# Run it with:  bash setup.sh
set -euo pipefail

PRACTICE="$HOME/devops-practice/03"

if [ -e "$PRACTICE" ]; then
  echo "The folder $PRACTICE already exists, so I did not touch it."
  echo "To start again from zero, delete it first:  rm -rf ~/devops-practice/03"
  exit 1
fi

export GIT_AUTHOR_NAME="Setup Script" GIT_AUTHOR_EMAIL="setup@example.com"
export GIT_COMMITTER_NAME="Setup Script" GIT_COMMITTER_EMAIL="setup@example.com"

# 1. The pretend GitHub: a "bare" repository = only the history, no working files.
#    Real GitHub stores your repositories exactly like this.
mkdir -p "$PRACTICE/pretend-github"
git init --quiet --bare --initial-branch=main "$PRACTICE/pretend-github/mood-app.git"

# 2. Your project, with one save.
mkdir -p "$PRACTICE/you/mood-app"
cd "$PRACTICE/you/mood-app"
git init --quiet --initial-branch=main
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
printf '.env\n__pycache__/\n*.log\n' > .gitignore
printf '# Mood app\n\nGuesses if a sentence sounds happy or sad.\n' > README.md
git add .
git commit --quiet -m "First version of the mood app"

echo "Created:"
echo "  pretend GitHub : $PRACTICE/pretend-github/mood-app.git"
echo "  your project   : $PRACTICE/you/mood-app"
echo "Next:  cd ~/devops-practice/03/you/mood-app"
