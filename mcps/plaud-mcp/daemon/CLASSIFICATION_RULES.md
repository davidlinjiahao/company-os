# Transcript Classification Rules

Configure these rules for your team's transcript classification gate.

## Team Members (INTERNAL)
- List your team members here
- Conversations among ONLY these people = PERSONAL

## SHARE Criteria
- External technical consultations with novel input
- Customer/partner calls with actionable insights
- Advisory sessions where external experts provide input

## PERSONAL Criteria
- Internal-only meetings (no external participants)
- Personal conversations
- Vendor negotiations without technical novelty
- Recruiting/interview calls

## Calendar Event Signals

| Calendar tag | Signal |
|---|---|
| `[Team - ...]` | Strong PERSONAL (internal meeting) |
| `[Relationship - ...]` | Strong PERSONAL |
| `[Recruiting - ...]` | Usually PERSONAL |
| Named external person/company | Likely SHARE |

## Examples
Add your own examples as you build your golden dataset:
- SHARE: "External advisor gave technical feedback on architecture"
- PERSONAL: "Internal standup, no external participants"
