# Discovery notes: Northwind Logistics · 2026-10-06 (on site, Rotterdam)

## Who we talked to
- Dana Okafor, VP Customer Operations: sponsor, owns the budget.
- Priya Raman, support team lead (Rotterdam): manages 25 agents, very hands-on.
- Sam Lee, senior support agent: 6 years at Northwind; we shadowed Sam for 1 hour.
- Marek Nowak, IT security lead: joined for the last 30 minutes.

## The problem in their words
- Dana: "Customers say we are slow. The board wants an AI story."
- Priya: "Half my team's day is copy-pasting tracking numbers between the email and the TMS."
- Sam: "I don't want a chatbot talking to my customers. I want something that does the boring lookup for me."
- In our words: agents spend most of their time answering repetitive "where is my shipment?" emails by hand-searching a legacy system, so replies are slow.

## Current process (step by step)
1. Customer emails support@northwind (about 9,000 emails a week). HelpDesk turns each email into a ticket.
2. Agent opens the ticket, reads it, and copies the tracking number (format NW-1234567) or the customer's order reference.
3. Agent opens the TMS (a Windows desktop app), searches for the shipment, reads the status and the last scan.
4. If there is a delay, the agent checks the delivery terms PDF on SharePoint to see what we promise.
5. Agent writes a reply from scratch (no templates are used in practice) and sets the ticket category by hand.
6. Damage claims and invoice disputes are forwarded to the claims team or finance by email.

## Pain and impact (numbers)
- First response time (FRT): median 19 hours, target in customer contracts is 8 hours (source: HelpDesk report Priya showed us).
- "Where is my shipment?" (WISMO) is about 40% of tickets (Priya's estimate; to be checked with SQL in the TMS replica).
- A WISMO ticket takes about 6 minutes of agent time (we timed 9 of Sam's tickets: 4 to 9 minutes).
- 45 agents; staff turnover 30% a year; new agents need 6 weeks to learn the TMS.
- 2 of the top 20 customers mentioned slow support in their last renewal review.

## Users and volume
- 45 support agents (Rotterdam 25, Kraków 20), working in English, Dutch and Polish.
- About 9,000 emails a week; peaks of 2,500 a day after holidays and storms.
- Later maybe: the claims team (8 people) and finance (5 people).

## Data sources
- HelpDesk tickets: 3 years of history, about 1.2 million tickets, with categories (set by hand, often wrong).
- TMS: Oracle database; IT can give a read-only replica (nightly copy) or a SQL view. Shipments, scans, customers.
- SharePoint: about 60 policy PDFs (claims, refunds, delivery terms), some scanned.
- Rate cards: Excel files, one per large customer, with merged header cells.
- Sam's personal "cheat sheet" Word document of good replies (useful as examples).

## Systems and integrations
- HelpDesk: has a REST API and webhooks (new ticket event); admin access via Priya.
- SalesCloud CRM: REST API with OAuth2 client credentials; owned by the sales ops team.
- TMS: no API. Read-only SQL replica possible (Marek must approve the firewall rule).
- SharePoint: Microsoft Graph API, needs an app registration approved by IT.
- Single sign-on with Microsoft Entra ID for every internal tool.

## Security, privacy and compliance
- Tickets contain names, addresses, phone numbers and sometimes bank details (refund requests).
- GDPR applies; data must stay in the EU. Marek: "Nothing leaves our tenant without a DPA and a review."
- AI may run in their Azure EU region or with a provider that has EU data residency. Which option will legal accept? TBD
- Agents must log in with SSO; finance documents must only be visible to finance.
- No AI reply may be sent to a customer without an agent approving it (Dana and Priya agreed).

## Success looks like
- Dana: FRT under 8 hours (contract target) within 3 months of go-live.
- Priya: WISMO handling time from 6 minutes to under 2 minutes.
- Sam: drafts are good enough that agents send them with small or no edits at least 70% of the time.
- Baseline today: FRT 19 h median; 6 min per WISMO ticket; 0% drafted.

## Constraints (time, budget, people)
- 12-week pilot, starting 2026-11-03; change freeze 15 Dec to 6 Jan.
- Budget approved for the pilot; production budget depends on pilot results.
- IT has one engineer (Tomasz) who can give us about 1 day a week.
- Pilot group: 10 agents in Rotterdam, English emails only.

## Stakeholders and decision makers
- Pays and decides: Dana. Wants a visible win before the board meeting on 2027-01-20.
- Can block: Marek (security review takes 3 to 4 weeks; start now).
- Daily users: agents like Sam. Worried that AI will replace them; enthusiastic if it removes lookups.
- Influencer: Priya. Trusted by agents. Will champion it if agents are involved in testing.

## Risks and unknowns
- Firewall rule for the TMS replica may take weeks. Fallback: nightly CSV export.
- Ticket categories in history are unreliable, so we can't use them as truth without cleaning.
- Scanned PDFs need OCR. How many of the 60 are scanned? TBD
- Legal may reject every hosted option. Fallback: an open model in their own Azure tenant (Part 5).
- Agents' trust: one bad answer in the first week could kill adoption.

## Next steps
- Us: write the design doc and success metrics, send by 2026-10-13.
- Us: SQL query on the replica sample to confirm the 40% WISMO share.
- Priya: export 500 recent tickets (anonymised) for us to build an eval set.
- Marek: send the security questionnaire; start the review.
- Tomasz: request the firewall rule for the TMS replica.
- Follow-up question to Marek: can we get a list of which policy PDFs are scanned?
