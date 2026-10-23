#!/usr/bin/env bash
# tour.sh - a guided tour of the Linux folder tree (the "Filesystem Hierarchy Standard").
# It only LOOKS at things, it changes nothing. Run it with:  ./tour.sh

set -euo pipefail

# show FOLDER "what it is for" -> prints the folder, its purpose, and a few things inside it
show() {
  local dir="$1"
  local purpose="$2"
  printf '%-10s %s\n' "$dir" "$purpose"          # %-10s = text padded to 10 characters, so columns line up
  if [[ -d "$dir" && -r "$dir" ]]; then          # only peek inside folders we are allowed to read
    # find -mindepth 1 -maxdepth 1 = the items directly inside; -printf '%f\n' = just their names
    # sort = alphabetical, head -n 4 = first 4, paste -sd ' ' - = join the lines with spaces
    local sample
    sample=$(find "$dir" -mindepth 1 -maxdepth 1 -printf '%f\n' 2> /dev/null | sort | head -n 4 | paste -sd ' ' -) || true
    printf '%-10s   e.g. %s\n' "" "${sample:-(empty)}"
  else
    printf '%-10s   (not readable as %s)\n' "" "$(whoami)"
  fi
}

echo "THE LINUX FOLDER TREE - everything starts at / (the 'root')"
echo ""
show /        "the root: the top of the tree, every other folder hangs from here"
show /home    "your files: one folder per user (/home/sam). Same idea as C:\\Users on Windows"
show /root    "the home folder of the root (admin) user"
show /etc     "settings (configuration) for the whole system and its programs: text files"
show /var     "'variable' data that grows: logs, caches, databases, websites"
show /var/log "log files: what happened and when (lesson 25 reads them)"
show /usr     "installed programs and their files (read-only during normal use)"
show /usr/bin "the commands you run: ls, grep, python3... (/bin points here on Ubuntu)"
show /usr/local "programs YOU installed by hand (not by apt)"
show /opt     "big optional add-on apps, one folder each (/opt/ai-api in lesson 28)"
show /tmp     "temporary files: anyone can write here; often wiped at reboot"
show /dev     "devices shown as files: disks (/dev/sda), /dev/null, /dev/random"
show /proc    "a window into the running kernel and every process: not real files on disk"
show /sys     "hardware and driver settings, also shown as files"
show /boot    "the kernel and what the computer needs to start"
show /mnt     "a place to attach (mount) a disk by hand for a while"
show /media   "where USB sticks and CDs appear automatically"
show /srv     "data for services this server offers (some admins use it for websites)"
show /run     "information about the running system since boot (PID files, sockets)"
