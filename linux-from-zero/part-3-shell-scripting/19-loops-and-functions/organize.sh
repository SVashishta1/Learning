#!/usr/bin/env bash
# organize.sh - tidies a messy folder by moving each file into a sub-folder for its type.
# Usage:   ./organize.sh [FOLDER] [--dry-run]
# Default: FOLDER = ~/linux-practice/19/downloads
# --dry-run = only SHOW what would move, change nothing (always try this first!)

folder="$HOME/linux-practice/19/downloads"   # default folder to tidy
dry_run="no"                                 # default: really move files

# Look at every argument, in any order: --dry-run switches on dry-run mode, anything else is the folder.
for arg in "$@"; do
  case "$arg" in
    --dry-run) dry_run="yes" ;;
    *)         folder="$arg" ;;
  esac
done

# category_for FILENAME -> prints the folder name for that kind of file.
category_for() {
  local name="${1,,}"                    # ${1,,} = $1 in lowercase, so .JPG and .jpg are the same
  case "$name" in
    *.jpg|*.jpeg|*.png|*.gif|*.webp) echo "images" ;;
    *.mp3|*.wav|*.flac|*.ogg)        echo "audio" ;;
    *.mp4|*.mkv|*.mov)               echo "videos" ;;
    *.pdf|*.doc|*.docx|*.txt|*.md)   echo "documents" ;;
    *.csv|*.json|*.xlsx)             echo "data" ;;
    *.gguf|*.safetensors|*.onnx|*.pt) echo "models" ;;  # AI model files
    *.zip|*.tar|*.gz|*.tgz)          echo "archives" ;;
    *.sh|*.py)                       echo "code" ;;
    *)                               echo "other" ;;
  esac
}

# move_file PATH CATEGORY -> moves (or pretends to move) one file into FOLDER/CATEGORY/
move_file() {
  local path="$1"
  local category="$2"
  local target="$folder/$category"
  if [[ "$dry_run" == "yes" ]]; then
    echo "  would move  $(basename "$path")  ->  $category/"
  else
    mkdir -p "$target"                   # create the category folder if needed
    mv -n -- "$path" "$target/"          # -n = never overwrite a file that is already there
    echo "  moved  $(basename "$path")  ->  $category/"
  fi
}

# --- main part ---------------------------------------------------------------
if [[ ! -d "$folder" ]]; then
  echo "Folder '$folder' does not exist. Did you run setup.sh?" >&2
  exit 1
fi

echo "Organizing: $folder  (dry run: $dry_run)"
moved=0
for path in "$folder"/*; do              # every item directly inside the folder
  [[ -f "$path" ]] || continue           # skip folders (and the literal * if the folder is empty)
  category=$(category_for "$(basename "$path")")
  move_file "$path" "$category"
  moved=$(( moved + 1 ))
done

echo "Done: $moved file(s) handled."
