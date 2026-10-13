# 8.7 · Human-in-the-loop agent: a file organizer you can trust

**What you build:** an agent that **takes real actions on your computer**: it tidies a messy Downloads folder into sensible sub-folders and removes empty files and exact duplicates. It's wrapped in the safety layers real companies require before letting an agent act:

| Safety layer | How |
|---|---|
| **Sandbox** | it can only touch `./workspace`; `../../` escape attempts are blocked |
| **Read freely, write with permission** | listing and reading run freely; every move or delete asks you **y/N** |
| **Dry-run mode** | `--dry-run` shows the plan without changing anything |
| **Reversible actions** | "delete" moves files to `workspace/.trash` |
| **Audit log** | every action goes to `audit_log.jsonl` with a timestamp |
| **Limits** | max steps, plus a cost report |

**Like you're 10:** a new helper cleans your room, but they can only touch things *inside your room*, they must ask "can I throw this away?" before binning anything, the "bin" is really a box you can dig things back out of, and they write down everything they did.

## Run it
```bash
cd level-8-multi-agent-systems/07-human-in-the-loop-file-organizer-agent
pip install -r requirements.txt
python make_messy_folder.py                 # creates workspace/downloads with 14 messy files
export ANTHROPIC_API_KEY=sk-ant-...
python organizer.py --dry-run               # see the plan, nothing changes
python organizer.py                         # do it for real; approve or decline each action
cat audit_log.jsonl
```
Try declining a few actions and watch the agent adapt.

Tests (offline): `pytest -v`

## Key ideas
- **The more an agent can DO, the more guardrails it needs.** Reading is low-risk; moving, deleting, sending, paying are high-risk.
- **Enforce safety in code** (`safe_path`), not in the prompt. A prompt saying "stay in the folder" isn't a security boundary.
- **Declines are information:** the tool returns "DECLINED, don't retry", so the agent adjusts instead of looping.
- **Audit logs** answer "what did the AI do and when?". That's mandatory in many industries.
- Duplicates are detected with **md5 hashes** (same content = same hash), not by guessing from file names.

## Your turn
1. Add an `undo_last()` tool that reads the audit log and reverses the last move.
2. Auto-approve "safe" moves (into a new sub-folder) and only ask for deletes: a risk-based approval policy.
3. Point it at a copy of your real Downloads folder (copy it into `workspace/` first!).

## Read
- Guardrails and human oversight for agents: https://www.anthropic.com/engineering/building-effective-agents
