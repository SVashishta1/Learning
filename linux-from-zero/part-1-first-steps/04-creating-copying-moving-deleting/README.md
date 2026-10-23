# 04 · Creating, copying, moving, deleting

**What you'll build:** you'll tidy a messy `downloads` folder into neat `pictures`, `documents` and `music` folders, make a full backup copy, and delete the junk, all by typing. A check script ticks off each job.
**Time:** ~60 min · **Builds on:** [03 · Moving around the filesystem](../03-moving-around-the-filesystem) · **Needs:** nothing extra

**Like you're 5:** you're tidying your bedroom. `mkdir` builds a new toy box, `touch` puts an empty sticky note in it, `cp` photocopies a drawing, `mv` carries a toy to another box (or writes a new name on it), and `rm` throws something in a bin that is emptied straight away.

## Why this matters
Real work on a server is mostly this: create a folder for an app, copy a config file before you change it, move a new version into place, rename a log, delete old files that fill the disk. Deployment scripts, Dockerfiles (`COPY`, `RUN mkdir`) and CI pipelines are full of these exact commands. And because the terminal has **no recycle bin**, knowing how to delete *safely* protects your data.

## What you'll learn
- **`mkdir` and `mkdir -p`**: make one folder, or a whole chain of folders at once.
- **`touch`**: create an empty file (or update the "last changed" time of an existing one).
- **`cp`, `cp -r`**: copy files, and copy folders with everything inside.
- **`mv`**: move *and* rename; they're the same operation.
- **`rm`, `rm -r`, `rmdir`**: delete files, folders with contents, and empty folders, plus safety options `-i` (ask first) and `-v` (say what you did).
- **Wildcards (globs)**: `*` (anything), `?` (exactly one character), `[abc]` (one of these), and **brace expansion** `{a,b,c}` (make a list).

## Before you start
- Finish [lesson 03](../03-moving-around-the-filesystem).
- No install, no API key. `setup.sh` only creates `~/linux-practice/04`. You can run it again to undo all your changes and start over.

## Run it
1. Go to the course folder:
   ```bash
   cd ~/Learning/linux-from-zero
   ```
2. Build the messy folder:
   ```bash
   bash part-1-first-steps/04-creating-copying-moving-deleting/setup.sh
   ```
   ```
   Practice folder ready: /home/sam/linux-practice/04
   Messy files are in: /home/sam/linux-practice/04/downloads
   ```
