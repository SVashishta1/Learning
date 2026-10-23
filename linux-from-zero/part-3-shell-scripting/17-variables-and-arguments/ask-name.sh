#!/usr/bin/env bash
# ask-name.sh - asks you questions and remembers the answers in variables.
# Run it with:  ./ask-name.sh

# read waits for you to type a line and press Enter, then stores it in a variable.
#   -r  = "raw": keep backslashes as they are (always use it)
#   -p  = show this prompt text first
read -r -p "What is your name? " name
read -r -p "How old are you? " age

next=$(( age + 1 ))                       # maths with the answer (it must be a whole number)
echo "Nice to meet you, $name. Next year you will be $next."
