#!/usr/bin/env bash
# special-vars.sh - the "special" variables that bash fills in for you.
# Run it with:  ./special-vars.sh

echo "\$\$  = $$   <- the process ID (PID) of THIS script while it runs"

sleep 30 &                       # & = run sleep in the BACKGROUND, so the script does not wait for it
echo "\$!  = $!   <- the PID of the last thing started in the background (that sleep)"
kill "$!"                        # stop that background sleep now; we only wanted its PID

ls /etc/hostname > /dev/null     # a command that works (output thrown away into /dev/null)
echo "\$?  = $?      <- exit code of the last command: 0 means success"

ls /no/such/folder 2> /dev/null  # a command that fails (error message thrown away)
echo "\$?  = $?      <- not 0 means something went wrong (lesson 18 explains the numbers)"

echo "\$0  = $0  <- how this script was called"
echo "\$RANDOM  = $RANDOM <- a new random number (0-32767) every time you read it"
echo "\$SECONDS = $SECONDS     <- seconds since this script started"
echo "\$USER    = $USER  \$PWD = $PWD"
