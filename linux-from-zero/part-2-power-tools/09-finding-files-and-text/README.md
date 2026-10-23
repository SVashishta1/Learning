# 09 · Finding files and text

**What you'll build:** a pretend AI project full of code, logs, data and one hidden secrets file. You'll find files by name, type, size and age with `find`, and find text inside files with `grep`: every TODO, every ERROR, and the leaked API key.
**Time:** ~60 min · **Builds on:** [08 · Redirection and pipes](../08-redirection-and-pipes) · **Needs:** nothing extra

**Like you're 5:** `find` is a search dog that walks through every room of the house looking for things by their *label* (name, size, age). `grep` is a magnifying glass that reads *inside* every page and points at the lines with your word.

## Why this matters
Real projects have thousands of files. You'll need to find "where is that config file?", "which logs are eating my disk?", "which file calls the OpenAI API?", "where did someone paste an API key?", and "how many errors happened today?". `find` and `grep` answer these in seconds on any server, and they're the first tools you reach for when debugging someone else's system as a forward-deployed engineer.

## What you'll learn
- **`find PLACE TESTS`**: walks a folder tree and lists everything matching tests like `-name`, `-iname`, `-type`, `-size`, `-mtime`, `-empty`, `-maxdepth`.
- **Acting on results**: `-exec command {} \;` or `{} +`, and `-delete` (look before you delete!).
- **`grep PATTERN FILES`**: prints matching lines; options `-n` (line numbers), `-i` (ignore case), `-r` (search folders), `-v` (invert), `-c` (count), `-l` (file names only), `-w` (whole word), `-o` (only the match), `-A/-B/-C` (context), `--include`.
- **Regular expressions (regex)**: a tiny pattern language: `^` start of line, `$` end, `.` any character, `*` repeat, `[0-9]` a digit, `-E` with `|` for "or".
- **Quote your patterns**, so the shell doesn't expand `*` before `find` or `grep` sees it.

## Before you start
- Finish [lesson 08](../08-redirection-and-pipes): you'll pipe results into `wc -l` and save them with `>`.
- No install, no API key. `setup.sh` only creates `~/linux-practice/09`. (The "API key" in it is fake.)

## Run it
1. Go to the course folder and build the project:
   ```bash
   cd ~/Learning/linux-from-zero
   bash part-2-power-tools/09-finding-files-and-text/setup.sh
   ```
   ```
   Practice folder ready: /home/sam/linux-practice/09/project
   ```
2. Go there and look at the whole tree (hidden files too):
   ```bash
   cd ~/linux-practice/09/project
   tree -a
   ```
   ```
   .
   ├── .env
   ├── README.md
   ├── build
   ├── cache
   │   ├── a.tmp
   │   └── b.tmp
   ├── config
   │   └── settings.yaml
   ├── data
   │   ├── big-dataset.csv
   │   └── small.csv
   ├── logs
   │   ├── app-2026-03-14.log
   │   └── old
   │       └── app-2020-01-10.log
   ├── notes
   │   ├── IDEAS.TXT
   │   ├── Meeting Notes.txt
   │   └── todo.txt
   ├── src
   │   ├── app.py
   │   ├── models
   │   │   ├── chat.py
   │   │   └── embed.py
   │   └── utils.py
   └── tests
       └── test_app.py

   11 directories, 17 files
   ```

### Part A · find (search by name, type, size, age)
3. Find all Python files, at any depth:
   ```bash
   find . -name "*.py"
   ```
   ```
   ./src/models/chat.py
   ./src/models/embed.py
   ./src/app.py
   ./src/utils.py
   ./tests/test_app.py
   ```
   | Piece | Meaning |
   |---|---|
   | `find` | walk through folders and print every path that passes the tests |
   | `.` | where to start: here. Every folder below it is searched too |
   | `-name` | test: does the file's name match the pattern? (case-sensitive) |
   | `"*.py"` | the pattern: anything ending in `.py`. **Quotes are needed** so the shell passes the `*` to `find` instead of expanding it itself |

   The order is the order `find` meets things on disk, not alphabetical. Pipe into `sort` if you want it sorted.
4. Ignore capitals with `-iname`:
   ```bash
   find . -iname "*.txt"
   ```
   ```
   ./notes/todo.txt
   ./notes/IDEAS.TXT
   ./notes/Meeting Notes.txt
   ```
   | Piece | Meaning |
   |---|---|
   | `-iname` | like `-name`, but **i**gnoring upper/lower case. `-name "*.txt"` alone misses `IDEAS.TXT` |

