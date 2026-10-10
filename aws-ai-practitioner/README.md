# AIF-C01 Trainer

A study app for the **AWS Certified AI Practitioner (AIF-C01)** exam. Open `index.html` in any browser; it works offline and saves progress in the browser.

## What's inside
- **279 exam-style questions** across all 5 domains, in multiple-choice, multiple-response, matching and ordering formats. Each is tagged Fundamental, Applied or Scenario and has an explanation.
  - 138 are checked, re-explained items from public practice sets. Wrong answers were corrected, and 36 low-value or duplicate items were removed.
  - 141 were written to match the exam's scenario style ("A company needs… with the LEAST operational overhead…").
- **54 AWS service cards** covering what each service does, when to use it, when not to, and the exam cue. They also generate **179 "which service fits?" questions**.
- **54 look-alike pairs** (e.g. Textract vs Rekognition, Knowledge Bases vs Agents, Clarify vs Model Monitor, CloudTrail vs Config). Each has the rule that separates them and generates **220 "this or that?" scenario questions**, where one condition decides the answer.
- **77 concept cards** with memory hooks, laid out as a 5-room memory palace (one room per domain).
- **143 keyword drills** and **50 true/false traps** for quick warm-ups.

## Modes
Daily review (spaced repetition) · Warm-up sprint (3 min) · Pop quiz · Custom quiz · Domain drill · Weak spots · Concept and question flashcards (tap to flip, rate Again/Hard/Good/Easy) · Full mock exam (65 Q, 90 min, weighted 20/24/28/14/14, scaled score).

## Learning science used
Retrieval practice, spaced repetition (SM-2 variant, intervals capped by your exam date), interleaving across domains, elaborative feedback with memory hooks, method of loci, and streak/XP/daily-goal habit loops.

## Editing content
Content lives in `tools/` (`services.jsonl`, `confusables.jsonl`, `scenarios.jsonl`, `notes.txt`, `authored.jsonl`, `concepts.jsonl`, `warmups.txt`, `tf.txt`). Run `python3 tools/build.py` to regenerate `data.js`.
