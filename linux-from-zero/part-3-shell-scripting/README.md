# Part 3 · Shell scripting

**A script is your commands, saved in a file, so the computer can do the job for you.** In Parts 1 and 2 you typed commands one at a time. Here you write them down once, add variables, decisions, loops and safety checks, and end up with real tools: a backup program with options and help text, a folder organizer, a disk alarm, and jobs that run on a schedule while you sleep.

**Time:** about 1.5 weeks at 1 hour a day · **Before this part:** finish [Part 2 · Power tools](../part-2-power-tools) (especially [11 · Permissions](../part-2-power-tools/11-permissions-and-ownership), [14 · Environment variables and quoting](../part-2-power-tools/14-environment-variables-and-quoting) and [15 · Installing software](../part-2-power-tools/15-installing-software))

| # | Lesson | What you'll have at the end |
|---|--------|-----------------------------|
| 16 | [Your first script](16-your-first-script) | scripts with a shebang, `chmod +x`, your own command in `~/bin` |
| 17 | [Variables and arguments](17-variables-and-arguments) | scripts that take inputs: `$1`, `$@`, `$#`, `$(...)`, quoting done right |
| 18 | [Decisions and exit codes](18-decisions-and-exit-codes) | `if`, `[[ ]]` tests, `&&` / `\|\|`, and a disk alarm with proper exit codes |
| 19 | [Loops and functions](19-loops-and-functions) | `for`, `while`, `case`, functions, and a folder organizer with `--dry-run` |
| 20 | [Robust scripts](20-robust-scripts) | `set -euo pipefail`, `trap`, `getopts`, here-docs, and a professional backup tool |
| 21 | [Scheduling with cron and timers](21-scheduling-with-cron-and-timers) | jobs that run every minute / night with cron and systemd timers |

## Install once for this part
Everything you need comes with Ubuntu. Add the script "spell checker" once:
```bash
sudo apt update
sudo apt install shellcheck
```
- `sudo apt update`: refresh the list of available packages (lesson 15).
- `shellcheck`: reads a script and points out mistakes (missing quotes, unchecked `cd`...) with a link explaining each one.

Lesson 21's timer part needs a Linux that runs **systemd** (a normal Ubuntu install, a VM, or WSL2 with systemd switched on; lesson 21 shows how). In a Docker container, use the cron part of that lesson instead.

**Practice folders.** Lessons that need files ship a `setup.sh`. Run it with `bash setup.sh`; it only creates things inside `~/linux-practice/NN` (NN = the lesson number). You can delete `~/linux-practice` at any time and run the setups again.

**Self-checks.** Most lessons have a `check.sh`. Run `./check.sh` at the end: every line says `PASS` or `FAIL` with a hint.

## After this part you'll be able to
- Write a bash script from scratch, make it executable, and install it as your own command.
- Pass arguments to scripts, quote variables safely, and capture command output with `$(...)`.
- Make decisions with `if` and `[[ ]]`, and use exit codes so other tools know whether your script worked.
- Process lists of files and lines with loops, and organize code into functions.
- Write scripts that stop safely on errors, clean up after themselves, accept `-h`-style options, and have a dry-run mode.
- Schedule jobs with cron and systemd timers, and check that they really ran.

**Every lesson works the same way:** `cd` into its folder from the course folder (`linux-from-zero`), follow the numbered steps in "Run it", compare with "What you should see", then read the scripts alongside "How it works". Every line of every script is commented.

## Next
Start with → [16 · Your first script](16-your-first-script). When you finish lesson 21, go on to → [Part 4 · Servers and networking](../part-4-servers-and-networking).
