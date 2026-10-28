# Handover checklist

> Handover is a process, not a meeting. Start it 3-4 weeks before you leave. Every line needs an owner on the
> CUSTOMER side and a date. "Done" means the customer did it themselves at least once while you watched.

## Ownership
- [ ] Named service owner (team and person) and business owner, written in the runbook
- [ ] On-call rota includes the system; first responders have access and know the runbook exists
- [ ] Support path after you leave: who to call, for how long, how (contract / SLA)

## Access and accounts
- [ ] All admin access is in the customer's names (cloud accounts, registry, CI, model provider console, DNS)
- [ ] Your personal access removed or scheduled for removal (date)
- [ ] Billing for the model provider and cloud resources is in the customer's budget, with alerts

## Code, configuration and infrastructure
- [ ] Repository transferred to the customer's Git; CI runs there and is green
- [ ] Infrastructure as code applied from the customer's pipeline (state in their storage)
- [ ] All secrets rotated after transfer (the old ones were known to you)
- [ ] Image versions pinned; the customer can rebuild from scratch (tested once)

## Operations
- [ ] Runbook reviewed and every command run by a customer engineer ("shadow then lead")
- [ ] Alerts route to the customer's pager, with tested test-alerts
- [ ] Dashboards and the monthly SLO report explained; first report produced by them
- [ ] Rollback done by them once in a non-production environment
- [ ] Backup and restore (if the system stores data) tested

## Quality and change
- [ ] Eval set and how to extend it explained; owner for adding new cases
- [ ] Process for prompt/model/policy changes: who approves, which evals must pass
- [ ] Known issues and the backlog handed over (with priorities agreed with the business owner)

## People
- [ ] End users trained (see the training plan); materials in their wiki
- [ ] Champions named in each team
- [ ] Feedback channel live (form, channel, or ticket category) and someone reads it

## Close
- [ ] Handover meeting held; results vs the success metrics in the design doc presented
- [ ] Sign-off from the service owner and business owner (date)
