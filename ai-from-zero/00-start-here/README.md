# 00 · Start here

**What you'll build:** a working setup on your own computer (Python 3.12, a code editor, the course files and a "virtual environment"), proved by running your first Python file, `hello.py`.
**Time:** ~45 min (once) · **Builds on:** nothing · **Needs:** a Windows, Mac or Linux computer with internet and about 3 GB of free disk space

Like you're 10: before you can bake, you need a kitchen. This lesson sets up the kitchen. Every other lesson cooks in it.

## Why this matters
Every lesson in this course is a Python program that you run from a **terminal**. Professional AI engineers work exactly like this every day: a terminal, an editor, Python, and one virtual environment per project. If this setup works, everything after it will work. If you skip a step here, you will hit confusing errors later, so take your time.

## What you'll learn
- **Python**: the programming language used for almost all AI work. You install it once.
- **Terminal**: a window where you type commands instead of clicking. You'll use it to run every lesson.
- **Code editor (VS Code)**: a free app for reading and editing code, with colours and helpful hints.
- **Virtual environment (venv)**: a private box for this course's add-ons, so they don't clash with anything else on your computer.
- **Running a file**: `python hello.py` tells Python to read the file and do what it says, line by line.

## Before you start
You don't need any software yet. You need to know two skills: opening a terminal, and copying commands into it.

### How to open a terminal
| Your computer | What to do |
|---|---|
| **Windows 11 / 10** | Press the **Windows key**, type `Terminal` (or `PowerShell` on older Windows 10), press **Enter**. |
| **Mac** | Press **Cmd + Space**, type `Terminal`, press **Enter**. |
| **Linux (Ubuntu and most others)** | Press **Ctrl + Alt + T**, or open your apps menu and search for `Terminal`. |

A window opens with a blinking cursor. That's the terminal. It starts in your **home folder** (on Windows something like `C:\Users\YourName`, on Mac/Linux `/Users/yourname` or `/home/yourname`).

### How to copy commands into the terminal
In these READMEs, commands are in grey boxes like this:
```bash
python --version
```
1. **Copy:** on GitHub, move your mouse over the grey box and click the **copy icon** in its top-right corner. Or select the text with your mouse and press **Ctrl + C** (Mac: **Cmd + C**).
2. **Paste into the terminal:** Windows: **Ctrl + V** or right-click. Mac: **Cmd + V**. Linux: **Ctrl + Shift + V** (plain Ctrl + V does not work in most Linux terminals).
3. Press **Enter** to run it.

Rules that save a lot of confusion:
- Run **one line at a time**, and wait until the previous one finishes (you get a fresh prompt line back).
- If a box shows `$` or `>` at the start of a line, **don't type that symbol**. It's the terminal's prompt, not part of the command.
- Lines starting with `#` inside a command box are notes for you. You don't need to run them.
- Copying text **out of** the terminal: select it, then **Ctrl + Shift + C** (Windows Terminal and Linux) or **Cmd + C** (Mac). In a terminal, plain Ctrl + C means "stop the program", not "copy".

### Terminal cheat sheet
| You type | It does |
|----------|---------|
| `cd folder-name` | go into a folder ("change directory") |
| `cd ..` | go back up one folder |
| `ls` (Mac/Linux) or `dir` (Windows) | list what's in this folder |
| `pwd` | show which folder you're in right now |
| `python file.py` | run a Python file |
| `pip install something` | download an add-on (a "package") into your venv |
| `Ctrl + C` | stop a running program |
| ↑ arrow key | bring back your last command |
| `Tab` key | finish a folder or file name for you (type `cd part` then press Tab) |

## Run it
Do these steps in order. Each one says what you should see, so you know it worked before you move on.

### 1. Install Python 3.12
The course is tested with **Python 3.12**. Python 3.10, 3.11 or 3.13 usually work too, but 3.12 is the safe choice because every AI package in the course supports it.

