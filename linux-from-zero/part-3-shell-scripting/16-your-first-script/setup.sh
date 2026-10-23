#!/usr/bin/env bash
# setup.sh - creates the practice folder for lesson 16.
# It only touches ~/linux-practice/16 (a folder inside your home). Safe to run again.
# Run it with:  bash setup.sh

practice="$HOME/linux-practice/16"      # where the practice files will live ($HOME = your home folder)

mkdir -p "$practice"                    # make the folder (-p = also make parents, no error if it exists)

# Create broken.sh, a script with TWO classic beginner problems:
#   1. it is not executable (no x permission), so ./broken.sh says "Permission denied"
#   2. it has Windows line endings (\r\n), so bash chokes on the invisible \r
# printf prints text exactly as given; \r\n is "carriage return + new line" (Windows style).
printf '#!/usr/bin/env bash\r\necho "I am fixed! Well done."\r\n' > "$practice/broken.sh"

chmod -x "$practice/broken.sh"          # make sure it is NOT executable (that is problem 1)

echo "Practice folder ready: $practice"
ls -l "$practice"                       # show what was created
