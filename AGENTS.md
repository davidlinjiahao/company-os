# Company OS — agent instructions

If you were asked to **set up**, **install**, or **deploy** this repository
(including Slack and channels), do not improvise. Read and follow, in order:

1. `.codex/skills/company-os-deploy/SKILL.md` — Company OS wrapper: this repo
   is already a QM deployment. Do **not** run `qm init`. Stamp the slug, collect
   secrets, deploy, then Slack bot + channels.
2. `.codex/skills/deploy-qm/SKILL.md` and `deployment.md` — the upstream QM
   operator workflow (health, sign-in, live canary).
3. `.codex/skills/deploy-qm/references/slack.md` — Slack bot vs Slack sign-in.
4. `.codex/skills/company-os-deploy/references/channels.md` — which channels
   to create or join, and what the bot is allowed to do in them.

Laptop-only onboarding (Claude Code on a Mac, no cloud agent) is `./setup.sh`
and `skills/setup/SKILL.md`. That path never runs `qm up`.

Never commit `.env`. Never copy another organization's Fly apps, bucket names,
portal hostnames, signing keys, or Slack workspace IDs. Never print secrets.

# QM deployment

This repository is a Company OS checkout that is also one QM deployment.
QM is the open-source multiplayer agent harness from Y Combinator
(https://github.com/yc-software/qm). The runtime is the published npm
package `@yc-software/qm`, not a copy of that source tree.

This directory holds a config, a secret contract, and a sandbox layer that
customizes the agent without forking the core images. Commit everything
here except `.env`, which holds the secret values and is covered by
`.gitignore`. Do not copy another organization's Fly apps, bucket names,
or signing keys into this file set.

## Where the documentation lives

- `package.json` pins the exact CLI version this directory is interpreted by,
  so every checkout resolves the same `qm`. `contract` in the config is only
  the coarse compatibility floor; this pin is the reproducible one. Upgrade it
  deliberately and re-run `qm check` afterwards.
- `qm.config.jsonc` describes what to run. Every field carries a comment
  explaining it, including the full list of services, so read the file itself
  before changing it. It is JSON with comments (the `tsconfig.json` dialect).
  That applies only to the config: `tool.json` files must stay strict JSON.
- `.env.example` is the secret catalog. It lists every secret the platform
  knows, what each one is for, what enables it, and the command that produces a
  value when one exists. The secrets the current config needs appear uncommented.
  `qm init` creates a gitignored `.env`, generates its local signing
  keys, and leaves provider credentials blank for you to fill in. Never write a
  secret value into any other file.
- `slack-app-manifest.yml` creates the optional qm bot app. Slack OIDC
  deployments also get `slack-sso-manifest.yml`. Run
  `npm exec qm -- slack render` after changing `publicUrl`, then
  `npm exec qm -- outputs` for creation links.

## Customizing the sandbox

`sandbox/` defines what the agent gets in its execution environment:

- A skill is `sandbox/skills/<id>/SKILL.md`: markdown with `name` and
  `description` frontmatter that teaches the agent a workflow and when to use it.
- A tool is `sandbox/tools/<id>/tool.json`: a descriptor whose minimal form is
  `{ "id": ..., "advertise": ..., "install": { "binary": ... } }`, with the
  executable next to it when the binary is not already in the base image.
- `sandbox/Dockerfile` is optional and only needed for system packages or
  runtimes.

The scaffold ships a working example, the `greet` skill and `example-tool`.
Copy its shape, then replace or delete it.

## The workflow

Run every command from this directory.

1. `npm exec qm -- check` validates the config and the sandbox layer and prints the
   secret names the config currently requires. It builds nothing, and when
   credential values are already present in `.env` it also verifies them
   against their providers, so run it after every edit.
2. `npm exec qm -- plan` reports what deployment would do
   without changing anything.
3. After the target prerequisites are complete, `npm exec qm -- up` brings the
   deployment up and prints the URLs. An AWS directory must first complete the
   edge and authenticated-portal steps in its AWS bootstrap section below.
   `--build-from <path to a QM checkout>` builds modified runtime code
   from your source fork or a contributor checkout.
4. `npm exec qm -- status`, `npm exec qm -- logs [service]`, and
   `npm exec qm -- down` show
   what is running, tail logs, and stop the deployment.
5. `npm exec qm -- secrets push` uploads the `.env` values to the deploy target.
   The docker target reads `.env` directly and does not need it.

`npm exec qm -- help` lists everything else, including `sandbox build` and
`rollback`.
