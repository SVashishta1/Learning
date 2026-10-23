#!/usr/bin/env bash
# compare.sh - compares numbers and text, and checks a pattern.
# Usage:  ./compare.sh NUMBER1 NUMBER2 [EMAIL]
# Example: ./compare.sh 7 12 sam@example.com

a="${1:?Usage: $0 NUMBER1 NUMBER2 [EMAIL]}"   # stop with a usage message if $1 is missing
b="${2:?Usage: $0 NUMBER1 NUMBER2 [EMAIL]}"   # same for $2
email="${3:-}"                                  # optional: empty if not given

# --- Numbers: use -lt -gt -eq -ne -le -ge inside [[ ]], or < > == inside (( )) ---
if [[ "$a" -lt "$b" ]]; then                    # -lt = less than
  echo "$a is smaller than $b"
elif [[ "$a" -gt "$b" ]]; then                  # -gt = greater than
  echo "$a is bigger than $b"
else
  echo "$a and $b are equal"
fi

if (( a % 2 == 0 )); then                       # (( )) = maths test; % = remainder; even numbers leave 0
  echo "$a is even"
else
  echo "$a is odd"
fi

# --- Text: == and != compare strings ---
if [[ "$a" == "$b" ]]; then                     # == on text: exactly the same characters?
  echo "As text, '$a' and '$b' are the same"
else
  echo "As text, '$a' and '$b' are different"
fi

# --- Patterns: == with * on the right side matches a "glob" (wildcard) ---
if [[ "$a" == 1* ]]; then                       # 1* = starts with 1 (no quotes around the pattern!)
  echo "$a starts with the digit 1"
fi

# --- Empty or not: -z (zero length) and -n (non-zero length) ---
if [[ -z "$email" ]]; then                      # -z = the text is empty
  echo "No email given (it was optional)"
elif [[ "$email" =~ ^[^@[:space:]]+@[^@[:space:]]+\.[a-z]+$ ]]; then
  # =~ = matches a "regular expression" (regex), a pattern language:
  #   ^ start, [^@[:space:]]+ one or more chars that are not @ or space, @ a real @,
  #   \. a real dot, [a-z]+ letters, $ end
  echo "'$email' looks like an email address"
else
  echo "'$email' does NOT look like an email address"
fi
