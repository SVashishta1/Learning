#!/usr/bin/env bash
# setup.sh - lesson 07: builds two files to fix in ~/linux-practice/07
#   shopping-list.txt  (you fix it with nano)
#   app.conf           (you fix it with vim)
# Safe: it only touches that one folder inside your home. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-1-first-steps/07-editing-files-with-nano-and-vim/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/07"
rm -rf "$practice"                      # delete an old copy, so you always start fresh
mkdir -p "$practice"
cd "$practice"

# A shopping list with two spelling mistakes and one line that must go.
cat > shopping-list.txt <<'EOF'
Shopping list
- aples
- bred
- milk
- chocolate cake (too much sugar, delete this line)
EOF

# A settings file for a pretend AI web API. You'll change it with vim.
cat > app.conf <<'EOF'
# app.conf - settings for a pretend AI API
app_name = mood-api
port = 8000
debug = true
log_level = info
model = small
delete_me = this line should not be here
EOF

echo "Practice folder ready: $practice"