5. Find only folders, or only files:
   ```bash
   find . -type d
   ```
   ```
   .
   ./src
   ./src/models
   ./config
   ./cache
   ./notes
   ./logs
   ./logs/old
   ./tests
   ./data
   ./build
   ```
   | Piece | Meaning |
   |---|---|
   | `-type d` | only **d**irectories (`-type f` = only regular **f**iles, `-type l` = only symbolic links) |

   Tests combine with "and": `find . -type f -name "*.log"` → `./logs/app-2026-03-14.log` and `./logs/old/app-2020-01-10.log`.
6. Find **big** files (great when a disk is full):
   ```bash
   find . -size +1M
   ```
   ```
   ./data/big-dataset.csv
   ```
   | Piece | Meaning |
   |---|---|
   | `-size +1M` | bigger than 1 megabyte. `+` = more than, `-` = less than; units `k` (kilobytes), `M`, `G` |

   `ls -lh data` confirms: `1.5M  big-dataset.csv`.
7. Find **old** files:
   ```bash
   find . -mtime +365
   ```
   ```
   ./logs/old/app-2020-01-10.log
   ```
   | Piece | Meaning |
   |---|---|
   | `-mtime +365` | **m**odified more than 365 days ago. `-mtime -1` = changed in the last day. (`setup.sh` back-dated this log to 2020 with `touch -t`) |

8. A few more useful tests:
   ```bash
   find . -empty
   ```
   ```
   ./build
   ```
   ```bash
   find . -maxdepth 1
   ```
   ```
   .
   ./.env
   ./src
   ./config
   ./cache
   ./notes
   ./README.md
   ./logs
   ./tests
   ./data
   ./build
   ```
   | Piece | Meaning |
   |---|---|
   | `-empty` | empty files and empty folders |
   | `-maxdepth 1` | don't go deeper than 1 level (put it before the other tests) |

   Notice `find` shows hidden files like `.env` without any extra option.
