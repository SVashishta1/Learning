#!/usr/bin/env bash
# setup.sh - creates a messy "downloads" folder to practise on (~/linux-practice/19).
# Running it again resets the folder to messy. Run it with:  bash setup.sh

practice="$HOME/linux-practice/19"
rm -rf "$practice/downloads"             # start fresh (only inside the practice folder)
mkdir -p "$practice/downloads"

# A loop that creates one small file for every name in the list.
for name in "report.pdf" "photo1.JPG" "holiday photo.png" "cat.gif" "song.mp3" \
            "notes.txt" "README.md" "sales.csv" "config.json" "backup.zip" \
            "install.sh" "train.py" "tinyllama.Q4_K_M.gguf" "mystery.xyz"; do
  echo "practice file: $name" > "$practice/downloads/$name"   # \ at a line end = "the line continues"
done

# A list of servers for the while-read example in loops.sh
cat > "$practice/servers.txt" <<'EOF'
# one server per line; lines starting with # are comments
web-1.example.com
web-2.example.com

db-1.example.com
EOF

echo "Practice folder ready: $practice"
ls "$practice/downloads"
