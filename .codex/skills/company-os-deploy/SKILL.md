---
name: company-os-deploy
description: >
  Deploy this Company OS repository as a QM company agent (Slack + web),
  including Slack app install and channel setup. Use when the operator says
  "deploy this", "set up QM", "install the company agent", "add the Slack
  bot", or "create the agent channels". This repo is already a QM deployment
  directory — do not run qm init.
---

# Deploy Company OS (QM + Slack + channels)

This repository **is already** a QM deployment (`qm.config.jsonc` + pinned
`@yc-software/qm`). Do **not** run `qm init`. Do **not** clone
`yc-software/qm` unless the operator explicitly wants a source fork.

Authoritative upstream workflow: `../../../deployment.md` and sibling
`../deploy-qm/SKILL.md`. This file only adds Company OS specifics.

## 0. Announce

"Deploying Company OS as a QM company agent. I will not run `qm init`.
Cloud deploy bills your account. I will collect choices, stamp the slug,
run `qm setup` / `qm up`, then install the Slack bot and join channels."

## 1. Collect (ask one at a time)

Required:

- Organization slug (lowercase DNS label). Default from
  `company-os.config.sh` → `COMPANY_SLUG` if that file exists and is not
  the placeholder `your-company`. Confirm it. Fly app names will be
  `<slug>-core`, `<slug>-portal`, …
- Hosting: Fly.io (default) or AWS. Do not offer docker as production.
- First admin **work** email.
- Sign-in: email magic link (built-in `auth` + Resend) **or** Slack SSO.
  If they already run Slack, recommend Slack SSO (no DNS, no Resend).
- Model provider and its API key (Anthropic default). Collect the key in
  the same pass. Never echo it. Write only via `npm exec qm -- secrets set`.
- Fly org + region (Fly default org slug is `personal`; region default `sjc`).
- Whether to enable the Slack **bot** now (yes unless they opt out).

Confirm billable resources (always-on machines, Postgres, object storage,
model tokens) before any `qm up`.

## 2. Stamp placeholders

If `COMPANY_SLUG` is set and is not `your-company`:

```bash
export COMPANY_SLUG QM_TARGET QM_REGION QM_FLY_ORG
bash setup/steps/11-qm.sh
```

Otherwise edit `qm.config.jsonc` (`orgId`, `appPrefix`, `publicUrl`,
`flyOrg`, `region`, `S3_BUCKET`) before setup. App names must be free on
the provider. On a collision, change `appPrefix`, not the org name.

`qm.config.jsonc` already mounts this repo's `skills/` into the agent.
Do not import a private git skill pack. Do not add a GitHub PAT.

## 3. Secrets and deploy

Follow `deployment.md` and `../deploy-qm/references/fly.md` (or `aws.md`).

```bash
npm ci
npm exec qm -- setup          # generates signing keys; prompts for the rest
npm exec qm -- slack render   # after publicUrl is final
npm exec qm -- check
# Fly: create the sandbox app first, as fly.md requires
npm exec qm -- secrets push
npm exec qm -- plan
npm exec qm -- up             # only after billing confirmation
npm exec qm -- check --live
```

`.env` is gitignored. Use `qm secrets set KEY` so values never hit shell
history. Never paste keys into chat.

## 4. Slack bot

Read `../deploy-qm/references/slack.md`.

- `"slack"` is already in `services`. Keep it if they want the bot.
- Run `npm exec qm -- outputs` and open the **bot** manifest creation URL
  (not a hand-built app).
- Install into **their** workspace. Create an app-level token with
  `connections:write`. Enter bot + app tokens in the Admin Slack card —
  not in git.
- Slack **sign-in** is a second, optional app. Only if they chose SSO:
  drop `"auth"` from `services`, set portal OIDC env as in `slack.md`,
  render, create the SSO app from the outputs URL.

## 5. Channels

Read `references/channels.md`. Create or reuse channels **in their
workspace**. Invite the bot. Prove it: mention the bot in `#agent-test`
and require a reply.

Do not copy channel names, standing orders, or workspace IDs from any
other company.

## 6. Handoff

Return the handoff block required by `deployment.md` §7, plus:

- which channels the bot is in, with Slack links
- that laptop Claude Code remains `./setup.sh` (unchanged, no `qm up`)
- `npm exec qm -- status` / `logs` / `rollback` / `down`

Do not claim done without a Slack reply in the test channel (if Slack
was requested) and a real web response with a generated sidebar title.
