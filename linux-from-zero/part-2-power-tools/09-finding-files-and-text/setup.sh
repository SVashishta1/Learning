#!/usr/bin/env bash
# setup.sh - lesson 09: builds a small pretend AI project to search in ~/linux-practice/09/project
# Safe: it only touches ~/linux-practice/09. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-2-power-tools/09-finding-files-and-text/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/09"
rm -rf "$practice"                      # delete an old copy, so you always start fresh
p="$practice/project"
mkdir -p "$p/src/models" "$p/tests" "$p/logs/old" "$p/data" "$p/notes" "$p/config" "$p/build" "$p/cache"
cd "$p"

cat > README.md <<'TXT'
# Pretend chat app
A tiny project to practise find and grep on.
TXT

cat > src/app.py <<'TXT'
import requests
from models.chat import answer

# TODO: add rate limiting
def main():
    question = input("Ask me: ")
    print(answer(question))

if __name__ == "__main__":
    main()
TXT

cat > src/utils.py <<'TXT'
def clean(text):
    # todo: handle emoji
    return text.strip().lower()
TXT

cat > src/models/chat.py <<'TXT'
import requests

API_URL = "http://localhost:11434/v1"

def answer(question):
    # TODO: call the real model
    return "I am a pretend model. You asked: " + question
TXT

cat > src/models/embed.py <<'TXT'
def embed(text):
    return [len(text), text.count(" ")]
TXT

cat > tests/test_app.py <<'TXT'
from utils import clean

def test_clean():
    assert clean("  Hi ") == "hi"
TXT

# A recent log: 30 lines, every 6th line is an ERROR, plus one WARN that mentions "error" in lowercase
i=1
while [ "$i" -le 30 ]; do
  if [ $((i % 6)) -eq 0 ]; then
    printf '2026-03-14 10:%02d:00 ERROR chat: model timeout after 30s\n' "$i"
  elif [ "$i" -eq 13 ]; then
    printf '2026-03-14 10:%02d:00 WARN  chat: retrying after network error\n' "$i"
  else
    printf '2026-03-14 10:%02d:00 INFO  chat: answered in %d ms\n' "$i" $((100 + i * 7))
  fi
  i=$((i + 1))
done > logs/app-2026-03-14.log

# An OLD log (we set its "last modified" date to January 2020 with touch -t)
cat > logs/old/app-2020-01-10.log <<'TXT'
2020-01-10 09:00:00 INFO  chat: started
2020-01-10 09:05:00 ERROR chat: out of memory
2020-01-10 09:06:00 INFO  chat: restarted
2020-01-10 09:30:00 ERROR chat: disk full
2020-01-10 09:31:00 INFO  chat: stopped
TXT
touch -t 202001102359 logs/old/app-2020-01-10.log

# A big file (over 1 MB) made with awk, and a small one
awk 'BEGIN { print "id,text,label"; for (i = 1; i <= 30000; i++) printf "%d,this is example sentence number %d,%s\n", i, i, (i % 3 ? "positive" : "negative") }' > data/big-dataset.csv
printf 'id,text,label\n1,great product,positive\n2,too slow,negative\n' > data/small.csv

printf 'Buy more GPUs\nTODO: write the docs\n' > notes/todo.txt
printf 'Meeting on Monday about the chat app.\n' > "notes/Meeting Notes.txt"
printf 'IDEA: voice mode\n' > notes/IDEAS.TXT

printf 'ANTHROPIC_API_KEY=pretend-key-123\n' > .env       # a hidden "secrets" file
printf 'model: claude-haiku-5-5\nport: 8000\n' > config/settings.yaml
printf 'temp\n' > cache/a.tmp
printf 'temp\n' > cache/b.tmp
# build/ stays empty on purpose

echo "Practice folder ready: $p"
