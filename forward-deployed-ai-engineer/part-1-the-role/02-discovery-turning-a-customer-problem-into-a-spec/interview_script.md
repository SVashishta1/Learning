# Discovery interview script (60 minutes)

Use this as a running order for a first discovery session. Print it, or keep it open on a second screen. Take notes straight into a copy of `notes_template.md`.

**Golden rules**
1. **Listen more than you talk** (aim for 80% them, 20% you).
2. **Ask about the past, not the future.** "Walk me through the last time this happened" gets facts. "Would you use an AI that...?" gets polite yeses.
3. **Get numbers.** "A lot" → "about how many a week?" "Slow" → "how long, from what to what?"
4. **Separate the problem from the solution they asked for.** They asked for "a chatbot"; find out what outcome they want.
5. **Ask "show me".** Watching someone work for 30 minutes beats 2 hours of meetings.
6. **Don't promise anything** in discovery. Say: "Let me check that and come back to you by Friday."

---

## 0. Before the meeting (15 min, alone)
- Re-read the brief. Write down your 3 biggest unknowns.
- Check who is coming and their roles. Make sure at least one daily user and one person from IT/security will be there; if not, ask for them.
- Prepare a copy of `notes_template.md` named `<customer>_notes_<date>.md`.

## 1. Opening (5 min)
> "Thanks for making time. The goal today is for us to understand how things work now and what a great outcome looks like for you. We won't pitch anything. Is it OK if I take notes? Is anyone joining late or should anyone else be here?"

- Agree the time box and the goal.
- Ask permission to record or take notes.

## 2. The problem and why now (10 min)
- "In your own words, what problem are we here to solve?"
- "Why is this important now? What happens if nothing changes for a year?"
- "Who feels this pain most?"
- "How would you know, in 3 months, that this was a success?"

## 3. The current process: "show me" (15 min)
- "Can you walk me through the last time you handled one of these, step by step?"
- "Which screen or tool is that? Can you share your screen and do one live?"
- For each step: "How long does this take? How often? What goes wrong?"
- "Where do you look when you're not sure?" (this finds the hidden data source)

## 4. Data and systems (10 min)
- "Where does the information for each step live?"
- "Who owns that system? Is there an API, a database, or only a screen?"
- "How clean is that data? Can you show me a typical example and a messy one?"
- "Can we get a sample this week? Does it need to be anonymised?"

## 5. Constraints, security and people (10 min)
- "What data is sensitive here? Which rules apply (GDPR, HIPAA, contracts)?"
- "Where is AI allowed to run? Does data have to stay in a country or in your cloud?"
- "Who has to approve a new tool? How long does that usually take?"
- "Who decides, who pays, and who could stop this project?"
- "Any deadlines, freezes or holidays we should plan around?"

## 6. Wrap-up (5 min)
- Read back the problem in one sentence: "So the core problem is ... Did I get that right?"
- Read back the success measure: "So success is going from X to Y by Z. Correct?"
- Agree next steps with owners and dates.
- "What did I not ask that I should have?" (people often say the most important thing here)

## 7. After the meeting (30 min, alone, same day)
- Clean up the notes while they are fresh.
- Run `python discovery_check.py your_notes.md` to find gaps.
- Send a thank-you email within 24 hours with: the problem in one sentence, the success measure, the next steps, and your follow-up questions.
