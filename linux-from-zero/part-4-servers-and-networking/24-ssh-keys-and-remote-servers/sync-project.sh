#!/usr/bin/env bash
# sync-project.sh - copy a project folder to a server with rsync. SAFE BY DEFAULT:
# without --go it only shows what WOULD change (a dry run).
# Usage:   ./sync-project.sh LOCAL_FOLDER HOST:REMOTE_FOLDER [--go]
# Example: ./sync-project.sh ~/linux-practice/24/project practice:linux-practice/24/deployed --go

set -euo pipefail

src="${1:?Usage: $0 LOCAL_FOLDER HOST:REMOTE_FOLDER [--go]}"
dest="${2:?Usage: $0 LOCAL_FOLDER HOST:REMOTE_FOLDER [--go]}"
go="${3:-}"

[[ -d "$src" ]] || { echo "Not a folder: $src" >&2; exit 1; }
[[ "$dest" == *:* ]] || { echo "Destination must look like HOST:FOLDER, got '$dest'" >&2; exit 2; }

# rsync options, one per line so each can have a comment. An array keeps them as separate words.
opts=(
  -a                      # archive: copy folders recursively and keep permissions and times
  -v                      # verbose: list each file
  -z                      # compress data on the way (helps on slow links)
  -h                      # human sizes in the summary
  --delete                # delete files on the server that no longer exist locally (an exact mirror)
  --exclude ".git/"       # never copy these
  --exclude "__pycache__/"
  --exclude ".venv/"
)

if [[ "$go" != "--go" ]]; then
  opts+=(--dry-run)       # += adds to the array: only SHOW what would happen
  echo "DRY RUN (nothing is copied). Add --go to really sync."
fi

# The / at the end of "$src/" means "the CONTENTS of the folder", not the folder itself.
rsync "${opts[@]}" "$src/" "$dest/"
