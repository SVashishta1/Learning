# FDE interview practice bank (questions + model answers)

Read the question, set a timer, answer **out loud** (or write bullet points), then compare with the model answer. A model answer is one good answer, not the only one. Interviewers care most about: clear structure, questions before solutions, numbers, trade-offs, and safety.

---

## A. Coding (45-60 min, live)
Typical: messy data, an unreliable API, a small feature in an existing codebase, or "write the tool function an agent will call". Practise with `practice/problems.md` (3 problems, solutions and tests).

**How to behave in the room**
1. Repeat the task in your own words and ask 2-3 questions (input size? bad data? what should happen on error?).
2. Write the simplest correct version first, with one test. Say what you are doing.
3. Then improve: edge cases, errors, complexity. Leave 5 minutes to walk through a test case by hand.

**Q1. "Write a tool function for an agent that looks up an order by id. What do you return when the order doesn't exist?"**
<details><summary>Model answer</summary>

Return a structured, readable result instead of raising into the model loop: `{"found": false, "order_id": "...", "hint": "Order ids look like NW-1234567; ask the customer to check it"}`. Validate the input format first (Pydantic or a regex) and say what was wrong. Never return a stack trace (noise, and may leak internals). Keep outputs short (the model pays for every token) and stable (same keys every time). Errors from the system itself (timeouts, 503) should be retried in the client with backoff, and only reported to the model after retries fail, phrased so the model can decide ("the order system is busy; try again later or tell the user"). Log the raw error for humans.
</details>

---

## B. LLM system design (45-60 min, whiteboard)
Use a fixed structure so you never freeze: **1) clarify** users, volume, data, constraints, success metric → **2) simplest design that works** (draw it) → **3) data and retrieval** → **4) model choice and prompts** → **5) evals** → **6) safety, privacy, permissions** → **7) cost and latency** → **8) rollout and operations**.

**Q2. "Design an assistant that drafts replies to 9,000 support emails a week for a logistics company."**
<details><summary>Model answer</summary>

*Clarify:* who sends the reply (agents must approve? yes), languages, systems (helpdesk API, shipment database, policy PDFs), data residency (EU), success metric (first-response time 19 h → under 8 h; drafts sent with small edits ≥ 70 %).
*Design:* helpdesk webhook on new ticket → classifier (cheap model: category, language, tracking number) → tools: shipment lookup (read-only replica), policy RAG with citations → draft with a strong model → shown in the helpdesk sidebar; agent edits and sends. Nothing is emailed automatically.
*Retrieval:* chunk policies by section, hybrid search (BM25 + embeddings), rerank, cite section ids; permissions so finance documents only reach finance users.
*Evals:* a golden set of 200 real, anonymised tickets with expected facts (status, promise allowed by policy), code checks for facts, an LLM judge for tone with human-calibrated rubric; run in CI; online metric = edit distance and "sent without edit".
*Safety:* PII redaction in logs, prompt-injection defence (email text is data; tools are read-only), refusal to promise compensation not in policy.
*Cost/latency:* ~1,800 tickets/day × ~6k input tokens; small model for classification, bigger for drafting; prompt caching for the policy context; async drafting so agents never wait.
*Rollout:* pilot with 10 agents in English, then languages; dashboards; runbook; kill switch.
</details>

**Q3. "Our RAG chatbot gives confident wrong answers. How do you debug it?"**
<details><summary>Model answer</summary>

Separate retrieval from generation. 1) Collect 30-50 failing questions with the right answer and the document that contains it. 2) Check retrieval: is the right chunk in the top-k? (recall@k). If not: chunking (answer split across chunks?), missing documents, embeddings weak on product codes → add keyword/BM25 hybrid search, metadata filters, reranking. 3) If retrieval is right but the answer is wrong: prompt (force answering only from context, cite chunk ids, say "I don't know"), context too long or contradictory (old and new policy versions → filter by version/date), model too small. 4) Add guardrails: require citations, check that cited text supports the claim (a cheap verifier), show sources in the UI. 5) Turn the failures into an eval set and gate every change on it. Report the before/after numbers to the customer.
</details>

**Q4. "When would you use a multi-agent system with a head agent instead of a single agent?"**
<details><summary>Model answer</summary>

Only when the work splits into genuinely different jobs with different tools, data or permissions, or when parallelism helps. Benefits: each specialist has a short prompt and few tools (more reliable), cheaper models for narrow jobs, separation of duties (the agent that decides isn't the one that acts), and independent testing. Costs: more tokens and latency, coordination failures, harder debugging. Start with a workflow or a single agent with good tools; move to a head + specialists when a single prompt gets crowded or when duties must be separated (e.g., assessing a claim vs sending money). Keep consequential actions behind human approval and give the whole team a budget and step limits. Example: the claims desk capstone (triage, shipment, policy, assessor, comms).
</details>

**Q5. "The customer's security team says no data may leave their AWS account. What are your options?"**
<details><summary>Model answer</summary>

1) Claude in Amazon Bedrock in their account and region, reached through VPC endpoints (PrivateLink), with an IAM role limited to approved models; logging configured in their account. 2) If no managed model is allowed: an open model served by vLLM or Ollama on their GPU/CPU servers, with local embeddings. Compare quality with an eval set, cost (GPUs vs per-token), and operations (who patches the model server?). Either way: private subnets, no internet egress, secrets in their secret manager, preflight checks and a written data-flow diagram for the security review. Ask early: which regions, which logging/retention rules, and who signs off.
</details>

