# 0.1 · Set up your AI workbench

**Goal:** get a working Python setup in 20 minutes so every other project "just runs".
**Analogy:** before cooking, you set up the kitchen: knives, pans, ingredients in reach.

## Steps

1. **Install Python 3.11 or newer**: https://www.python.org/downloads/ (on Windows, tick "Add Python to PATH").
2. **Install Git**: https://git-scm.com/downloads
3. **Install VS Code**: https://code.visualstudio.com/ and add the "Python" extension.
4. **Clone this repo**
   ```bash
   git clone https://github.com/SVashishta1/Learning.git
   cd Learning/ai-engineer-journey
   ```
5. **Create a virtual environment.** A venv is a private box of packages for one project, so projects don't fight over versions.
   ```bash
   python -m venv .venv
   # macOS/Linux:
   source .venv/bin/activate
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   ```
   Your prompt now starts with `(.venv)`. Run `deactivate` to leave it.
6. **Run the checker**
   ```bash
   python level-0-setup/01-setup-your-ai-workbench/check_setup.py
   ```
   It prints a ✅ or ❌ for each tool. You don't need everything on day one; each project lists what it needs.

## How to work through this repo

- Every project folder has its own `README.md` and `requirements.txt`.
- Install a project's packages from inside its folder: `pip install -r requirements.txt`
- Read the code top to bottom. The comments explain the *why*.
- Do the **"Your turn"** challenges at the bottom of each README. That's where learning sticks.
- Commit after every project: `git add . && git commit -m "finished 1.3 joke api"`. Watching your commit list grow builds confidence.

## Watch
- Git & GitHub for beginners (freeCodeCamp): https://www.youtube.com/watch?v=RGOj5yH7evk
- Python virtual environments explained: https://www.youtube.com/results?search_query=corey+schafer+python+venv+virtual+environment
