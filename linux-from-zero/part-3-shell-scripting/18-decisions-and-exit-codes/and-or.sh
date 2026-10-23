#!/usr/bin/env bash
# and-or.sh - && (AND) and || (OR): tiny decisions on one line.
# Run it with:  ./and-or.sh

# A && B  = run B only if A SUCCEEDED (exit code 0).  "Do this, and if that worked, do that."
mkdir -p ~/linux-practice/18 && echo "1. Folder is ready, so this line runs."

# A || B  = run B only if A FAILED (exit code not 0).  "Try this, or else do that."
ls /no/such/folder 2> /dev/null || echo "2. ls failed, so the 'or else' part runs."

# A common safety pattern: cd somewhere || stop the script. Never carry on in the wrong folder!
cd ~/linux-practice/18 || exit 1
echo "3. Now working in: $(pwd)"

# Combining both: A && B || C reads as "if A then B, otherwise C".
grep -q "^root:" /etc/passwd && echo "4. The root user exists." || echo "4. No root user?!"
# Careful: if B itself fails, C runs too. For anything important, use a real if/then/else.

# ! flips success and failure.
! grep -q zebra /etc/passwd && echo "5. No zebra in /etc/passwd (! turned 'not found' into success)."

# The exit code of a pipeline is the exit code of the LAST command in it.
grep zebra /etc/passwd | sort > /dev/null
echo "6. grep failed but 'grep | sort' gives $? because sort (the last command) worked. Lesson 20 fixes this."
