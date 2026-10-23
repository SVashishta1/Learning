#!/usr/bin/env bash
# proc-peek.sh - "everything is a file": read facts about the computer straight from /proc.
# These files are not stored on a disk. The kernel writes their contents the moment you read them.
# Run it with:  ./proc-peek.sh

set -euo pipefail

echo "CPU model:    $(grep -m 1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
# grep -m 1 = stop after the first match; cut -d: -f2 = the part after the colon; sed removes the leading space
echo "CPU cores:    $(grep -c '^processor' /proc/cpuinfo)"      # one "processor" block per core
echo "Memory total: $(awk '/^MemTotal/ {printf "%.1f GiB", $2/1024/1024}' /proc/meminfo)"
echo "Memory free:  $(awk '/^MemAvailable/ {printf "%.1f GiB", $2/1024/1024}' /proc/meminfo) available"
# awk '/pattern/ {action}' = on lines matching the pattern, do the action; $2 = the 2nd column (in kB)
echo "Up for:       $(awk '{printf "%d hours %d minutes", $1/3600, ($1%3600)/60}' /proc/uptime)"
echo "Load average: $(cut -d ' ' -f 1-3 /proc/loadavg)   (1, 5 and 15 minutes; lesson 27)"
echo "Kernel:       $(cat /proc/sys/kernel/osrelease)"
echo ""
echo "This script is process number $$. The kernel keeps a folder about it: /proc/$$"
grep -E '^(Name|State|VmRSS)' "/proc/$$/status"                # VmRSS = memory it is using right now
echo "It was started with the command line: $(tr '\0' ' ' < "/proc/$$/cmdline")"
# cmdline separates words with an invisible \0 character; tr turns those into spaces
