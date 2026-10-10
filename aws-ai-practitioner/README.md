# AIF-C01 Trainer

A study app for the **AWS Certified AI Practitioner (AIF-C01)** exam. Open `index.html` in any browser; it works offline and saves progress in the browser.

## What's inside
- **268 exam-style questions** across all 5 domains, in multiple-choice, multiple-response, matching and ordering formats, each with an explanation. 176 were checked and re-explained from public practice sets (several wrong answers in those sets were corrected); 92 were written to cover topics the sets missed.
- **77 concept cards** with memory hooks, laid out as a 5-room memory palace (one room per domain).
- **143 keyword drills** and **50 true/false traps** for quick warm-ups.

## Modes
Daily review (spaced repetition) · Warm-up sprint (3 min) · Pop quiz · Custom quiz · Domain drill · Weak spots · Concept and question flashcards (tap to flip, rate Again/Hard/Good/Easy) · Full mock exam (65 Q, 90 min, weighted 20/24/28/14/14, scaled score).

## Learning science used
Retrieval practice, spaced repetition (SM-2 variant, intervals capped by your exam date), interleaving across domains, elaborative feedback with memory hooks, method of loci, and streak/XP/daily-goal habit loops.

## Editing content
Content lives in `tools/` (`notes.txt`, `authored.jsonl`, `concepts.jsonl`, `warmups.txt`, `tf.txt`). Run `python3 tools/build.py` to regenerate `data.js`.
