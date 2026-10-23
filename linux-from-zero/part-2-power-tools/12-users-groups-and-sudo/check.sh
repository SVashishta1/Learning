#!/usr/bin/env bash
# check.sh - lesson 12: checks the users, group and team folder you created.
# Run it (as your normal user, no sudo needed) from the course folder with:
#   bash part-2-power-tools/12-users-groups-and-sudo/check.sh
# It only READS the user and group lists (with getent). It changes nothing.
# Run it BEFORE the "Clean up" step at the end of the lesson.

passed=0
total=0
team_dir=/srv/team-practice

ok()  { passed=$((passed + 1)); total=$((total + 1)); printf '✅ %s\n' "$1"; }
bad() { total=$((total + 1)); printf '❌ %s\n   hint: %s\n' "$1" "$2"; }

# in_group USER GROUP -> succeeds if USER is a member of GROUP
in_group() { id -nG "$1" 2>/dev/null | tr ' ' '\n' | grep -qx "$2"; }

if [ "$(uname -s)" != "Linux" ]; then
  echo "❌ This lesson needs Linux (users are managed differently on a Mac)."
  echo "   Use WSL, a Linux machine, or the Docker ubuntu:24.04 option from lesson 01."
  exit 1
fi

me="$(id -un)"
echo "Checking users and groups (you are: $me) ..."
echo ""
echo "Run it:"

if getent passwd alice >/dev/null; then
  ok "user alice exists"
else
  bad "user alice does not exist" "sudo useradd -m -s /bin/bash alice   (step 6)"
fi

if [ "$(getent passwd alice | cut -d: -f7)" = "/bin/bash" ] && [ -d /home/alice ]; then
  ok "alice has a home folder and bash as her shell"
else
  bad "alice needs a home folder (/home/alice) and the shell /bin/bash" "sudo userdel -r alice, then: sudo useradd -m -s /bin/bash alice"
fi

if getent group team >/dev/null; then
  ok "group team exists"
else
  bad "group team does not exist" "sudo groupadd team   (step 8)"
fi

if in_group alice team && in_group "$me" team; then
  ok "alice and $me are both in team"
else
  bad "alice and $me must both be in team" "sudo usermod -aG team alice   and   sudo usermod -aG team $me   (step 9)"
fi

if [ -d "$team_dir" ] && [ "$(stat -c %G "$team_dir")" = "team" ] && [ -g "$team_dir" ]; then
  ok "$team_dir belongs to group team and has the setgid bit"
else
  bad "$team_dir should be owned by group team with mode 2775" "sudo mkdir -p $team_dir; sudo chgrp team $team_dir; sudo chmod 2775 $team_dir   (step 11)"
fi

if [ -f "$team_dir/hello-from-alice.txt" ] && [ "$(stat -c %U "$team_dir/hello-from-alice.txt")" = "alice" ]; then
  ok "alice wrote hello-from-alice.txt in the team folder"
else
  bad "no hello-from-alice.txt owned by alice in $team_dir" "sudo -u alice touch $team_dir/hello-from-alice.txt   (step 12)"
fi

echo ""
echo "Try this:"

if getent passwd aibot >/dev/null && [ "$(getent passwd aibot | cut -d: -f7)" = "/usr/sbin/nologin" ]; then
  ok "1. service user aibot exists and cannot log in (nologin)"
else
  bad "1. no service user aibot with shell /usr/sbin/nologin" "sudo useradd --system --shell /usr/sbin/nologin aibot"
fi

if getent passwd bob >/dev/null && in_group bob team; then
  ok "2. bob exists and is in team"
else
  bad "2. bob should exist and be in team" "sudo useradd -m -s /bin/bash -G team bob"
fi

if [ -f "$team_dir/from-bob.txt" ] && [ "$(stat -c %G "$team_dir/from-bob.txt")" = "team" ]; then
  ok "3. bob's file got the group team automatically (setgid at work)"
else
  bad "3. no from-bob.txt with group team in $team_dir" "sudo -u bob touch $team_dir/from-bob.txt   then   ls -l $team_dir"
fi

echo ""
echo "Result: $passed of $total checks passed."
if [ "$passed" -eq "$total" ]; then
  echo "You can manage users like an admin. Now do the Clean up step, then on to lesson 13!"
else
  echo "Fix the ❌ lines, then run the check again."
  exit 1
fi
