#!/usr/bin/env bash
# setup.sh - lesson 03: builds a "house" of folders with a treasure hunt in ~/linux-practice/03
# Safe: it only touches that one folder inside your home. Run it again any time to start fresh.
# Run it from the course folder with:
#   bash part-1-first-steps/03-moving-around-the-filesystem/setup.sh

set -e                                  # stop at the first command that fails
: "${HOME:?HOME is not set}"            # refuse to run if your home folder is unknown

practice="$HOME/linux-practice/03"
rm -rf "$practice"                      # delete an old copy, so you always start fresh
house="$practice/house"

# mkdir -p makes a folder and any missing parent folders on the way
mkdir -p "$house/kitchen/fridge" "$house/kitchen/cupboard" \
         "$house/living-room/sofa" "$house/bedroom/wardrobe" "$house/bedroom/bed" \
         "$house/attic/old-toys" "$house/garden/shed/tools" "$house/garden/shed/.secret-box"

cd "$house"

# Room contents (just small text files)
printf 'A cold bottle of milk.\n' > kitchen/fridge/milk.txt
printf 'A big piece of cheese.\n' > kitchen/fridge/cheese.txt
printf 'A box of crunchy cereal.\n' > kitchen/cupboard/cereal.txt
printf 'Three coins and a button.\n' > living-room/sofa/coins.txt
printf 'The TV remote. Finally!\n' > living-room/sofa/remote.txt
printf 'Odd socks.\n' > bedroom/wardrobe/socks.txt
printf 'A shirt with a penguin on it.\n' > bedroom/wardrobe/shirt.txt
printf 'An old teddy bear.\n' > attic/old-toys/teddy.txt
printf 'A heavy hammer.\n' > garden/shed/tools/hammer.txt

# The treasure hunt: each clue tells you where to go next.
cat > START-HERE.txt <<'EOF'
Welcome, explorer!
Your first clue is in the kitchen, inside the fridge.
Try:  cd kitchen/fridge   then   ls   then   cat clue.txt
EOF

cat > kitchen/fridge/clue.txt <<'EOF'
Clue 1: well done!
The next clue is under the sofa in the living room.
You are in house/kitchen/fridge. Go UP two folders, then down:
  cd ../../living-room/sofa
EOF

cat > living-room/sofa/clue.txt <<'EOF'
Clue 2: great!
The next clue is in the attic, in the old-toys box.
This time use an ABSOLUTE path (one that starts from your home folder):
  cd ~/linux-practice/03/house/attic/old-toys
EOF

cat > attic/old-toys/clue.txt <<'EOF'
Clue 3: almost there!
The treasure is in a HIDDEN box in the garden shed.
Go to the shed, then list EVERYTHING (hidden things too):
  cd ~/linux-practice/03/house/garden/shed
  ls -a
EOF

cat > garden/shed/.secret-box/treasure.txt <<'EOF'
You found the treasure!
The secret word is: PENGUIN
(The quiz in check.sh will ask you for it.)
EOF

echo "Practice folder ready: $practice"
echo "Start with:  cd ~/linux-practice/03/house  and  cat START-HERE.txt"
