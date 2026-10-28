# Discovery notes: Northwind claims desk · 2026-12-08 (on site, Kraków)

## Who we talked to
- Joanna Wiśniewska, Claims Team Lead: sponsor for phase 2, owns the claims process.
- Two claims handlers (Piotr, 4 years; Eva, 1 year). We shadowed each for 45 minutes.
- Marek Nowak, IT Security (30 minutes). Tomasz, IT engineer (owns the TMS read-only gateway built in phase 1).
- A finance controller (15 minutes, by phone) about credit notes.

## The problem in their words
- Joanna: "Approve claims automatically." When we asked why: "So customers stop waiting three weeks."
- Piotr: "The decision takes 30 seconds. Finding the shipment, the POD and writing the email in Dutch takes 15 minutes."
- Finance: "An AI must never pay anyone. A person approves, and above EUR 1,000 a supervisor."
- **In our words:** handlers spend most of each claim on lookups and writing replies, not on the decision, so claims wait for weeks. The win is a prepared decision pack per claim (facts, policy basis, amount, reply draft) that a handler approves in one minute. **Not** automatic approval.

## Current process (step by step)
1. Customer emails claims@northwind; HelpDesk creates a ticket in the "claims" queue.
2. Handler finds the tracking number (NW-1234567) and opens the TMS: weight, insurance, delivery date, POD remark.
3. Handler opens the claims policy PDF to check time limits and the liability cap (EUR 10 per kg unless insured).
4. Handler calculates the amount in Excel, asks a supervisor if above EUR 1,000, creates a credit note in the finance system.
5. Handler writes the reply from scratch in the customer's language (EN, NL or PL).

## Pain and impact (numbers)
- 600 claims a month; median time to decision 19 working days (HelpDesk report); target 3 days.
- Handling time: 15 to 20 minutes per claim (timed 11 claims), of which about 2 minutes is the actual decision.
- About 10 % of claims are reopened because the first answer was wrong (mostly time limits misapplied).
- One fraud attempt per month on average (changed bank details in emails).

## Data and systems
- HelpDesk: REST API (OAuth2 client credentials, from phase 1); internal notes, replies.
- TMS: the read-only gateway Tomasz built in phase 1 (`/tms/shipments/{tracking}`). Sometimes slow: returns 503 at busy times.
- Finance: credit-note API, owned by finance IT. Credits always go to the bank account on the customer contract.
- Policies: claims policy v3.2 and delivery terms v5.0 (Markdown exports from SharePoint).

## Security, privacy, compliance
- Same rules as phase 1: EU data residency, SSO, no customer email sent without a person approving it.
- New: payment authority. Handlers up to EUR 1,000, supervisors above. Payment details are never taken from emails.
- Marek: "Show me that a prompt injection in a customer email cannot move money."

## Success looks like
- Median time to decision from 19 working days to under 3 (Joanna).
- Handling time per claim from 15 minutes to under 4 (Piotr).
- Reopened claims from 10 % to under 3 %, because rules are applied by code (Joanna).
- Zero payments without the right human approval (finance, Marek).

## Risks and unknowns
- The TMS gateway's 503s at peak times. Mitigation: retries with backoff; tested with a 30 % failure rate.
- Dutch and Polish replies must be checked by native speakers in the pilot (Eva speaks Polish; a Rotterdam colleague for Dutch).
- Policy changes: when v3.3 arrives, who updates the rules in code? (Owner: Joanna + Tomasz; see runbook.)
