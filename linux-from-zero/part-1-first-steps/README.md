# Part 1 · First steps

**The terminal is a conversation with your computer.** In this part you get a Linux terminal (on Windows, Mac, Linux or in Docker), learn the grammar every command follows, find your way around the folder tree, create and tidy files, read logs, look up any command yourself, and edit files with nano and vim.

**Time:** about 1 week at 1 hour a day · **Before this part:** nothing. Start with lesson 01.

| # | Lesson | What you'll have at the end |
|---|--------|-----------------------------|
| 01 | [What is Linux and the terminal](01-what-is-linux-and-the-terminal) | a working Linux terminal, the course files, and your first 10 commands |
| 02 | [Anatomy of a command](02-anatomy-of-a-command) | the skill to split any command into name, options and arguments |
| 03 | [Moving around the filesystem](03-moving-around-the-filesystem) | a treasure hunt solved with absolute and relative paths |
| 04 | [Creating, copying, moving, deleting](04-creating-copying-moving-deleting) | a messy downloads folder tidied with `mkdir`, `cp`, `mv`, `rm` and wildcards |
| 05 | [Reading files](05-reading-files) | logs, CSVs and mystery files read with `cat`, `less`, `head`, `tail -f`, `wc`, `file` |
| 06 | [Getting help](06-getting-help) | the habit of answering your own questions with `man`, `--help` and `help` |
| 07 | [Editing files with nano and vim](07-editing-files-with-nano-and-vim) | a config file edited in vim, and the confidence to quit it |

## Install once for this part
Lesson 01 walks you through it. In short, on Ubuntu, WSL or Docker:
```bash
sudo apt update
sudo apt install -y git curl nano vim less man-db tree file
git clone https://github.com/SVashishta1/Learning.git ~/Learning
```
- `git`: downloads this course. `curl`: downloads from web addresses.
- `nano`, `vim`: terminal text editors (lesson 07).
- `less`: page-by-page file viewer (lesson 05). `man-db`: the manual (lesson 06).
- `tree`: draws folders as a tree (lesson 03). `file`: says what kind of file something is (lesson 05).

On a Mac: `xcode-select --install`, then `brew install tree nano` (lesson 01, Option B).

## How every lesson works
1. Go to the course folder: `cd ~/Learning/linux-from-zero`.
2. If the lesson has a `setup.sh`, run it: `bash part-1-first-steps/<lesson>/setup.sh`. It builds a practice folder in `~/linux-practice/<number>` and never touches anything else. Run it again any time to start fresh.
3. Follow "Run it" step by step and compare with the outputs shown.
4. Run the lesson's `check.sh` the same way. It prints ✅ or ❌ for each task or quiz question, with a hint for every ❌.

## After this part you'll be able to
- Open a terminal on any computer and read the prompt (who, where, which machine, root or not).
- Read any command: name, short and long options, arguments, quotes, `;` and `&&`.
- Move anywhere with `cd`, absolute and relative paths, `~`, `.`, `..` and `-`, and know what lives in `/etc`, `/var/log`, `/home` and `/tmp`.
- Create, copy, move, rename and delete files and folders safely, using wildcards and brace expansion.
- Read files of any size, follow a live log with `tail -f`, and count lines.
- Look things up in `man` pages, `--help` and `help`, and check an AI's suggestion before running it.
- Edit files in nano and vim, and always find the way out.

## Next
Start with → [01 · What is Linux and the terminal](01-what-is-linux-and-the-terminal). When you finish lesson 07, go on to → [Part 2 · Power tools](../part-2-power-tools).
