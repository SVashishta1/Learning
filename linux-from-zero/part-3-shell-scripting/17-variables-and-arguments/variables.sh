#!/usr/bin/env bash
# variables.sh - variables, quotes, $(...) and $((...)) in one place.
# Run it with:  ./variables.sh

# --- 1. Making a variable -------------------------------------------------
# NAME=value  with NO spaces around =. (name = "Sam" would try to run a command called "name".)
name="Sam"                      # a box called name, holding the text Sam
city="New Delhi"                # quotes are needed because the value has a space

# --- 2. Using a variable --------------------------------------------------
# Put $ in front of the name to take out what is inside.
echo "Hello, $name!"            # inside double quotes, $name is replaced by Sam
echo "You live in $city."
echo "Plural: ${name}s"         # ${ } marks where the name ends: ${name}s = Sams ($names would be empty)

# --- 3. Single vs double quotes ------------------------------------------
echo "Double quotes: $name"     # double quotes: $ is expanded -> Sam
# shellcheck disable=SC2016  # (note for shellcheck: printing a literal $name is the point here)
echo 'Single quotes: $name'     # single quotes: everything is literal -> $name

# --- 4. Saving a command's output: $( ... ) --------------------------------
# $( command ) runs the command and puts its output right here. This is "command substitution".
today=$(date +%F)               # date +%F prints YYYY-MM-DD, e.g. 2026-10-22
me=$(whoami)                    # your user name
cores=$(nproc)                  # number of CPU cores
echo "Today is $today, you are $me, this computer has $cores CPU cores."

# --- 5. Doing maths: $(( ... )) --------------------------------------------
# $(( )) does whole-number arithmetic. Inside it you can leave out the $ on variable names.
apples=7
boxes=6
total=$(( apples * boxes ))     # * = multiply, + add, - subtract, / divide (whole numbers), % remainder
echo "$apples boxes of $boxes apples = $total apples"
echo "17 / 5 = $(( 17 / 5 )) remainder $(( 17 % 5 ))"   # bash maths has no decimals: 17/5 = 3

# --- 6. Changing a variable ------------------------------------------------
count=1
count=$(( count + 1 ))          # take the old value, add 1, store it back
echo "count is now $count"

# --- 7. Variables that already exist (environment variables, lesson 14) ---
echo "Your home folder is $HOME and your shell is $SHELL"

# --- 8. A variable that must never change ---------------------------------
readonly PI_ISH=3               # readonly = a locked box; changing it later is an error
echo "PI_ISH is locked at $PI_ISH"
