# Demo script: Northwind Reply Assistant (20 minutes)

**Audience:** Dana (VP, decides), Priya (team lead), Sam (agent), Marek (security).
**One thing they must remember:** "It does the lookup, drafts a reply with sources, and the agent stays in control."

## Before (T minus 30 minutes)
- [ ] Laptop charged, notifications off, browser zoom at 125%, other tabs closed.
- [ ] `uvicorn app:app` running; `python preflight.py` says **All green**.
- [ ] If Wi-Fi is unreliable: restart with `DEMO_MODE=recorded` (and say so honestly if asked).
- [ ] Phone hotspot ready as a backup network.
- [ ] A screen recording of a good run saved on the desktop (last-resort backup).
- [ ] Know your 3 samples by heart: delayed, delivered-but-missing, damage claim.

## 1. Their problem, in their words (2 min)
> "Last week Sam showed us how a 'where is my shipment' email takes about 6 minutes, mostly copying numbers into the TMS. 40% of your 9,000 weekly emails look like that. Today we'll show one idea for getting those 6 minutes down to under 2."

Don't start with the technology. Start with their numbers. It shows you listened.

## 2. The happy path (5 min)
1. Click **Delayed shipment**. Read the email aloud in one sentence.
2. Click **Draft reply**. While it thinks (1–3 seconds), say: "It's looking up the shipment and the delivery terms."
3. Point at **Facts from the TMS**: "This part is plain code, not AI. The status comes straight from your system, so it can't be made up."
4. Point at the draft: the new ETA, the apology, the 10% credit offer, and **Policy cited: DT-3.1, DT-3.2**.
5. Turn to Sam: "Would you send this? What would you change?" (Let him answer. Write it down.)

## 3. The tricky cases (5 min)
1. **Delivered but missing:** the draft names who signed and offers proof of delivery. Ask Priya if that's the right process.
2. **Damage claim:** the assistant does NOT promise compensation; it routes to Claims (DT-5.1). Say: "We told it what it must not do. That's a non-goal from the design doc."
3. **No tracking number:** it asks for the number instead of guessing.

## 4. Trust and safety (4 min, mainly for Marek)
- Every reply is a **draft**; nothing is sent without an agent.
- Facts come from code; the AI only writes the words around them.
- The badge shows LIVE, RECORDED or FALLBACK, so nobody is ever misled about what they see.
- In the pilot: EU hosting, SSO, redaction of bank details, audit log (design doc section "Security").

## 5. Next steps (4 min)
- Ask: "What would make you say yes to the 12-week pilot?"
- Agree: 500 anonymised tickets for the evaluation set; security questionnaire; firewall request.
- Confirm the decision date.

## If something goes wrong live
| What happens | What you say and do |
|--------------|---------------------|
| Answer is wrong | "Good catch, that's exactly why an agent reviews every draft, and why we measure accuracy on 300 real tickets before the pilot." Note it; never argue with the output. |
| Spinner hangs | After 20 seconds the app falls back by itself and shows FALLBACK. Say: "The live AI didn't answer in time, so it shows a recorded answer. In production we'd alert on this." |
| App crashes | Switch to the screen recording. "Let me show you the recording while I restart it." Restart with `DEMO_MODE=recorded`. |
| Someone asks for a feature you don't have | "Great idea. Can I add it to the list for after the pilot?" Never build live on stage. |
| A question you can't answer | "I don't know yet. I'll find out and email you by Friday." Then do it. |
