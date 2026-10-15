# 0.1 · Set up your AI workbench

**What you'll build:** a working Python setup (Python, Git, VS Code, a virtual environment) and a checker script that tells you what's installed.
**Like you're 10:** before cooking, you set up the kitchen: knives, pans and ingredients within reach. Then every recipe after this "just works".
**Time:** ~30 min · **Builds on:** nothing · **Needs:** a computer with internet (macOS, Windows or Linux)

## Why this matters
Every AI engineer's day starts in this same setup: a terminal, Python, Git and an editor. Most "it doesn't work" problems beginners hit are setup problems (wrong Python, package installed in the wrong place). Getting this right once saves you hours in every later project.

## What you'll learn
- **Terminal:** the text window where you type commands like `cd` (change folder) and `python file.py` (run a file).
- **Git:** a tool that saves snapshots of your code (commits) so you can go back in time and share it on GitHub.
- **Virtual environment (venv):** a private box of packages for one project, so projects don't fight over versions.
- **pip:** Python's package installer. `pip install -r requirements.txt` installs everything a project lists.

## Before you start
Install these three programs (all free):
1. **Python 3.11 or newer**: https://www.python.org/downloads/
   On Windows, tick **"Add python.exe to PATH"** on the first installer screen.
2. **Git**: https://git-scm.com/downloads
3. **VS Code**: https://code.visualstudio.com/ then open the Extensions panel (the four squares icon) and install **"Python"** by Microsoft.

Open a terminal: on macOS press `Cmd+Space` and type "Terminal"; on Windows open "PowerShell"; in VS Code use **Terminal → New Terminal**. Check the installs:
```bash
python --version    # macOS/Linux may need: python3 --version
git --version
```
No packages and no API key are needed for this project.

## Run it
1. **Get the course code** (this makes a folder called `Learning`):
   ```bash
   git clone https://github.com/SVashishta1/Learning.git
   cd Learning/ai-engineer-journey
   ```
2. **Create a virtual environment** once, in the course root (`ai-engineer-journey`). Every project uses this same one.
   ```bash
   python -m venv .venv          # macOS/Linux may need: python3 -m venv .venv
   ```
3. **Activate it.** Do this every time you open a new terminal.
   ```bash
   # macOS/Linux:
   source .venv/bin/activate
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   ```
   Your prompt now starts with `(.venv)`. Type `deactivate` to leave it.
4. **Run the checker:**
   ```bash
   python level-0-setup/01-setup-your-ai-workbench/check_setup.py
   ```
5. **Open the course in VS Code:** `code .` (or File → Open Folder). When VS Code asks which Python to use, pick the one inside `.venv`.

### What you should see
On a fresh setup with the venv active:
```
Tools:
✅ Python 3.12.4 (need 3.11+)
✅ running inside a virtual environment
✅ git on PATH
❌ docker on PATH   → install Docker Desktop (needed from project 1.5 Part B and 1.7)

Packages (install per project when you get there):
❌ fastapi (used in Level 1)   → pip install fastapi
❌ numpy (used in Level 2)   → pip install numpy
❌ sklearn (used in Level 3)   → pip install scikit-learn
❌ torch (used in Levels 4-6)   → pip install torch
❌ transformers (used in Levels 5-6)   → pip install transformers
❌ anthropic (used in Levels 7-8)   → pip install anthropic
```
The first three **Tools** lines must be ✅. The ❌ packages are normal on day one: each project installs what it needs with its own `requirements.txt`.

## How it works
`check_setup.py` is 30 lines. Read it top to bottom:
1. `ok(good, label, hint)` is a tiny helper: it prints ✅ and the label if `good` is `True`, otherwise ❌ plus a hint.
2. `sys.version_info >= (3, 11)` compares your Python version with 3.11.
3. `sys.prefix != sys.base_prefix` is `True` only inside a venv: `sys.prefix` points into `.venv`, while `sys.base_prefix` points at the Python you installed.
4. `shutil.which("git")` searches your PATH (the list of folders your terminal looks in for programs) and returns `None` if it can't find it.
5. The last loop uses `importlib.util.find_spec(pkg)` to *look for* each package without loading it, which is fast even for big ones like `torch`.

How the course fits together:
```
Learning/ai-engineer-journey/
├── .venv/                      ← your private box of packages (made in step 2)
├── level-0-setup/
│   └── 01-setup-your-ai-workbench/
│       ├── README.md           ← the lesson (this file)
│       ├── requirements.txt    ← packages this project needs
│       └── check_setup.py      ← the code
└── level-1-apis/ ...
```
For every project: `cd` into its folder, run `pip install -r requirements.txt`, read the README, run the code, then do **Try this**.

## If something goes wrong
- **`python: command not found`** (macOS/Linux) → use `python3` instead of `python` for the venv step. Once the venv is active, `python` works.
- **`'python' is not recognized`** (Windows) → re-run the Python installer, choose **Modify**, and tick "Add Python to environment variables". Or use `py` instead of `python`.
- **PowerShell says "running scripts is disabled on this system"** when activating → run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer `Y`, then activate again.
- **`❌ running inside a virtual environment`** even though you made one → you opened a new terminal. Activate again (step 3); look for `(.venv)` at the start of the prompt.
- **`ModuleNotFoundError` in a later project** → the venv isn't active, or you skipped `pip install -r requirements.txt` in that project's folder.

## Try this
1. Install one package and watch the checker change: `pip install numpy`, then re-run `check_setup.py`.
   <details><summary>Hint</summary>

   The `numpy` line turns into ✅. Run `pip list` to see every package inside your venv. Run `deactivate` and `pip list` again: numpy disappears, because it lives only in the venv.
   </details>
2. Make your first commit. Create a file `notes.md` in the course root, write one line about what you learned, and commit it.
   <details><summary>Solution</summary>

   ```bash
   git add notes.md
   git commit -m "finished 0.1 setup"
   git log --oneline     # your commit is at the top
   ```
   If Git asks who you are, run `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"` once.
   </details>
3. Add a check to `check_setup.py` that shows whether `pip` is on your PATH, with the hint "reinstall Python".
   <details><summary>Solution</summary>

   Add `("pip", "reinstall Python")` to the list in the `for tool, hint in [...]` loop. Run the script again and you get a new `✅ pip on PATH` line.
   </details>

## Check yourself
1. Why use a virtual environment instead of installing every package straight into your system Python?
2. You open a new terminal and `python check_setup.py` says you're not in a venv. What happened, and what's the fix?
3. What does `pip install -r requirements.txt` do?
4. What's the difference between `git commit` and `git push`?

<details><summary>Answers</summary>

1. Each project can have its own package versions without breaking other projects or your operating system's Python. If a venv gets messy, you delete the `.venv` folder and make a new one.
2. Activation only lasts for one terminal window. Run the activate command again (`source .venv/bin/activate` or `.venv\Scripts\Activate.ps1`).
3. It reads the list of packages in `requirements.txt` and installs all of them into the active Python (your venv).
4. `git commit` saves a snapshot on *your* computer. `git push` uploads your commits to GitHub.
</details>

## Learn more (optional)
- Git & GitHub for beginners (freeCodeCamp): https://www.youtube.com/watch?v=RGOj5yH7evk
- Python virtual environments explained: https://www.youtube.com/results?search_query=corey+schafer+python+venv+virtual+environment
- Python's official venv tutorial: https://docs.python.org/3/tutorial/venv.html

## Next
→ [0.2 · Python for AI warm-up](../02-python-for-ai-warmup)
