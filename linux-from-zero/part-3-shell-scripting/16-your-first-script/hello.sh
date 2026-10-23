#!/usr/bin/env bash
# ^ Line 1 is the "shebang". #! tells Linux "run this file with the program
#   that follows". /usr/bin/env bash means "find the program called bash on
#   this computer and use it". It must be the very first line, no spaces before it.

# Every line that starts with # (except the shebang) is a COMMENT.
# Bash skips comments. They are notes for humans, like this one.

# hello.sh - my very first script.
# Run it with:  ./hello.sh

echo "Hello from my first script!"   # echo prints the text between the quotes
echo "Today is:"                     # another line of text
date                                 # runs the date command, exactly as if you typed it
echo "You are logged in as:"
whoami                               # prints your user name
echo "You are standing in this folder:"
pwd                                  # prints the folder you ran the script from
