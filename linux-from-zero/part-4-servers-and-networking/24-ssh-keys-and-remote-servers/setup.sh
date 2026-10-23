#!/usr/bin/env bash
# setup.sh - creates a small project in ~/linux-practice/24/project to copy to the "server".
# Run it with:  bash setup.sh

set -euo pipefail
project="$HOME/linux-practice/24/project"
mkdir -p "$project/data"

echo "print('Hello from the server!')" > "$project/app.py"
echo "fastapi" > "$project/requirements.txt"
head -c 200K /dev/urandom > "$project/data/model.bin"     # 200 KB of random bytes: a pretend model file
echo "A tiny project to practise scp and rsync." > "$project/README.md"

echo "Project ready: $project"
find "$project" -type f | sort