9. **Do something** with each result:
   ```bash
   find . -name "*.py" -exec wc -l {} +
   ```
   ```
     7 ./src/models/chat.py
     2 ./src/models/embed.py
    10 ./src/app.py
     3 ./src/utils.py
     4 ./tests/test_app.py
    26 total
   ```
   | Piece | Meaning |
   |---|---|
   | `-exec` | run a command on the results |
   | `wc -l` | the command to run (count lines) |
   | `{}` | placeholder: `find` puts the found path(s) here |
   | `+` | end of the command: put **many** paths into one `wc` run (that's why you get a `total`) |
   | `\;` | the other way to end it: run the command **once per path**. The `\` stops the shell treating `;` as "next command" |

10. **Delete** what you find, safely: first look, then delete.
    ```bash
    find cache -name "*.tmp"
    ```
    ```
    cache/a.tmp
    cache/b.tmp
    ```
    ```bash
    find cache -name "*.tmp" -delete
    ls cache
    ```
    (`ls cache` prints nothing: the folder is empty now.)

    | Piece | Meaning |
    |---|---|
    | `-delete` | delete each match. No bin, no "are you sure?". **Always run the same `find` without `-delete` first**, and put `-delete` last (if it comes before `-name`, it deletes everything) |

11. Search the **whole computer**, hiding the "Permission denied" noise (lesson 08):
    ```bash
    find / -name "os-release" 2>/dev/null
    ```
    ```
    /etc/os-release
    /usr/lib/os-release
    ```
    Searching from `/` reads every folder, so it can take a while on a big machine.

### Part B · grep (search inside files)
12. Find a word in one file, with line numbers:
    ```bash
    grep -n TODO src/app.py
    ```
    ```
    4:# TODO: add rate limiting
    ```
    | Piece | Meaning |
    |---|---|
    | `grep` | "global regular expression print": print every line that matches a pattern |
    | `-n` | put the line **n**umber in front (`4:`) |
    | `TODO` | the pattern to look for (case-sensitive) |
    | `src/app.py` | the file(s) to search |

13. Search a whole folder, recursively, ignoring case:
    ```bash
    grep -rni todo src
    ```
    ```
    src/models/chat.py:6:    # TODO: call the real model
    src/app.py:4:# TODO: add rate limiting
    src/utils.py:2:    # todo: handle emoji
    ```
    | Piece | Meaning |
    |---|---|
    | `-r` | **r**ecursive: search every file in the folder and its sub-folders |
    | `-n` | line numbers |
    | `-i` | **i**gnore case: `todo`, `TODO` and `ToDo` all match |
    | `src` | the folder to search |

    Each result reads `file:line:text`.
14. **Count** matching lines:
    ```bash
    grep -c ERROR logs/app-2026-03-14.log
    ```
    ```
    5
    ```
    Across a whole folder, pipe into `wc -l`:
    ```bash
    grep -r ERROR logs | wc -l
    ```
    ```
    7
    ```
    | Piece | Meaning |
    |---|---|
    | `-c` | **c**ount matching lines per file instead of printing them |
    | `\| wc -l` | count all printed lines together (lesson 08) |

    `grep -ri error logs | wc -l` gives `8`: the extra one is a `WARN` line that says "network error" in lowercase.
15. Which files mention something? Just the names:
    ```bash
    grep -rl requests .
    ```
    ```
    ./src/models/chat.py
    ./src/app.py
    ```
    | Piece | Meaning |
    |---|---|
    | `-l` | print only the names of files that contain a match (**l**ist) |

16. **Invert**: show the lines that do NOT match (hide the boring INFO lines):
    ```bash
    grep -v INFO logs/app-2026-03-14.log
    ```
    ```
    2026-03-14 10:06:00 ERROR chat: model timeout after 30s
    2026-03-14 10:12:00 ERROR chat: model timeout after 30s
    2026-03-14 10:13:00 WARN  chat: retrying after network error
    2026-03-14 10:18:00 ERROR chat: model timeout after 30s
    2026-03-14 10:24:00 ERROR chat: model timeout after 30s
    2026-03-14 10:30:00 ERROR chat: model timeout after 30s
    ```
    | Piece | Meaning |
    |---|---|
    | `-v` | in**v**ert: print lines that do *not* contain the pattern |

17. **Whole words** only:
    ```bash
    grep -n model src/app.py
    ```
    ```
    2:from models.chat import answer
    ```
    ```bash
    grep -nw model src/app.py
    ```
    (prints nothing)

    | Piece | Meaning |
    |---|---|
    | `-w` | match only the whole **w**ord: `model` no longer matches inside `models` |

18. **Patterns (regular expressions).** Lines that *start* with `import`:
    ```bash
    grep -n "^import" src/app.py src/models/chat.py
    ```
    ```
    src/app.py:1:import requests
    src/models/chat.py:1:import requests
    ```
    ERROR **or** WARN lines:
    ```bash
    grep -E "ERROR|WARN" logs/app-2026-03-14.log
    ```
    ```
    2026-03-14 10:06:00 ERROR chat: model timeout after 30s
    2026-03-14 10:12:00 ERROR chat: model timeout after 30s
    2026-03-14 10:13:00 WARN  chat: retrying after network error
    2026-03-14 10:18:00 ERROR chat: model timeout after 30s
    2026-03-14 10:24:00 ERROR chat: model timeout after 30s
    2026-03-14 10:30:00 ERROR chat: model timeout after 30s
    ```
    Only the matching part, not the whole line:
    ```bash
    grep -o "[0-9]* ms" logs/app-2026-03-14.log | head -n 3
    ```
    ```
    107 ms
    114 ms
    121 ms
    ```
    | Piece | Meaning |
    |---|---|
    | `^` | the start of a line (`^import` = lines beginning with "import") |
    | `$` | the end of a line (`)$` = lines ending with a `)`) |
    | `-E` | **E**xtended regex: allows `\|` (or), `+`, `?` and `( )` without backslashes |
    | `ERROR\|WARN` | "ERROR" or "WARN" |
    | `-o` | print **o**nly the matching text |
    | `[0-9]` | any one digit; `[0-9]*` = zero or more digits |
    | ` ms` | then a space and "ms" |

    Always put patterns in quotes: `|`, `*`, `$` and `^` mean something to the shell too.
19. **Context**: lines around a match:
    ```bash
    grep -A 2 "def answer" src/models/chat.py
    ```
    ```
    def answer(question):
        # TODO: call the real model
        return "I am a pretend model. You asked: " + question
    ```
    | Piece | Meaning |
    |---|---|
    | `-A 2` | also print 2 lines **A**fter each match. `-B 2` = **B**efore, `-C 2` = both (context) |

20. Limit a recursive search to some file types:
    ```bash
    grep -rn "TODO" --include="*.py" .
    ```
    ```
    ./src/models/chat.py:6:    # TODO: call the real model
    ./src/app.py:4:# TODO: add rate limiting
    ```
    | Piece | Meaning |
    |---|---|
    | `--include="*.py"` | only search files whose names match `*.py` (here it skips `notes/todo.txt`). `--exclude` does the opposite, `--exclude-dir=.git` skips a folder |

21. **Security check**: is there a secret in the project?
    ```bash
    grep -r API_KEY .
    ```
    ```
    ./.env:ANTHROPIC_API_KEY=pretend-key-123
    ```
    Found it in a hidden file. (`grep -r API_KEY *` finds nothing, because `*` skips hidden names: search `.` instead.) In real projects, `.env` files must never be committed to git or copied into Docker images; this one-liner is a quick audit.
22. Take the quiz (answer it in a second terminal inside `~/linux-practice/09/project`):
    ```bash
    cd ~/Learning/linux-from-zero
    bash part-2-power-tools/09-finding-files-and-text/check.sh
    ```

### What you should see
After the quiz, before the Try this exercises:
```
Lesson 09 quiz. Work in a second terminal, in ~/linux-practice/09/project.

