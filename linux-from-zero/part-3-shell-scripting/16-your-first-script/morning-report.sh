#!/usr/bin/env bash
# morning-report.sh - prints a short report about this computer.
# Every line below is a command you already know from Parts 1 and 2.
# A script simply runs them for you, top to bottom, one after another.
# Run it with:  ./morning-report.sh

echo "=============================="   # a line of = signs, just decoration
echo "      MORNING REPORT"
echo "=============================="

echo ""                                 # echo "" prints an empty line (a gap)
echo "--- Date and time ---"
date "+%A %d %B %Y, %H:%M"              # date with a format: weekday, day, month, year, hour:minute

echo ""
echo "--- Who and where ---"
whoami                                  # your user name
hostname                                # the computer's name on the network

echo ""
echo "--- How long the computer has been on ---"
uptime -p                               # -p = "pretty": e.g. "up 2 hours, 5 minutes"

echo ""
echo "--- Free space on the disk that holds your home folder ---"
df -h ~ | tail -n 1                     # df -h = disk free, human sizes; ~ = your home; tail -n 1 = keep the last line only

echo ""
echo "--- Memory (RAM) ---"
free -h | head -n 2                     # free -h = memory in human sizes; head -n 2 = header + the "Mem:" line

echo ""
echo "--- Number of items in your home folder ---"
# The next line is a note for the checker tool "shellcheck" (lesson 16): this simple count is fine here.
# shellcheck disable=SC2012
ls ~ | wc -l                            # ls lists your home, wc -l counts the lines = number of items

echo ""
echo "Have a great day!"
