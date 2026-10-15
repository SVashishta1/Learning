# 8.7 · Human-in-the-loop agent: a file organizer you can trust

**What you'll build:** an agent that **takes real actions on your computer**: it tidies a messy Downloads folder into sensible sub-folders and removes empty files and exact duplicates. It's wrapped in the safety layers real companies require before letting an agent act:

| Safety layer | How |
|---|---|
| **Sandbox** | it can only touch `./workspace`; `../../` escape attempts are blocked in code |
| **Read freely, write with permission** | listing and reading run freely; every move or delete asks you **y/N** |
| **Dry-run mode** | `--dry-run` shows the plan without changing anything |
| **Reversible actions** | "delete" moves files to `workspace/.trash` |
| **Audit log** | every action, and every action you declined, goes to `audit_log.jsonl` with a timestamp |
| **Limits** | a maximum number of steps, plus a cost report |

**Like you're 10:** a new helper cleans your room, but they can only touch things *inside your room*, they must ask "can I throw this away?" before binning anything, the "bin" is really a box you can dig things back out of, and they write down everything they did.
**Time:** ~2 h · **Builds on:** [8.6 Build your own MCP server](../06-build-your-own-mcp-server) and approvals from [8.2](../02-customer-support-router-and-specialists) · **Needs:** an Anthropic API key (tests run without one)

## Why this matters
An agent that only talks can be wrong; an agent that *acts* can do damage: delete the wrong files, send the wrong email, pay the wrong invoice. As agents get more power (computer use, coding agents, booking and payment agents), the engineering that keeps them safe matters more than the clever prompt. Sandboxes, approvals, dry runs, undo and audit logs are exactly what security and compliance teams ask about before any agent goes live.

## What you'll learn
- **Sandboxing**: limiting an agent to one folder, enforced by code that checks every path.
- **Risk-based permissions**: low-risk actions (read, list) run freely; high-risk ones (move, delete) need a human "yes".
- **Dry run**: showing exactly what would happen without doing it.
- **Reversibility**: designing actions so mistakes can be undone (a trash folder instead of real deletion).
- **Audit logging**: an append-only record of what the agent did and what the human refused.

