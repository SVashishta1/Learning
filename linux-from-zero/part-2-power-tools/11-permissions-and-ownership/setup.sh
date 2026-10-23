#!/usr/bin/env bash
# setup.sh - lesson 11: builds files with "wrong" permissions for you to fix in ~/linux-practice/11
# Safe: it only touches ~/linux-practice/11. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-2-power-tools/11-permissions-and-ownership/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/11"
if [ -d "$practice" ]; then
  chmod -R u+rwx "$practice"            # give yourself full access first, so the old copy can be deleted
  rm -rf "$practice"                    # delete the old copy, so you always start fresh
fi
mkdir -p "$practice/private" "$practice/shared" "$practice/locked-folder" "$practice/tools"
cd "$practice"

printf 'Dear diary, today I learned chmod.\n' > diary.txt
printf '#!/usr/bin/env bash\necho "Hello! I am running."\n' > hello.sh
printf 'Meeting notes everyone may read.\n' > public-notes.txt
printf 'Do not change me.\n' > readonly.txt
printf 'The password is: swordfish\n' > locked-folder/secret.txt
printf 'Team plan\n' > shared/plan.txt
for t in backup deploy cleanup; do
  printf '#!/usr/bin/env bash\necho "%s done"\n' "$t" > "tools/$t.sh"
done

# Now set the starting permissions (lesson 11 explains the numbers)
chmod 644 diary.txt          # rw-r--r--  everyone can read your diary (bad!)
chmod 644 hello.sh           # rw-r--r--  a script nobody may run (yet)
chmod 600 public-notes.txt   # rw-------  "public" notes only you can read (wrong!)
chmod 444 readonly.txt       # r--r--r--  nobody may change it, not even you
chmod 755 private            # rwxr-xr-x  a "private" folder everyone can enter (bad!)
chmod 775 shared             # rwxrwxr-x  a folder for a team
chmod 644 tools/*.sh         # three scripts that can't be run yet
chmod 600 locked-folder      # rw-------  a folder without x: you can't go in!

echo "Practice folder ready: $practice"
