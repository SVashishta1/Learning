# Part 1 · Git & GitHub

**Git is a time machine for your code.** Every time you "commit", Git takes a photo of your project that you can go back to. GitHub is a website that keeps a copy of those photos online, so teammates can work with you and robots can test every change. Every AI team in the world works this way.

**Time:** about 1 week at 1 hour a day · **Before this part:** [Linux from Zero](../../linux-from-zero), Parts 1–3, and [AI from Zero, Part 1](../../ai-from-zero/part-1-apis) (FastAPI)

| # | Lesson | What you'll have at the end |
|---|--------|-----------------------------|
| 01 | [Git basics: save points](01-git-basics-save-points) | a project with a history you can read, compare and rewind, and secrets kept out of it |
| 02 | [Branches and merge conflicts](02-branches-and-merge-conflicts) | two lines of work merged together, and a real merge conflict fixed by you |
| 03 | [GitHub and pull requests](03-github-and-pull-requests) | your code on GitHub over SSH, a pull request reviewed and merged, a fork |
| 04 | [CI with GitHub Actions](04-ci-with-github-actions) | a robot that runs ruff and pytest on every push for a small FastAPI AI app |

## Install once for this part
1. **Install Git** (version 2.28 or newer):
   - **Ubuntu / WSL2:** `sudo apt update && sudo apt install -y git`
   - **Mac:** run `git --version` in Terminal. If Git is missing, macOS offers to install the "command line developer tools": click **Install**. (Or `brew install git` if you use Homebrew.)
   - **Windows without WSL2:** install "Git for Windows" from https://git-scm.com/downloads and use the "Git Bash" terminal it adds.
2. **Check it:** `git --version` should print something like `git version 2.43.0`.
3. **Python 3.12 and a venv** (lesson 04 only): the same setup as [AI from Zero · Start here](../../ai-from-zero/00-start-here). Lesson 04's README has the exact pip line.
4. **A free GitHub account** (lesson 03): sign up at https://github.com/signup. Lessons 01–02 and the first half of 03 work without it.

## After this part you'll be able to
- Turn any folder into a Git repository and save clean, well-named commits.
- Read the history, compare versions, and undo mistakes with `git restore`.
- Keep secrets (`.env`) and junk (`__pycache__`) out of Git with `.gitignore`.
- Work on branches, merge them, and calmly fix a merge conflict.
- Push to GitHub over SSH or HTTPS, open and review a pull request, and contribute to someone else's project through a fork.
- Write a GitHub Actions workflow that lints and tests a Python AI API on every push and pull request.

**Every lesson works the same way:** `cd` into its folder from the course folder (`cloud-and-devops-for-ai`), follow **Run it** step by step, compare with **What you should see**, then read **How it works**.

## Next
Start with → [01 · Git basics: save points](01-git-basics-save-points). When you finish lesson 04, go on to → [Part 2 · Docker](../part-2-docker).