1. How many .py files are in the project (all folders)?
> ✅ Correct: 5

2. Which file is bigger than 1 MB? (just its name)
> ✅ Correct: big-dataset.csv

3. How many lines of logs/app-2026-03-14.log contain ERROR (capitals)?
> ✅ Correct: 5

4. Which file holds the API key? (its name)
> ✅ Correct: .env

5. On which line number of src/app.py is the TODO?
> ✅ Correct: 4

Try this:
❌ 1. py-files.txt should list the 5 .py files
   hint: cd ~/linux-practice/09/project && find . -name "*.py" > ../py-files.txt
❌ 2. todo-report.txt should have 3 lines like src/app.py:4:# TODO...
   hint: grep -rni todo --include="*.py" . > ../todo-report.txt
❌ 3. delete ONLY logs older than a year
   hint: find logs -name "*.log" -mtime +365 (look first!), then add -delete

Result: 5 of 8 correct.
Use the hints, then run the check again. (setup.sh starts you over.)
```
After Try this: `Result: 8 of 8 correct.` and `You can find anything, anywhere. On to lesson 10!`

## How it works
**`find` looks at names and labels; `grep` reads contents.** They work great together.

```mermaid
flowchart LR
    Q{"What do you know?"} -->|"part of the NAME,<br/>type, size, age"| F["find . -name '*.log' -mtime +7"]
    Q -->|"some TEXT inside"| G["grep -rn 'timeout' ."]
    F -->|"-exec grep ... {} +<br/>or | xargs grep"| G
    G -->|"| wc -l"| C["a count"]
