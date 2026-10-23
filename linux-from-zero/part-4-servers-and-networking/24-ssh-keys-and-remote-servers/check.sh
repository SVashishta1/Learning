#!/usr/bin/env bash
# check.sh - checks your SSH setup for lesson 24.  Run it with:  ./check.sh

pass=0
fail=0
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL  $1"; echo "        hint: $2"; fail=$((fail + 1)); }

# perm FILE -> prints the file's permissions as a number like 600 (stat -c %a = access rights in octal)
perm() { stat -c %a "$1" 2> /dev/null; }

echo "Checking lesson 24..."

key="$HOME/.ssh/id_ed25519"
if [[ -f "$key" && -f "$key.pub" ]]; then
  ok "you have an ed25519 key pair (id_ed25519 + id_ed25519.pub)"
else
  bad "no ~/.ssh/id_ed25519 key pair" "Run it, step 4: ssh-keygen -t ed25519 -C \"your comment\""
fi

if [[ "$(perm "$HOME/.ssh")" == "700" ]]; then
  ok "your .ssh folder is 700 (only you can enter it)"
else
  bad "your .ssh folder is $(perm "$HOME/.ssh"), should be 700" "chmod 700 ~/.ssh"
fi

if [[ -f "$key" && "$(perm "$key")" == "600" ]]; then
  ok "private key is 600 (only you can read it)"
else
  bad "private key permissions are $(perm "$key"), should be 600" "chmod 600 ~/.ssh/id_ed25519"
fi

if [[ -f "$HOME/.ssh/config" ]] && grep -q "^Host practice" "$HOME/.ssh/config"; then
  ok "your .ssh/config has a 'Host practice' block"
else
  bad "no 'Host practice' block in ~/.ssh/config" "Run it, step 10"
fi

# BatchMode=yes = never ask for a password: succeeds only if key login works.
# ConnectTimeout=5 = give up after 5 seconds.
if ssh -o BatchMode=yes -o ConnectTimeout=5 practice true 2> /dev/null; then
  ok "ssh practice logs in with your key, no password"
else
  bad "'ssh practice' cannot log in with a key" "steps 7-10; if your key has a passphrase, run ssh-add first"
fi

if ssh -o BatchMode=yes -o ConnectTimeout=5 practice 'test -f linux-practice/24/deployed/app.py' 2> /dev/null; then
  ok "the project was synced to the server (deployed/app.py exists)"
else
  bad "deployed/app.py not found on the server" "Run it, step 13: ./sync-project.sh ... --go"
fi

echo ""
echo "Result: $pass passed, $fail failed."
(( fail == 0 )) && echo "All done. You can work on remote servers safely!"
(( fail == 0 ))
