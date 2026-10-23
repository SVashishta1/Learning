#!/usr/bin/env bash
# setup.sh - fills ~/linux-practice/22 with about 95 MB of files, including a hidden space hog.
# Your job (Run it, steps 7-9): find the biggest thing and delete it. Safe to run again.
# Run it with:  bash setup.sh

set -euo pipefail
practice="$HOME/linux-practice/22"
rm -rf "$practice"
mkdir -p "$practice"/{projects,downloads,logs,.cache/models}    # {a,b} = make several folders at once

# head -c 60M /dev/zero = take 60 megabytes of zero bytes. Real data, so it really uses disk space.
head -c 60M /dev/zero > "$practice/.cache/models/old-model.gguf"   # the hog, hidden in a dot-folder
head -c 25M /dev/zero > "$practice/downloads/dataset.zip"
head -c 10M /dev/zero > "$practice/logs/app.log"
echo "Important: do NOT delete me." > "$practice/projects/notes.txt"

echo "Practice folder ready: $practice"
echo "Something in there is wasting a lot of space. Can you find it?"
