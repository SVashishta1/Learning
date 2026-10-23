#!/usr/bin/env bash
# functions.sh - a function is a named mini-script inside your script.
# Run it with:  ./functions.sh

# --- 1. Define a function: name() { commands; } ----------------------------
# Defining it does NOT run it. It is like writing a recipe card.
say_hello() {
  echo "Hello from a function!"
}
say_hello                                # calling it by name runs it (cooking the recipe)
say_hello                                # ...as many times as you like

# --- 2. Functions get their own $1, $2, $# ----------------------------------
greet() {
  local name="${1:-stranger}"            # inside a function, $1 is the function's first argument
  local times="${2:-1}"                  # local = this variable only exists inside the function
  for (( i = 1; i <= times; i++ )); do   # i++ = add 1 to i
    echo "Hi, $name!"
  done
}
greet "Priya"                            # one argument
greet "Ravi" 2                           # two arguments: name and how many times

# --- 3. local vs global ------------------------------------------------------
colour="blue"                            # a normal ("global") variable, visible everywhere
paint() {
  local colour="red"                     # a NEW colour that lives only inside paint()
  echo "Inside paint(): colour is $colour"
}
paint
echo "Outside, colour is still $colour (local kept it safe)"

# --- 4. Giving back a VALUE: echo it, and catch it with $( ) -----------------
square() {
  echo $(( $1 * $1 ))                    # print the answer...
}
result=$(square 7)                       # ...and $( ) catches what the function printed
echo "7 squared is $result"

# --- 5. Giving back SUCCESS or FAILURE: return 0 / return 1 ------------------
# return sets the function's exit code (0-255), exactly like exit does for a script.
is_even() {
  if (( $1 % 2 == 0 )); then
    return 0                             # 0 = yes / success
  else
    return 1                             # 1 = no / failure
  fi
}
for n in 3 4; do
  if is_even "$n"; then                  # if uses the exit code, so functions plug straight in
    echo "$n is even"
  else
    echo "$n is odd"
  fi
done

# --- 6. A useful one: log messages with a time stamp ------------------------
log() {
  echo "[$(date +%H:%M:%S)] $*"          # $* = all the function's arguments as one line of text
}
log "Starting the job"
log "Job finished"