**Windows**
1. Open https://www.python.org/downloads/release/python-31210/ , scroll down to **Files**, and click **Windows installer (64-bit)**. (This is the newest 3.12 that has a ready-made installer.)
2. Run the downloaded file. On the first screen, **tick "Add python.exe to PATH"** at the bottom. This is the most important click of the whole setup.
3. Click **Install Now**, wait, then click **Close**.
   (Alternative if you like the terminal: run `winget install -e --id Python.Python.3.12` in a terminal.)
4. **Close the terminal and open a new one** (new terminals see the new install; old ones don't), then check:
   ```bash
   py -3.12 --version
   ```
   You should see `Python 3.12.10` (or another 3.12.x).

**Mac**
1. Open https://www.python.org/downloads/release/python-31210/ , scroll down to **Files**, and click **macOS 64-bit universal2 installer**.
2. Open the downloaded `.pkg` file and click **Continue / Agree / Install** until it finishes.
   (Alternative if you use Homebrew: `brew install python@3.12`.)
3. Open a **new** terminal and check:
   ```bash
   python3.12 --version
   ```
   You should see `Python 3.12.10` (or another 3.12.x).

**Linux**
- **Ubuntu 24.04, Linux Mint 22, Pop!_OS 24.04** already come with Python 3.12. Add the venv and pip tools, plus Git:
  ```bash
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip git
  python3 --version
  ```
  `sudo` asks for your computer password. Nothing appears while you type it; that's normal. Press Enter.
- **Fedora:** `sudo dnf install -y python3.12 git`, then check with `python3.12 --version`.
- **Older Ubuntu (22.04)** ships Python 3.10, which also works with this course. Use `python3` wherever this guide says `python3.12`.

### 2. Install VS Code (your code editor)
1. Go to https://code.visualstudio.com/ and click the big **Download** button for your system.
   - Windows: run the installer. Tick **"Add to PATH"** and **"Add 'Open with Code' action"** when offered.
   - Mac: open the downloaded zip and drag **Visual Studio Code** into your **Applications** folder.
   - Linux: download the `.deb` (Ubuntu/Mint) or `.rpm` (Fedora) file and double-click it, or run `sudo snap install code --classic`.
2. Open VS Code. Click the **Extensions** icon on the left (four little squares), search **Python**, and install the one **by Microsoft**.

Prefer another editor? PyCharm Community Edition (free) or any text editor is fine. This guide uses VS Code because it's free, works on all three systems and has a built-in terminal.

### 3. Get the course files onto your computer
**Option A: with Git (recommended, makes updating easy)**
1. Install Git:
   - Windows: download from https://git-scm.com/downloads/win and click **Next** through the installer (the default choices are fine). Then open a **new** terminal.
   - Mac: type `git --version` in the terminal. If Git is missing, a window offers to install the "command line developer tools". Click **Install** and wait.
   - Linux: you installed it in step 1 (`git` was in the install line).
2. In the terminal, run these two lines, one at a time:
   ```bash
   git clone https://github.com/SVashishta1/Learning.git
   cd Learning/ai-from-zero
   ```
   You should see `Cloning into 'Learning'...` and then a prompt that ends in `ai-from-zero`.

**Option B: without Git**
1. Open https://github.com/SVashishta1/Learning , click the green **Code** button, then **Download ZIP**.
2. Unzip it (Windows: right-click → **Extract All**; Mac: double-click). Move the `Learning-main` folder into your home folder.
3. In the terminal: `cd Learning-main/ai-from-zero`

From now on, **"the course folder"** means this `ai-from-zero` folder. Every lesson's commands start from here.

### 4. Check you're in the course folder
```bash
ls
```
(Windows: `dir`.) You should see `00-start-here`, `part-1-apis`, `part-2-machine-learning` and the other parts. If you don't, you're in the wrong folder: see "If something goes wrong" below.

### 5. Make a virtual environment
This creates a folder called `.venv` holding a private copy of Python for the course. You do this **once**.

| Your computer | Command |
|---|---|
| Windows | `py -3.12 -m venv .venv` |
| Mac | `python3.12 -m venv .venv` |
| Linux | `python3 -m venv .venv` (or `python3.12 -m venv .venv` on Fedora) |

It takes a few seconds and prints nothing. Nothing printed = it worked.

### 6. Switch the virtual environment on
Do this **every time you open a new terminal** for the course (from the course folder):

| Your computer | Command |
|---|---|
| Windows (PowerShell / Terminal) | `.venv\Scripts\Activate.ps1` |
| Windows (old Command Prompt) | `.venv\Scripts\activate.bat` |
| Mac and Linux | `source .venv/bin/activate` |

You'll see `(.venv)` at the start of the prompt line. That means it worked. While it's on, just type **`python`** and **`pip`** on every system (no `3`, no `py`): they point to the venv's Python 3.12.

Then update pip, the tool that installs add-ons:
```bash
python -m pip install --upgrade pip
```

### 7. Run your first program
```bash
python 00-start-here/hello.py
```

### What you should see
```
Hello, future AI engineer! Python works on your computer. 🎉
  Part 1: APIs
  Part 2: machine learning
  Part 3: neural networks
  Part 4: chatbots
  Part 5: RAG
  Part 6: AI agents
double(21) = 42

Your Python version: 3.12.15
✅ Python version is fine.
✅ Your virtual environment (.venv) is switched on.
```
Look at the last two lines. Two green ticks mean **you're ready**. 🎉 (Your version's last number may differ, e.g. `3.12.10`. That's fine.) If a line starts with ⚠️, it tells you what to fix.

### 8. Open the course in VS Code
1. In VS Code: **File → Open Folder...** and choose the `ai-from-zero` folder (inside `Learning`). If it asks "Do you trust the authors?", click **Yes**.
2. Press **Ctrl + Shift + P** (Mac: **Cmd + Shift + P**), type `Python: Select Interpreter`, and choose the one with **`.venv`** in it.
3. Open VS Code's own terminal: **View → Terminal** (or **Ctrl + `**, the key above Tab). It opens already inside the course folder and usually switches the venv on for you. If you don't see `(.venv)`, run the step 6 command.
4. Click `00-start-here/hello.py` in the left panel to read it.

**Your routine for every future session:** open the terminal (VS Code's is easiest) → make sure you're in the course folder → switch on the venv (step 6) → follow the lesson's README.

## How it works
**The setup.** Python is the program that understands `.py` files. The terminal is how you tell it which file to run. The venv is a folder (`.venv`) with its own Python and its own add-ons; "switching it on" just makes `python` and `pip` in this terminal point into that folder. That's why you see `(.venv)` and why you must switch it on in every new terminal.

```
you type:  python 00-start-here/hello.py
              │            │
              │            └── which file to run (a path from the course folder)
              └── the venv's Python 3.12 reads the file and runs it top to bottom
```

**The file, `hello.py`, top to bottom:**
1. Lines starting with `#` are **comments**: notes for humans that Python ignores. Every lesson explains itself in comments like these.
2. `import sys` borrows a ready-made **module** (a toolbox of code). `sys` knows facts about the running Python.
3. `name = "future AI engineer"` makes a **variable**: a labelled box holding a value. `print(f"Hello, {name}!...")` shows text; the `f` before the quotes lets `{name}` be replaced by the box's contents.
4. `skills = [...]` is a **list** (many values in order). `for number, skill in enumerate(skills, start=1):` is a **loop**: the indented line under it runs once per item, with `number` counting 1, 2, 3...
5. `def double(x): return x * 2` defines a **function**: a reusable recipe. `double(21)` runs it with `x = 21` and gives back `42`.
6. The setup check reads `sys.version_info` (your Python version) and compares it to `(3, 10)`. Then it compares `sys.prefix` (where the running Python keeps its add-ons) with `sys.base_prefix` (the main install). Inside a venv they differ, so the script can tell whether your venv is on.

**Indentation matters.** In Python, the spaces at the start of a line decide what belongs to a loop, `if` or function. VS Code handles this for you when you press Enter after a line ending in `:`.

**How every lesson in this course works:**
1. Read the lesson README's **Before you start** and run its install line (once per part).
2. **Run it** by copying the commands.
3. Compare with **What you should see**.
4. Open the code file in VS Code and read the comments while you read **How it works**.
5. Do the **Try this** exercises. Breaking things is how you learn; you can't hurt your computer.
6. Answer **Check yourself** before moving on.

## If something goes wrong
- **`python` / `py` / `python3.12` is "not recognized" or "command not found"** → you opened the terminal before installing, so open a **new** terminal. On Windows, if it still fails, run the installer again, choose **Modify**, and make sure "Add Python to environment variables" is ticked. On Windows, also check you used `py -3.12` (not `python3.12`) and on Mac `python3.12` (not `py`).
- **Windows: typing `python` opens the Microsoft Store** → Windows has a fake "python" shortcut. Use `py -3.12` for step 5. After step 6, `python` works because the venv's Python comes first. (You can also turn the shortcut off: Settings → Apps → Advanced app settings → App execution aliases → switch off `python.exe` and `python3.exe`.)
- **Windows: `Activate.ps1 cannot be loaded because running scripts is disabled on this system`** → run this once, type `Y` if asked, then activate again:
  ```bash
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- **Linux: `The virtual environment was not created successfully because ensurepip is not available`** → run `sudo apt install -y python3-venv` (or `python3.12-venv`), delete the half-made folder with `rm -rf .venv`, and repeat step 5.
- **`can't open file '...hello.py': [Errno 2] No such file or directory`** → you're not in the course folder. Run `pwd` to see where you are, then `cd` into `Learning/ai-from-zero` (or `Learning-main/ai-from-zero`) and try again.
- **`ModuleNotFoundError: No module named '...'` in any later lesson** → your venv is off (no `(.venv)` at the start of the line) or you skipped the lesson's install line. Switch it on (step 6), run the install line, run the file again.

Stuck on an error not listed here? Copy the **last line** of the error into a search engine or ask Claude. That's what professionals do too.

## Try this
1. Change `name` to your own name, save the file (**Ctrl + S** / **Cmd + S**), and run it again.
2. Add `"vector databases"` to the `skills` list and run it. How many parts does it print now? Why did you not have to change the loop?
3. Write a new function `square(x)` that returns `x * x`, and print `square(12)`.

<details><summary>Hints and solutions</summary>

1. Line 4 becomes `name = "Sam"` (with your name). The greeting changes.
2. It prints 7 lines. The `for` loop runs once per item in the list, however long the list is.
3. Add under the `double` function:
   ```python
   def square(x):
       return x * x


   print("square(12) =", square(12))
   ```
   You should see `square(12) = 144`.
</details>

## Check yourself
1. You open a brand new terminal tomorrow and want to run a lesson. What two things must you do before `python ...` works properly?
2. Why do we make a virtual environment instead of installing add-ons straight into the main Python?
3. In `hello.py`, what does the loop's `enumerate(skills, start=1)` give you on each turn?
4. You see `ModuleNotFoundError: No module named 'fastapi'`. What is the most likely cause?

<details><summary>Answers</summary>

1. Go into the course folder (`cd Learning/ai-from-zero`) and switch the venv on (step 6), so you see `(.venv)`.
2. It keeps the course's add-ons (and their exact versions) in one private folder. Other projects can't break it, it can't break them, and you can delete `.venv` and rebuild it if it ever gets messy.
3. A pair: a counting number (1, 2, 3...) and the next item from the list.
4. The venv is off, or you haven't run that part's `pip install` line yet in this venv.
</details>

## Learn more (optional)
- Official Python tutorial (the first 3 chapters are enough for now): https://docs.python.org/3/tutorial/
- Python in VS Code, official guide: https://code.visualstudio.com/docs/python/python-tutorial
- Virtual environments explained: https://docs.python.org/3/tutorial/venv.html
- Video: search YouTube for "Python for beginners" (for example the free full courses from freeCodeCamp or Programming with Mosh).

## Next
→ [01 · Your first API](../part-1-apis/01-your-first-api) (the [Part 1 overview](../part-1-apis) has the install line for the whole part)