---

## C. Customer role-play (30-45 min)
An interviewer plays the customer. They test listening, honesty, calm, and turning emotion into a plan. Pattern: **acknowledge → ask → summarise → propose next step with an owner and a time**.

**Q6. The VP says: "Your AI told a customer we'd refund their shipment. We don't do that. This is unacceptable."**
<details><summary>Model answer</summary>

"You're right to be upset; a wrong promise to a customer is serious. Can I ask a few things so we fix the right problem? Which ticket was it, and was the reply sent by an agent after editing? ... Here's what I'll do today: pull the draft, the sources it used and the agent's edits; check whether the policy text retrieved was outdated or the model ignored it. By 5 pm you'll have a short write-up with the cause and the fix. Meanwhile I suggest we add a rule that drafts can't mention refunds unless the cited policy section allows it, and add this ticket to our test set so it can never come back. Would it help if I also joined Priya's team meeting tomorrow to explain what changed?" Key points: no blame (on the model or the agent), facts first, a concrete timeline, a prevention step, and an offer to communicate.
</details>

**Q7. The security lead asks: "Where exactly does our data go, and who can see it?"**
<details><summary>Model answer</summary>

Draw it: user → app in your VPC → model endpoint (named provider, region) → back. Then answer the details: what is sent (ticket text, retrieved policy chunks; PII redacted where possible), what is stored and where (logs without message text, 30-day retention), what the provider does with it (cite the provider's data-usage terms and your contract/DPA, don't guess), who has access (roles, SSO groups), encryption in transit and at rest. Offer the written data-flow document and the preflight output. If you don't know something: "I'll confirm that in writing by Thursday." Never improvise a compliance answer.
</details>

**Q8. Mid-project, the sponsor asks: "Can we also add invoice disputes? It should be easy."**
<details><summary>Model answer</summary>

"I'd love to help with invoices; it sounds valuable. Before I say yes, two questions: how many disputes a month, and who owns the finance data? Adding it now would put the current go-live date at risk, because it needs new data access and finance sign-off. Options: (a) keep the date, and I write a one-page scope for invoices as phase 2 next week; (b) add it now and move go-live by about four weeks. Which matters more to you?" Protect the commitment, show the trade-off, let the customer decide, write it down.
</details>

---

## D. Take-home (4-8 hours, sometimes paid)
Typical prompt: *"Here are 200 support tickets and 10 policy documents. Build a prototype that drafts answers, and tell us how good it is."*

**How to approach it**
1. Spend the first 30 minutes reading the data and writing down assumptions and questions (email them if allowed).
2. Build the simplest end-to-end path first (retrieval + draft + a CLI or tiny UI), then measure.
3. Make a small golden set (20-30 items) and report numbers, including failures.
4. README: problem, how to run (one command), design diagram, results table, trade-offs, what you'd do next, time spent. Run `python portfolio_check.py <your folder>` before submitting.
5. Don't gold-plate. A working, measured, honest prototype beats a beautiful unfinished one.

**Q9. "You had 6 hours. Why didn't you fine-tune a model?"**
<details><summary>Model answer</summary>

"Fine-tuning needs good labelled data, evaluation and time; it's the right tool for style or format consistency at scale, not for knowledge that changes, like policies. With 6 hours, retrieval plus a strong instruction-following model gave a measurable baseline: 82 % of my golden questions answered correctly with citations. The failures are mostly retrieval misses on product codes, so my next step is hybrid search, not fine-tuning. If after that the tone is inconsistent across thousands of replies, I'd consider fine-tuning a small model on approved past replies."
</details>

---

## E. Behavioural (30 min)
Answer with **STAR**: Situation, Task, Action (what *you* did), Result (numbers), plus what you learned.

**Q10. "Tell me about a time a project didn't go as planned."**
<details><summary>Model answer</summary>

Use a real story from your projects. Example from this course: "In my claims-desk capstone, my evals passed with a perfect mock API. When I added a run with 30 % failing requests, the whole batch crashed: one lookup failed four times in a row and the exception escaped the agent loop. I changed the engine so tool failures are reported back to the agent, added one more retry with backoff, and kept the flaky run in CI permanently. Since then, every change is tested against an unreliable system, which is what real customer systems are."
</details>

---

## Questions to ask *them*
- "What does the first 90 days look like for a new FDE? Which customer would I join?"
- "How do FDE learnings get back into the product?"
- "How much time is on site vs remote, and how do you protect focus time?"
- "What separates a good FDE from a great one here?"
