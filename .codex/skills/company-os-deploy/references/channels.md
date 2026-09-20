# Slack channels for a Company OS agent

Create these in **the operator's** Slack workspace. Ask before renaming.
Do not reuse another team's channel IDs, standing orders, or workspace.

## Required (when the Slack bot is enabled)

| Channel | Why | Bot |
|---|---|---|
| `#agent-test` | Proof the bot works. Mention it once; require a reply. | Invite, then `@mention` |

If `#agent-test` already exists, reuse it. Do not create a second test channel.

Return:

```text
Test channel: https://app.slack.com/client/<team-id>/<channel-id>
```

Keep `<team-id>` and `<channel-id>` out of git. They may appear in the
handoff the operator sees.

## Recommended (ask; default yes if they use the matching skill)

| Channel | Why | Bot behavior |
|---|---|---|
| `#decisions` | 1-way / 2-way calls via the `/decide` skill | Member. Reply when mentioned or when the operator sets a standing order. No unsolicited posts. |
| `#general` | Optional default-channel presence | Invite only if the operator wants it. Same reply rule. |

Do **not** create a transcripts / vault / CRM channel unless the operator
asks. Those need extra connectors this template does not assume.

## Standing orders

QM channel automation is a standing order on that channel, not a webhook
you invent. After the bot can reply in `#agent-test`:

1. Ask whether they want any standing order at all. Default is **none**.
2. If they want `#decisions` to log outcomes, write a short order in the
   channel (operator pastes, or you draft for them to paste): reply when
   someone asks to record a decision; do not post on a timer; never dump
   private docs.
3. No uncapped cron posting.

## What not to do

- Do not invite the bot to every channel.
- Do not put workspace IDs, bot tokens, or channel IDs in this repo.
- Do not clone another company's `#transcripts` / vault pipeline.
- Changing `slack-app-manifest.yml` does nothing until the Slack app is
  **reinstalled**. If the bot connects but cannot post, reinstall.