```

1. **How `find` works.** It starts at the folder you give it and visits every file and sub-folder below (a "walk"). For each one it checks your tests from left to right, joined by "and". If all pass, it runs the action: `-print` (the default), `-exec`, or `-delete`. Use `-o` for "or" and `!` for "not": `find . -name "*.py" ! -path "./tests/*"` (Python files outside `tests`).
2. **Why quote `"*.py"`?** Without quotes the shell expands `*.py` first (lesson 04). If the current folder has Python files, `find` receives their names instead of the pattern, and complains:
   ```
   sam@laptop:~/linux-practice/09/project/src$ find . -name *.py
   find: paths must precede expression: `utils.py'
   find: possible unquoted pattern after predicate `-name'?
   ```
3. **How `grep` works.** It reads each file line by line and prints the lines where the pattern matches. A **regular expression** is a small language for describing text:

   | Regex | Matches |
   |---|---|
   | `abc` | the letters `abc` anywhere in the line |
   | `.` | any single character (`c.t` matches `cat`, `cut`, `c t`) |
   | `*` | the thing before it, repeated 0 or more times (`lo*l` matches `ll`, `lol`, `looool`) |
   | `^` / `$` | start / end of the line |
   | `[abc]` / `[0-9]` / `[^0-9]` | one of these / one digit / one character that is NOT a digit |
   | `\.` | a real dot (the backslash turns off the special meaning) |
   | `x\|y` (with `-E`) | `x` or `y` |
   | `+` / `?` (with `-E`) | 1 or more / 0 or 1 of the thing before |

   Careful: regex `*` is not the same as the shell's glob `*`. In a glob `*` means "anything"; in a regex it means "repeat the previous character", and "anything" is `.*`.
4. **Exit codes.** `grep` also reports back whether it found something (0 = found, 1 = nothing found, 2 = error). Scripts use this to decide what to do next (lesson 18). `grep -q` prints nothing and only reports back.
5. **`-exec ... {} \;` vs `+`.** `\;` starts the command once per file (simple, slow for thousands of files). `+` packs as many paths as fit into one command (fast). Another common style is `find ... | xargs command`, but it breaks on names with spaces unless you use `find ... -print0 | xargs -0 command`.
6. **Other ways to find things.** `which python3` → `/usr/bin/python3` (where a command lives, lesson 14). `locate name` searches a pre-built index of the whole disk instantly (`sudo apt install plocate`; the index updates once a day). Faster modern tools you may meet: `fd` (for find) and `rg` / ripgrep (for grep).
7. **GNU vs Mac:** Mac `find` needs the starting folder (`find . -name ...`; GNU lets you leave out `.`). Mac `grep` is BSD grep: most options here work, but `grep -P` (Perl-style regex) does not, and `--include` behaves slightly differently. `find -delete`, `-mtime`, `-size`, `-empty` all work on both.

## If something goes wrong
- **`find: paths must precede expression`** → you forgot the quotes around the pattern: `find . -name "*.py"`.
- **`find: '/root': Permission denied` (lots of them)** → you searched folders you're not allowed to read. Add `2>/dev/null`, or search only your own folders.
- **`grep` prints nothing** → check case (`-i`), check you searched the right place (`-r` for folders), and remember `*` skips hidden files (use `.`).
- **`grep: src: Is a directory`** → you gave a folder without `-r`.
- **`grep -E "ERROR|WARN"` without quotes runs `WARN` as a command** → `|` outside quotes is a pipe. Keep patterns in quotes.
- **You deleted too much with `-delete`** → run `setup.sh` again here. On real files: always run the `find` without `-delete` first and read the list.

## Try this
1. Save the list of all `.py` files in the project to `~/linux-practice/09/py-files.txt`.
2. Save every TODO (any capitalisation) in `.py` files only, with file names and line numbers, to `~/linux-practice/09/todo-report.txt`.
3. Delete only the `.log` files older than one year from `logs/` (look first!). The new log must survive.

<details><summary>Solutions</summary>

From `~/linux-practice/09/project` (`..` is the folder above, `~/linux-practice/09`):
1. `find . -name "*.py" > ../py-files.txt`
2. `grep -rni todo --include="*.py" . > ../todo-report.txt`. `cat ../todo-report.txt` shows 3 lines, including `./src/utils.py:2:    # todo: handle emoji`.
3. Look: `find logs -name "*.log" -mtime +365` → `logs/old/app-2020-01-10.log`. Then: `find logs -name "*.log" -mtime +365 -delete`.
</details>

## Check yourself
1. What's the difference between `find . -name "*.py"` and `grep -r "\.py" .`?
2. Why does `grep -r API_KEY *` miss `.env` while `grep -r API_KEY .` finds it?
3. Write a command that prints all lines containing `timeout` in every `.log` file under `/var/log/myapp`, with line numbers, ignoring case.
4. Your disk is full. Which `find` command lists files over 500 MB in your home folder?

<details><summary>Answers</summary>

1. `find` lists files whose **names** end in `.py`. `grep` prints **lines inside files** that contain the text `.py`.
2. The shell expands `*` to the visible names only (names starting with `.` are skipped). `.` means "this folder", and `grep -r` then visits everything inside, hidden files included.
3. `grep -rni timeout --include="*.log" /var/log/myapp`
4. `find ~ -type f -size +500M` (add `-exec ls -lh {} +` to see their sizes).
</details>

## Learn more (optional)
**Read the official docs**
- `find`: https://man7.org/linux/man-pages/man1/find.1.html
- GNU findutils manual: https://www.gnu.org/software/findutils/manual/html_mono/find.html
- `grep`: https://man7.org/linux/man-pages/man1/grep.1.html
- GNU grep manual: https://www.gnu.org/software/grep/manual/grep.html
- Regular expressions (`regex(7)`): https://man7.org/linux/man-pages/man7/regex.7.html

**Watch**
- Linux find command tutorial: https://www.youtube.com/results?search_query=linux+find+command+tutorial
- grep tutorial for beginners: https://www.youtube.com/results?search_query=grep+command+tutorial+beginners
- Fireship, Regular expressions in 100 seconds: https://www.youtube.com/results?search_query=fireship+regex+in+100+seconds
- NetworkChuck, Linux for hackers (find and grep): https://www.youtube.com/results?search_query=networkchuck+linux+grep+find

## Next
→ [10 · Text processing: cut, sort, uniq, sed, awk](../10-text-processing-cut-sort-uniq-sed-awk)