3. Go to the practice folder (you'll stay here until step 19):
   ```bash
   cd ~/linux-practice/04
   ```
4. Look at the mess:
   ```bash
   ls downloads
   ```
   ```
    cat.png          holiday-03.jpg      notes.txt   temp-1.tmp
    cv.docx          invoice-april.pdf   old-stuff   temp-2.tmp
    holiday-01.jpg   invoice-march.pdf   song1.mp3   temp-3.tmp
    holiday-02.jpg  'my essay.docx'      song2.mp3
   ```
5. Make the new folders. First one folder:
   ```bash
   mkdir organized
   ```
   | Piece | Meaning |
   |---|---|
   | `mkdir` | "make directory": create a new, empty folder |
   | `organized` | its name (a relative path, so it's made right here) |

   Now try to make a folder two levels deep in one go:
   ```bash
   mkdir organized/pictures/2026
   ```
   ```
   mkdir: cannot create directory ‘organized/pictures/2026’: No such file or directory
   ```
   It fails because `pictures` doesn't exist yet. The fix is `-p`. And instead of typing three commands for three folders, use **braces**. Preview what braces do with `echo`:
   ```bash
   echo organized/{pictures,documents,music}
   ```
   ```
   organized/pictures organized/documents organized/music
   ```
   Then do it for real:
   ```bash
   mkdir -p organized/{pictures,documents,music}
   ```
   | Piece | Meaning |
   |---|---|
   | `-p` | "parents": also create any missing folders on the way, and don't complain if the folder already exists |
   | `{pictures,documents,music}` | **brace expansion**: the shell turns this into three words, `organized/pictures organized/documents organized/music`, *before* `mkdir` runs. No spaces after the commas! |

   Check: `ls organized` shows `documents  music  pictures`.
6. Create an empty file:
   ```bash
   touch organized/README.txt
   ls -l organized
   ```
   ```
   total 12
   -rw-r--r-- 1 sam sam    0 Oct 22 09:00 README.txt
   drwxr-xr-x 2 sam sam 4096 Oct 22 09:00 documents
   drwxr-xr-x 2 sam sam 4096 Oct 22 09:00 music
   drwxr-xr-x 2 sam sam 4096 Oct 22 09:00 pictures
   ```
   | Piece | Meaning |
   |---|---|
   | `touch` | create the file if it doesn't exist (size `0`); if it does exist, just update its "last changed" time. It never erases content |
   | `organized/README.txt` | the file to create |

7. Before moving many files, **preview a wildcard** with `echo`:
   ```bash
   echo downloads/*.jpg
   ```
   ```
   downloads/holiday-01.jpg downloads/holiday-02.jpg downloads/holiday-03.jpg
   ```
   | Piece | Meaning |
   |---|---|
   | `*` | "any characters, any number of them (even none)". The shell replaces `downloads/*.jpg` with every matching name *before* the command runs |
   | `.jpg` | the names must end in `.jpg` |

   This habit (try with `echo` first) saves you from moving or deleting the wrong files.
8. **Move** the pictures:
   ```bash
   mv downloads/*.jpg organized/pictures/
   mv -v downloads/cat.png organized/pictures/
   ```
   ```
   renamed 'downloads/cat.png' -> 'organized/pictures/cat.png'
   ```
   | Piece | Meaning |
   |---|---|
   | `mv` | "move": take the files from where they are and put them somewhere else (nothing is copied; they leave the old place) |
   | `downloads/*.jpg` | the **sources**: all `.jpg` files in `downloads` (three files after expansion) |
   | `organized/pictures/` | the **destination** (always the LAST argument). The trailing `/` says "this is a folder" |
   | `-v` | "verbose": print what was done. `mv` calls it "renamed" because a move *is* a rename of the path |

   `ls organized/pictures` → `cat.png  holiday-01.jpg  holiday-02.jpg  holiday-03.jpg`.
9. Move the documents (two wildcards in one command):
   ```bash
   mv downloads/*.pdf downloads/*.docx organized/documents/
   ls organized/documents
   ```
   ```
    cv.docx   invoice-april.pdf   invoice-march.pdf  'my essay.docx'
   ```
   The file with a space moved fine: wildcards handle spaces safely.
10. **Rename** a file. Renaming is just `mv` to a new name in the same folder:
    ```bash
    mv organized/documents/cv.docx organized/documents/cv-2026.docx
    ```
    | Piece | Meaning |
    |---|---|
    | `organized/documents/cv.docx` | the old name |
    | `organized/documents/cv-2026.docx` | the new name. If a file with that name already existed, `mv` would silently **replace** it |

11. Move the music:
    ```bash
    mv downloads/*.mp3 organized/music/
    ```
12. **Copy** the notes (keep the original):
    ```bash
    cp downloads/notes.txt organized/documents/
    ls downloads organized/documents
    ```
    ```
    downloads:
    notes.txt  old-stuff  temp-1.tmp  temp-2.tmp  temp-3.tmp

    organized/documents:
     cv-2026.docx        invoice-march.pdf   notes.txt
     invoice-april.pdf  'my essay.docx'
    ```
    | Piece | Meaning |
    |---|---|
    | `cp` | "copy": make a duplicate; the original stays |
    | `downloads/notes.txt` | the source |
    | `organized/documents/` | the destination folder (keeps the name `notes.txt`). Give a file name instead, like `organized/documents/notes-copy.txt`, to copy under a new name |

13. **Delete** the temp files. Preview first:
    ```bash
    echo downloads/temp-?.tmp
    ```
    ```
    downloads/temp-1.tmp downloads/temp-2.tmp downloads/temp-3.tmp
    ```
    ```bash
    rm downloads/temp-?.tmp
    ls downloads
    ```
    ```
    notes.txt  old-stuff
    ```
    | Piece | Meaning |
    |---|---|
    | `rm` | "remove": delete files. **There is no recycle bin.** Gone is gone |
    | `?` | exactly ONE character. `temp-?.tmp` matches `temp-1.tmp` but not `temp-10.tmp` |

14. Try to delete the `old-stuff` folder the "wrong" ways, to see the guard rails:
    ```bash
    rmdir downloads/old-stuff
    ```
    ```
    rmdir: failed to remove 'downloads/old-stuff': Directory not empty
    ```
    ```bash
    rm downloads/old-stuff
    ```
    ```
    rm: cannot remove 'downloads/old-stuff': Is a directory
    ```
    | Piece | Meaning |
    |---|---|
    | `rmdir` | "remove directory": deletes a folder only if it's **empty**. Safe by design |
    | `rm` (no options) | deletes files only, never folders |

15. Delete the folder and everything inside it:
    ```bash
    rm -r downloads/old-stuff
    ```
    | Piece | Meaning |
    |---|---|
    | `-r` | "recursive": go into the folder, delete everything inside, then the folder itself |

    You'll see `rm -rf` online. `-f` means "force: never ask, ignore files that don't exist". `rm -rf` with a wrong path (or a space in the wrong place, like `rm -rf / home/sam/old`) can wipe everything you own. Read it twice before pressing Enter, or use `-i`.
16. **Back up** the whole organized folder. `cp` needs `-r` for folders, too:
    ```bash
    cp organized organized-backup
    ```
    ```
    cp: -r not specified; omitting directory 'organized'
    ```
    ```bash
    cp -r organized organized-backup
    ```
    | Piece | Meaning |
    |---|---|
    | `-r` | recursive: copy the folder and everything in it |
    | `organized-backup` | the new folder's name. (If `organized-backup` already existed, the copy would go *inside* it as `organized-backup/organized`) |

17. Admire your work:
    ```bash
    tree
    ```
    ```
    .
    ├── downloads
    │   └── notes.txt
    ├── organized
    │   ├── README.txt
    │   ├── documents
    │   │   ├── cv-2026.docx
    │   │   ├── invoice-april.pdf
    │   │   ├── invoice-march.pdf
    │   │   ├── my essay.docx
    │   │   └── notes.txt
    │   ├── music
    │   │   ├── song1.mp3
    │   │   └── song2.mp3
    │   └── pictures
    │       ├── cat.png
    │       ├── holiday-01.jpg
    │       ├── holiday-02.jpg
    │       └── holiday-03.jpg
    └── organized-backup
        ├── README.txt
        ├── documents
        │   ├── cv-2026.docx
        │   ├── invoice-april.pdf
        │   ├── invoice-march.pdf
        │   ├── my essay.docx
        │   └── notes.txt
        ├── music
        │   ├── song1.mp3
        │   └── song2.mp3
        └── pictures
            ├── cat.png
            ├── holiday-01.jpg
            ├── holiday-02.jpg
            └── holiday-03.jpg

    10 directories, 25 files
    ```
18. Meet the **safety options**. `cp` and `mv` silently overwrite a file that already exists. Add `-i` to be asked first (answer `n` and press Enter to say no):
    ```bash
    cp -i downloads/notes.txt organized/documents/notes.txt
    ```
    ```
    cp: overwrite 'organized/documents/notes.txt'? n
    ```
    ```bash
    rm -i downloads/notes.txt
    ```
    ```
    rm: remove regular file 'downloads/notes.txt'? n
    ```
    | Piece | Meaning |
    |---|---|
    | `-i` | "interactive": ask `y`/`n` before overwriting or deleting. Anything other than `y` means no |

    Keep `downloads/notes.txt`: the check looks for it.
19. Check your work:
    ```bash
    cd ~/Learning/linux-from-zero
    bash part-1-first-steps/04-creating-copying-moving-deleting/check.sh
    ```

### What you should see
After the steps above (before the Try this exercises), the ten "Run it" checks pass and the three "Try this" checks wait for you:
```
Checking ~/linux-practice/04 ...

Run it:
✅ organized/ has pictures, documents and music folders
✅ organized/README.txt exists
✅ the 3 holiday photos and cat.png are in organized/pictures
✅ the invoices and the essay are in organized/documents
✅ cv.docx was renamed to cv-2026.docx
✅ both songs are in organized/music
✅ notes.txt was COPIED (it's in downloads AND organized/documents)
✅ the .tmp files are deleted
✅ downloads/old-stuff is deleted
✅ organized-backup is a full copy of organized

Try this:
❌ 1. projects/2026/{jan,feb,mar} not found
   hint: mkdir -p projects/2026/{jan,feb,mar}
❌ 2. phone-upload/ should hold copies of the 3 holiday photos
   hint: mkdir phone-upload && cp organized/pictures/holiday-*.jpg phone-upload/
❌ 3. organized/documents/my-essay.docx not found
   hint: mv "organized/documents/my essay.docx" organized/documents/my-essay.docx

Result: 10 of 13 checks passed.
Fix the ❌ lines (each hint shows a command), then run the check again.
```
After the Try this exercises the last lines become `Result: 13 of 13 checks passed.` and `Tidy! You can create, copy, move and delete like a pro.` Messed something up? Run `setup.sh` again to start over.

## How it works
**Wildcards are expanded by the shell, not by the command.** When you type `mv downloads/*.jpg organized/pictures/`, `mv` never sees the `*`. The shell first swaps the pattern for the matching names, then starts `mv` with the full list:

```mermaid
flowchart LR
    A["You type:<br/>mv downloads/*.jpg organized/pictures/"] --> B["Shell expands the glob:<br/>looks in downloads/ for names ending .jpg"]
    B --> C["mv downloads/holiday-01.jpg<br/>downloads/holiday-02.jpg<br/>downloads/holiday-03.jpg<br/>organized/pictures/"]
    C --> D["mv moves each source<br/>into the LAST argument"]
```

1. **Wildcards (globs)** match existing file names:

   | Pattern | Matches | Example |
   |---|---|---|
   | `*` | any characters, any number | `*.pdf` → every name ending in `.pdf` |
   | `?` | exactly one character | `temp-?.tmp` → `temp-1.tmp`, not `temp-10.tmp` |
   | `[abc]` | one character from the set | `holiday-0[12].jpg` → `-01` and `-02` |
   | `[0-9]` | one character in the range | `song[0-9].mp3` |

   `*` does not match names starting with `.` (hidden files), so `rm *` leaves `.bashrc` alone. If nothing matches, bash leaves the pattern as it is, and the command then complains `No such file or directory` about a file literally named `*.xyz`.
2. **Braces are different from globs.** `{a,b,c}` makes a list whether files exist or not, which is why it can *create* folders. Globs only *find* things that exist. You can combine both: `mkdir -p projects/2026/{jan,feb,mar}`.
3. **`mv` is cheap, `cp` is real work.** Within the same disk, `mv` only changes the label (the path) of a file; it doesn't copy any data, so moving a 50 GB model file is instant. `cp` reads and writes every byte.
4. **Sources first, destination last.** `cp` and `mv` both take `SOURCE... DESTINATION`. With several sources, the destination must be an existing folder.

   | Command | If destination exists as a folder | If destination doesn't exist |
   |---|---|---|
   | `mv a.txt b` | moves `a.txt` into `b/` | renames `a.txt` to `b` |
   | `cp -r dir1 dir2` | copies to `dir2/dir1` | creates `dir2` as the copy |

5. **Deleting is permanent.** `rm` tells the system to forget the file; there's no undo. Safe habits: preview globs with `echo` (or `ls`) first; use `-i` when unsure; use `-v` to see what happened; prefer `rmdir` for folders you think are empty; never run `rm -rf` on a path you built from a variable you haven't checked (Part 3 shows how scripts guard against this).
6. **On a Mac:** all of these work the same. Small differences: messages are worded differently (no `renamed '...'` line from `mv -v`, it prints `a -> b`), and GNU's `rm -I` ("ask once before deleting more than three files") doesn't exist there.

## If something goes wrong
- **`mkdir: cannot create directory ‘a/b’: No such file or directory`** → the parent folder is missing. Add `-p`.
- **`mv: cannot stat 'downloads/*.jpg': No such file or directory`** → nothing matched: the files were already moved, or you're in the wrong folder (`pwd`). The literal `*` in the message is the clue that the glob matched nothing.
- **`cp: -r not specified; omitting directory`** → you tried to copy a folder. Add `-r`.
- **`rm: cannot remove 'x': Is a directory`** → use `rmdir x` (empty) or `rm -r x` (with contents).
- **`mkdir` made a strange folder like `{pictures,` or `{pictures,documents,music}`** → you typed a space after a comma (the space splits the braces into separate words), or ran the line with `sh` instead of `bash` (`sh` doesn't know braces). Delete it with quotes, for example `rm -r 'organized/{pictures,'`, and retype without spaces.
- **You deleted or moved the wrong thing** → run `setup.sh` again; it rebuilds the practice folder from scratch. (On your real files there's no such button: that's why you practise here.)

## Try this
1. Make the folders `projects/2026/jan`, `projects/2026/feb` and `projects/2026/mar` (inside `~/linux-practice/04`) with **one** command.
2. Make a folder `phone-upload` and **copy** (not move) the three holiday photos from `organized/pictures` into it with one `cp` and a wildcard.
3. Rename `organized/documents/my essay.docx` to `my-essay.docx` (names without spaces are easier in a terminal).

Then run the check again from the course folder.

<details><summary>Solutions</summary>

Run these from `~/linux-practice/04`:
1. `mkdir -p projects/2026/{jan,feb,mar}` (`-p` creates `projects` and `2026` on the way). Check with `tree projects`.
2. `mkdir phone-upload && cp organized/pictures/holiday-*.jpg phone-upload/` (`&&` = only copy if the folder was made). `cat.png` isn't copied because it doesn't match `holiday-*.jpg`.
3. `mv "organized/documents/my essay.docx" organized/documents/my-essay.docx` (quotes because of the space; or press Tab after `my` and the shell adds `my\ essay.docx` for you).
</details>

## Check yourself
1. What's the difference between `cp report.txt backup/` and `mv report.txt backup/`?
2. You run `rm *.log` in a folder with `app.log`, `.hidden.log` and `old.log.gz`. Which files are deleted?
3. Why does `mkdir -p a/b/c` succeed when `mkdir a/b/c` fails in an empty folder?
4. Your friend wants to rename every `.txt` file to `.md` with `mv *.txt *.md`. Why won't that work?

<details><summary>Answers</summary>

1. `cp` leaves `report.txt` where it is and puts a copy in `backup/`. `mv` takes the original away and puts it in `backup/`.
2. Only `app.log`. `*` doesn't match the hidden `.hidden.log`, and `old.log.gz` doesn't end in `.log`.
3. `-p` creates the missing parents `a` and `a/b` first. Without it, `mkdir` refuses because `a/b` doesn't exist.
4. The shell expands the globs before `mv` runs. `*.md` matches nothing (or existing `.md` files), so `mv` receives a list of `.txt` files and a last argument that isn't a folder, and fails with `mv: target '*.md': No such file or directory`. Renaming many files needs a loop (Part 3, lesson 19).
</details>

## Learn more (optional)
**Read the official docs**
- `mkdir`: https://man7.org/linux/man-pages/man1/mkdir.1.html
- `cp`: https://man7.org/linux/man-pages/man1/cp.1.html
- `mv`: https://man7.org/linux/man-pages/man1/mv.1.html
- `rm`: https://man7.org/linux/man-pages/man1/rm.1.html
- `touch`: https://man7.org/linux/man-pages/man1/touch.1.html
- Wildcards ("glob"): https://man7.org/linux/man-pages/man7/glob.7.html
- Brace expansion, GNU Bash manual: https://www.gnu.org/software/bash/manual/html_node/Brace-Expansion.html

**Watch**
- NetworkChuck, Linux for hackers (files and folders episodes): https://www.youtube.com/results?search_query=networkchuck+linux+for+hackers+files
- Linux cp, mv, rm, mkdir explained: https://www.youtube.com/results?search_query=linux+cp+mv+rm+mkdir+tutorial+beginners
- Wildcards and globbing in bash: https://www.youtube.com/results?search_query=bash+wildcards+globbing+explained

## Next
→ [05 · Reading files](../05-reading-files)
