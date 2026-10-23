#!/usr/bin/env bash
# backup.sh - a robust, reusable backup tool. A template for every "real" script you write.
# It packs a folder into a time-stamped .tar.gz file, checks the archive, and keeps only
# the newest N backups. Run ./backup.sh -h for help.

set -euo pipefail                      # strict mode: stop on errors, unset variables and broken pipes

# --- Settings (defaults; options below can change them) ---------------------
source_dir="$HOME/linux-practice/20/project"   # what to back up
dest_dir="$HOME/linux-practice/20/backups"     # where to put the archives
keep=3                                          # how many backups to keep
dry_run=false                                   # true = only say what would happen
verbose=false                                   # true = print extra details
script_name=$(basename "$0")                    # e.g. backup.sh (for messages)

# --- Helper functions --------------------------------------------------------
usage() {
  # A here-document: the text between <<EOF and EOF is printed as-is ($script_name is filled in).
  cat <<EOF
Usage: $script_name [-s SOURCE] [-d DEST] [-k KEEP] [-n] [-v] [-h]

Pack SOURCE into DEST/<name>-YYYYmmdd-HHMMSS.tar.gz and keep the newest KEEP backups.

Options:
  -s SOURCE  folder to back up      (default: $source_dir)
  -d DEST    folder for the backups (default: $dest_dir)
  -k KEEP    how many backups to keep, 1 or more (default: $keep)
  -n         dry run: show what would happen, change nothing
  -v         verbose: print extra details
  -h         show this help and exit

Exit codes: 0 = success, 1 = something failed, 2 = wrong usage
EOF
}

log()  { echo "[$(date +%H:%M:%S)] $*" >&2; }              # messages go to stderr (stream 2)
info() { if [[ "$verbose" == true ]]; then log "$@"; fi; }  # only printed with -v
die()  { log "ERROR: $*"; exit 1; }                         # print an error and stop

# --- Read the options with getopts --------------------------------------------
# "s:d:k:nvh" = the letters we accept. A colon after a letter means "this option needs a value".
while getopts "s:d:k:nvh" opt; do
  case "$opt" in
    s) source_dir="$OPTARG" ;;          # $OPTARG = the value given after -s
    d) dest_dir="$OPTARG" ;;
    k) keep="$OPTARG" ;;
    n) dry_run=true ;;
    v) verbose=true ;;
    h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;             # getopts sets opt to ? for an unknown option
  esac
done
shift $(( OPTIND - 1 ))                 # throw away the options we read; "$@" now holds what is left
if (( $# > 0 )); then                   # nothing else is expected
  echo "Unexpected argument: $1" >&2; usage >&2; exit 2
fi

# --- Check the inputs before doing anything ----------------------------------
[[ "$keep" =~ ^[1-9][0-9]*$ ]] || { echo "-k needs a whole number of 1 or more, got '$keep'" >&2; exit 2; }
[[ -d "$source_dir" ]] || die "source folder '$source_dir' does not exist"
command -v tar > /dev/null || die "the tar command is not installed"

# --- Clean up automatically, whatever happens ----------------------------------
work_dir=$(mktemp -d)                   # mktemp -d = make a brand-new empty temp folder, print its name
cleanup() {
  rm -rf "$work_dir"                    # remove the temp folder
  info "cleaned up $work_dir"
}
trap cleanup EXIT                       # run cleanup when the script ends: success, error or Ctrl+C
trap 'log "FAILED at line $LINENO: $BASH_COMMAND"' ERR   # on any failing command, say where
trap 'log "Interrupted"; exit 130' INT TERM               # Ctrl+C (INT) or kill (TERM): exit cleanly

# --- Do the work ------------------------------------------------------------
name=$(basename "$source_dir")          # e.g. project
stamp=$(date +%Y%m%d-%H%M%S)            # e.g. 20261022-091500
archive="$name-$stamp.tar.gz"

info "source=$source_dir dest=$dest_dir keep=$keep dry_run=$dry_run"

if [[ "$dry_run" == true ]]; then
  log "DRY RUN: would create $dest_dir/$archive"
else
  mkdir -p "$dest_dir"
  if [[ -e "$dest_dir/$archive" ]]; then   # two runs in the same second would get the same name
    die "$dest_dir/$archive already exists; wait a second and try again"
  fi
  # tar: -c create, -z compress with gzip, -f the archive file name,
  #      -C go into this folder first, then pack the item "$name" from there.
  tar -czf "$work_dir/$archive" -C "$(dirname "$source_dir")" "$name"
  tar -tzf "$work_dir/$archive" > /dev/null   # -t = list the contents: proves the archive is readable
  mv "$work_dir/$archive" "$dest_dir/"        # only a checked archive reaches the backups folder
  size=$(du -h "$dest_dir/$archive" | cut -f1)
  log "created $dest_dir/$archive ($size)"
fi

# --- Keep only the newest $keep backups -----------------------------------------
shopt -s nullglob                       # a pattern that matches nothing becomes an empty list
backups=("$dest_dir/$name"-*.tar.gz)    # all backups; names contain the time, so they sort oldest first
extra=$(( ${#backups[@]} - keep ))      # how many are too many
if (( extra > 0 )); then
  for old in "${backups[@]:0:extra}"; do   # ${array[@]:0:extra} = the first $extra items (the oldest)
    if [[ "$dry_run" == true ]]; then
      log "DRY RUN: would delete old backup $(basename "$old")"
    else
      rm -f -- "$old"
      log "deleted old backup $(basename "$old")"
    fi
  done
fi

log "done. Backups now in $dest_dir:"
ls -1 "$dest_dir" >&2 2> /dev/null || true   # || true = do not fail if the folder is missing (dry run)