## Before you start
```bash
cd level-8-multi-agent-systems/07-human-in-the-loop-file-organizer-agent
pip install -r requirements.txt
```
- `anthropic`: calls Claude. `pydantic`: tool inputs. `pytest`: tests. (Everything else is Python's standard library: `pathlib`, `shutil`, `hashlib`.)

**API key:** set `ANTHROPIC_API_KEY` as in the [Level 7 README](../../level-7-real-world-ai-apps/README.md#api-key-needed-from-here-on). Cheap mode: `export CLAUDE_MODEL=claude-haiku-5-5`.

## Run it
1. From the course root: `cd level-8-multi-agent-systems/07-human-in-the-loop-file-organizer-agent`
2. Tests (offline): `pytest -v`
3. Create the messy folder (14 files, including duplicates and an empty file): `python make_messy_folder.py`
4. See the plan without changing anything: `python organizer.py --dry-run`
5. Do it for real: `python organizer.py`, then answer `y` or `n` for each action. Try declining a few and watch the agent adapt.
6. Read the log: `cat audit_log.jsonl` (Windows: `type audit_log.jsonl`)

To start over, delete the `workspace` folder and `audit_log.jsonl`, then run step 3 again.

### What you should see
(Representative: the agent's plan and folder names vary.)
```
[Organizer] ▶ Tidy up the 'downloads' folder: put files in sensible sub-folders, delete empty files and exact duplicates.
[Organizer] 🔧 list_files({"path": "downloads"}) -> downloads/IMG_2041.jpg  (16 bytes, md5 66241640)
downloads/IMG_2042.jpg  (16 bytes, md5 66241640)
...
⚠️  Organizer wants to run move_file({"source": "downloads/IMG_2041.jpg", "destination": "downloads/Images/IMG_2041.jpg"}). Allow? [y/N] y
[Organizer] 🔧 move_file(...) -> Moved downloads/IMG_2041.jpg -> downloads/Images/IMG_2041.jpg

⚠️  Organizer wants to run move_file({"source": "downloads/setup_installer.exe", "destination": "downloads/Installers/setup_installer.exe"}). Allow? [y/N] n
[Organizer] 🚫 move_file declined by human

⚠️  Organizer wants to run delete_file({"path": "downloads/untitled.txt"}). Allow? [y/N] y
[Organizer] 🔧 delete_file(...) -> Deleted downloads/untitled.txt (recoverable from workspace/.trash)
...
| Action | File | Result |
|---|---|---|
| moved | IMG_2041.jpg → Images/ | done |
| moved | setup_installer.exe → Installers/ | declined by you, left in place |
| deleted | untitled.txt (empty) | in .trash |
...
Audit log: .../audit_log.jsonl | changes applied
```
And `audit_log.jsonl` (real format):
```
{"time": "2026-10-15T04:43:49", "action": "move", "dry_run": false, "source": "downloads/IMG_2041.jpg", "destination": "downloads/Images/IMG_2041.jpg"}
{"time": "2026-10-15T04:43:49", "action": "declined", "dry_run": false, "tool": "move_file", "source": "downloads/setup_installer.exe", "destination": "downloads/Installers/setup_installer.exe"}
{"time": "2026-10-15T04:43:49", "action": "delete", "dry_run": false, "path": "downloads/untitled.txt", "size": 0}
```
What to look at: `IMG_2041.jpg` and `IMG_2042.jpg` have the same md5, which is how the agent *knows* they're duplicates; after you decline, the agent carries on with other actions instead of retrying; `untitled.txt` is in `workspace/.trash`, not gone.

## How it works
```
Organizer agent ─► list_files / read_file ─────────────────────► runs freely (read-only)
               └─► move_file / delete_file ─► approver(): y/N? ─► no  → "DECLINED" to the agent + audit("declined")
                                                               └► yes → safe_path() check → audit() → act (or dry run)
```

1. **`HERE`, `SANDBOX`, `AUDIT_LOG`**: paths are built from the script's own folder, so the sandbox is always this project's `workspace/`, wherever you run it from.
2. **`safe_path(p)`** joins `p` to the sandbox and calls `.resolve()`, which turns `..` and symbolic links into the real absolute path. If the result isn't the sandbox or inside it, it raises `PermissionError`. Every tool uses it, so even a model asked to "tidy ../../Documents" can't escape. This is the boundary; the prompt is not.
3. **Read-only tools.** `list_files` lists every file with its size and the first 8 characters of its **md5 hash** (a fingerprint of the content: same content = same hash). `read_file` returns the first 2,000 characters of a text file.
4. **Changing tools.** `move_file` refuses missing sources and existing destinations (no accidental overwrites), writes an audit entry, then moves (creating folders as needed). `delete_file` audits, then moves the file into `.trash` with a time prefix. In dry-run mode both return "[dry run] would ..." and change nothing.
5. **`audit(action, **details)`** appends one JSON line with the time, the action, whether it was a dry run and the details. Append-only lines are easy to read, search and keep.
6. **`approver()`** is what `agent_core` calls for tools with `needs_approval=True`. In a dry run it says yes (nothing real happens). Otherwise it asks you with `cli_approver`, and if you say no it records a `declined` entry. `agent_core` then tells the model "The human reviewer DECLINED this action. Do not retry it", so it adapts.
7. **The agent** has a system prompt that says: list and inspect first, plan, then act; only delete empty files or exact duplicates; respect declines; finish with a summary table. `max_steps=30` caps the run.
8. **Tests** check the sandbox blocks `../../etc/passwd`, that moves and deletes are audited and reversible, that dry runs change nothing, that duplicate files show the same hash, and that declines are audited.

## If something goes wrong
- **`Run: python make_messy_folder.py`** → the workspace doesn't exist yet. Run that script first.
- **The script seems stuck** → it's waiting for your `y`/`N` answer to an `Allow?` question.
- **`... already exists; choose another name`** → you ran it before and files are already organised. Delete `workspace/` and `audit_log.jsonl` and rebuild with `make_messy_folder.py`.
- **`PermissionError: ... is outside the sandbox`** in the log → the agent tried a path outside `workspace/`. That's the safety layer working; it gets the error and should correct itself.
- **`[Organizer] stopped after 30 steps`** → many files need many tool calls. Raise `max_steps`, or ask for fewer changes per run.

## Try this
1. **Undo.** Add an `undo_last_move()` tool that reads `audit_log.jsonl`, finds the last real `move`, and moves the file back.
   <details><summary>Solution</summary>

   ```python
   def undo_last_move() -> str:
       moves = [json.loads(l) for l in AUDIT_LOG.read_text(encoding="utf-8").splitlines()]
       moves = [m for m in moves if m["action"] == "move" and not m["dry_run"]]
       if not moves:
           return "Nothing to undo."
       last = moves[-1]
       return move_file(last["destination"], last["source"])     # same safety checks and audit as any move
   ```
   Register it with `Tool("undo_last_move", "Undo the most recent move", NoArgs, undo_last_move, needs_approval=True)`, where `class NoArgs(BaseModel): pass`. Because it reuses `move_file`, the undo is itself sandboxed and audited.
   </details>
2. **A risk-based approval policy.** Auto-approve moves into a *new* sub-folder of `downloads`, but keep asking for every delete.
   <details><summary>Solution</summary>

   ```python
   def approver(agent, tool, args):
       if DRY_RUN:
           return True
       if tool == "move_file" and Path(args["destination"]).parent != Path(args["source"]).parent:
           return True                                   # tidying into a folder: low risk, reversible
       allowed = cli_approver(agent, tool, args)
       if not allowed:
           audit("declined", tool=tool, **args)
       return allowed
   ```
   Real agent products work like this: low-risk, reversible actions run automatically; risky ones need a human.
   </details>
3. **Your real Downloads folder (safely).** *Copy* (never move) your real Downloads folder to `workspace/downloads`, run with `--dry-run` first, read the plan, then run for real.
   <details><summary>Hint</summary>

   macOS/Linux: `rm -rf workspace/downloads && cp -r ~/Downloads workspace/downloads`. Windows PowerShell: `Copy-Item -Recurse $HOME\Downloads workspace\downloads`. Large folders make `list_files` long (it hashes every file), so try a copy of a smaller folder first. Never point `SANDBOX` at a folder you can't afford to have reorganised.
   </details>

## Check yourself
1. Why is "stay inside the workspace folder" enforced in `safe_path` and not just in the system prompt?
2. Why does "delete" move files to `.trash` instead of really deleting them?
3. How does the agent know two files are duplicates, even with different names?
4. Name an action in another product (not files) that should always need human approval, and one that shouldn't.

<details><summary>Answers</summary>

1. Prompts are guidance; a model can misunderstand or be tricked (prompt injection). Code is a hard boundary: the path check runs on every action, whatever the model says.
2. Reversibility: if the agent (or you) made a mistake, the file can be restored. Designing actions to be undoable makes autonomy much safer.
3. It compares md5 hashes from `list_files`: the hash depends only on the content, so identical content gives an identical hash regardless of file name.
4. Always approve: sending money, emailing customers, deleting data, deploying to production. Fine to automate: reading, searching, drafting, creating a new folder or a draft document.
</details>

## Learn more (optional)
- Building effective agents, guardrails and human oversight (Anthropic): https://www.anthropic.com/engineering/building-effective-agents
- Python `pathlib` (resolve, parents): https://docs.python.org/3/library/pathlib.html
- Principle of least privilege: https://www.youtube.com/results?search_query=principle+of+least+privilege+explained

## Next
→ [8.8 · Capstone: AI incident-response team](../08-capstone-ai-incident-response-team)
