#!/usr/bin/env bash
# menu.sh - a tiny interactive menu: a while loop + a case statement.
# Run it with:  ./menu.sh   (type a number and press Enter; q quits)

while true; do                           # true always succeeds, so this loops forever... until break
  echo ""
  echo "What would you like to see?"
  echo "  1) date and time"
  echo "  2) disk space"
  echo "  3) who am I"
  echo "  q) quit"
  read -r -p "Your choice: " choice

  # case compares $choice with each pattern, top to bottom, and runs the FIRST match.
  case "$choice" in
    1|date)                              # | = "or": typing 1 or date both match
      date
      ;;                                 # ;; = end of this choice (like a full stop)
    2|disk)
      df -h /
      ;;
    3|me|whoami)
      echo "You are $(whoami) on $(hostname)"
      ;;
    q|Q|quit|exit)
      echo "Bye!"
      break                              # leave the while loop
      ;;
    "")                                  # "" = the user just pressed Enter
      echo "Please type something."
      ;;
    *)                                   # * = anything else (the catch-all, always last)
      echo "Sorry, '$choice' is not on the menu."
      ;;
  esac                                   # esac = end of case ("case" backwards)
done
