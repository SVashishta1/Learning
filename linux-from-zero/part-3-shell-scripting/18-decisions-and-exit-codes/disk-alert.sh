#!/usr/bin/env bash
# disk-alert.sh - warns when a disk is getting full. Real servers run checks like this all the time.
# Usage:  ./disk-alert.sh [WARN_PERCENT] [CRIT_PERCENT] [FOLDER]
# Defaults: warn at 80%, critical at 90%, check the disk that holds /
# Exit codes (the same ones monitoring tools such as Nagios use):
#   0 = OK, 1 = WARNING, 2 = CRITICAL, 3 = UNKNOWN (bad input)

warn="${1:-80}"                # first argument, or 80 if not given
crit="${2:-90}"                # second argument, or 90
folder="${3:-/}"               # third argument, or / (the root of everything)

# Input check: both limits must be whole numbers. =~ ^[0-9]+$ means "only digits, at least one".
if ! [[ "$warn" =~ ^[0-9]+$ && "$crit" =~ ^[0-9]+$ ]]; then
  echo "UNKNOWN - limits must be whole numbers, got '$warn' and '$crit'" >&2
  exit 3
fi

# df --output=pcent prints a header line "Use%" and then e.g. " 42%".
#   tail -n 1  = keep the last line ( 42%)
#   tr -d ' %' = delete spaces and % signs (42)
used=$(df --output=pcent "$folder" | tail -n 1 | tr -d ' %')

if [[ -z "$used" ]]; then                       # df failed (wrong folder?), so we have no number
  echo "UNKNOWN - could not read disk usage for '$folder'" >&2
  exit 3
elif (( used >= crit )); then                   # >= = greater than or equal
  echo "CRITICAL - $folder is ${used}% full (limit ${crit}%)"
  exit 2
elif (( used >= warn )); then
  echo "WARNING - $folder is ${used}% full (limit ${warn}%)"
  exit 1
else
  echo "OK - $folder is ${used}% full"
  exit 0
fi
