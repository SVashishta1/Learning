#!/usr/bin/env bash
# args.sh - shows the "arguments" (extra words) you type after a script's name.
# Try:  ./args.sh apple "big banana" cherry

echo "Script name (\$0):        $0"     # \$ = print a real dollar sign; $0 = how the script was called
echo "First argument (\$1):     $1"     # the first word after the script name
echo "Second argument (\$2):    $2"     # the second word ("big banana" counts as ONE word thanks to the quotes)
echo "Third argument (\$3):     $3"
echo "Number of arguments (\$#): $#"    # $# = how many arguments there are

echo "All arguments, one per line (\"\$@\"):"
printf '  - %s\n' "$@"                  # "$@" = every argument, each kept as its own word
                                        # printf repeats its pattern once per argument: %s = the text, \n = new line

echo "All arguments glued into one string (\"\$*\"): $*"   # "$*" = all arguments joined with spaces

# A default value: ${1:-World} means "use $1, but if it is empty use World".
who="${1:-World}"
echo "Hello, $who!"

# shift throws away $1 and moves every argument one place left ($2 becomes $1, ...).
shift
echo "After shift, \$1 is now: ${1:-<nothing left>}  and \$# is $#"
