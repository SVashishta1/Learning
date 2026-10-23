#!/usr/bin/env bash
# setup.sh - creates a small "project" to back up (~/linux-practice/20). Safe to run again.
# Run it with:  bash setup.sh

set -euo pipefail                         # even setup scripts deserve strict mode
practice="$HOME/linux-practice/20"
mkdir -p "$practice/project/data"

# Here-documents (explained in this lesson) write several lines at once.
cat > "$practice/project/notes.md" <<'EOF'
# My AI project
- TODO: clean the data
- TODO: train a tiny model
EOF
cat > "$practice/project/train.py" <<'EOF'
print("pretend training... done!")
EOF
printf 'id,text,label\n1,great product,positive\n2,broken on arrival,negative\n' > "$practice/project/data/reviews.csv"

echo "Practice project ready: $practice/project"
find "$practice/project" | sort           # show every file and folder inside it
