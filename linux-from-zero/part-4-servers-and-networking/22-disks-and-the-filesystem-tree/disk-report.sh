#!/usr/bin/env bash
# disk-report.sh - where is my disk space going?
# Usage:  ./disk-report.sh [FOLDER]     (default: your home folder)

set -euo pipefail
folder="${1:-$HOME}"

echo "=== 1. Disks and how full they are (df) ==="
# df = "disk free". -h = human sizes (G, M), -T = show the filesystem type.
# -x = leave out these pretend filesystems that live in memory, not on a disk.
df -hT -x tmpfs -x devtmpfs -x squashfs -x efivarfs

echo ""
echo "=== 2. Inodes: the number of FILES a disk can hold (df -i) ==="
# A disk can be "full" with free space left if it runs out of inodes (millions of tiny files).
df -hi "$folder" | sed 's/^/  /'

echo ""
echo "=== 3. Biggest items inside $folder (du) ==="
# du = "disk usage". -x = stay on this disk, -h = human sizes,
# --max-depth=1 = only one level down, 2>/dev/null = hide "Permission denied" noise.
# sort -rh = sort human sizes (-h), biggest first (-r). head -n 11 = the folder itself + top 10.
du -xh --max-depth=1 "$folder" 2> /dev/null | sort -rh | head -n 11

echo ""
echo "=== 4. Block devices: the physical disks and their parts (lsblk) ==="
# lsblk lists disks (sda, nvme0n1, vda...) and partitions (sda1...). -e 7 hides loop devices (snaps).
lsblk -e 7 -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS 2> /dev/null || lsblk
