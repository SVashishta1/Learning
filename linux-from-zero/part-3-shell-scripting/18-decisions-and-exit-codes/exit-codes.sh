#!/usr/bin/env bash
# exit-codes.sh - every command finishes with a number called its EXIT CODE.
# 0 = "it worked". Anything from 1 to 255 = "something went wrong" (the number says what).
# Run it with:  ./exit-codes.sh

true                                 # a command whose only job is to succeed
echo "true                     -> $?"   # $? = the exit code of the command just before

false                                # a command whose only job is to fail
echo "false                    -> $?"

ls /etc/hostname > /dev/null         # works (output thrown away)
echo "ls /etc/hostname         -> $?"

ls /no/such/file 2> /dev/null        # fails: ls uses 2 for "serious trouble" (here: not found)
echo "ls /no/such/file         -> $?"

grep -q root /etc/passwd             # grep -q = search quietly; finds "root"
echo "grep root /etc/passwd    -> $?   (found)"

grep -q zebra /etc/passwd            # grep finds nothing: 1 = "no match" (not an error!)
echo "grep zebra /etc/passwd   -> $?   (not found)"

grep -q root /no/such/file 2> /dev/null   # grep could not even read the file: 2 = error
echo "grep root /no/such/file  -> $?   (error)"

no-such-command 2> /dev/null         # bash cannot find this command at all
echo "no-such-command          -> $?  (command not found)"

/etc/hostname 2> /dev/null           # the file exists but is not executable
echo "/etc/hostname            -> $?  (found, but not executable)"

sleep 10 &                           # start sleep in the background (lesson 13)
kill "$!"                            # send it the polite "please stop" signal (TERM = number 15)
wait "$!"                            # wait for it to finish and collect its exit code
echo "sleep killed by kill     -> $?  (128 + signal 15)"

( exit 42 )                          # ( ) runs commands in a mini copy of bash; exit 42 ends that copy with code 42
echo "( exit 42 )              -> $?   (you choose the number with exit)"
