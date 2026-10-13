# 00 · Start here (zero experience needed)

You'll do this once. It takes about 30 minutes.

## 1. Install Python
- Go to https://www.python.org/downloads/ and click the big yellow **Download** button.
- **Windows:** in the installer, tick **"Add Python to PATH"** before clicking Install.
- **Mac:** just run the installer.

## 2. Install VS Code (where you'll read and edit code)
- https://code.visualstudio.com/ → install → open it → click the **Extensions** icon (four squares on the left) → search **Python** → Install.

## 3. Get these projects onto your computer
- Install Git: https://git-scm.com/downloads
- Open a **terminal** (a window where you type commands):
  - Windows: press the Start key, type `PowerShell`, press Enter.
  - Mac: press Cmd+Space, type `Terminal`, press Enter.
- Type these lines one at a time, pressing Enter after each:
  ```bash
  git clone https://github.com/SVashishta1/Learning.git
  cd Learning/ai-from-zero
  ```

## 4. Make a "virtual environment"
It's a private box for this course's add-ons, so they don't mess up your computer.
```bash
python -m venv .venv
```
Then turn it on. **Do this every time you open a new terminal:**
- Windows: `.venv\Scripts\activate`
- Mac: `source .venv/bin/activate`

You'll see `(.venv)` at the start of the line. That means it worked.
(On a Mac, if `python` isn't found, use `python3` instead.)

## 5. Run your first program
```bash
python 00-start-here/hello.py
```
If you see a greeting, **you're ready.** 🎉

## Terminal cheat sheet
| You type | It does |
|----------|---------|
| `cd folder-name` | go into a folder |
| `cd ..` | go back up one folder |
| `ls` (Mac) or `dir` (Windows) | list what's in this folder |
| `python file.py` | run a Python file |
| `pip install something` | download an add-on (a "package") |
| `Ctrl + C` | stop a running program |
| ↑ arrow key | repeat your last command |

## How every project works
Each folder has **one main file** and a short README:
1. **Run it** (copy the commands).
2. **Look at what it prints.**
3. **Open the file in VS Code** and read the comments (lines starting with `#`). They explain each step in plain English.
4. Do one **Try this** change. Breaking things is how you learn. You can't hurt your computer.

Stuck on an error? Copy the **last line** of the red text into Google or ask Claude. That's what professionals do too.
