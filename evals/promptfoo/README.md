# Promptfoo Security Evals

Adversarial testing for prompts used by company-os agents.

## Run

```bash
cd evals/promptfoo

# Baseline tests in promptfooconfig.yaml
promptfoo eval

# Generate hundreds of adversarial variants from the redteam config,
# then run them
promptfoo redteam generate
promptfoo redteam eval

# View results in browser
promptfoo view
```

## What to extend

1. Replace the generic prompt in `promptfooconfig.yaml` with actual prompts
   from your skills (`skills/build/SKILL.md`, a code-reviewer subagent when
   defined, a research skill's pre-processing prompt, etc.).
2. Add provider entries to compare resistance across models. The model id in
   `promptfooconfig.yaml` is a placeholder (`anthropic:messages:claude-opus-4-x`) —
   swap in the exact model ids you run.
3. Tighten the redteam `purpose` block as your agents take on new surfaces
   (e.g. contracts, meeting transcripts, web content ingested by skills).

## Notes

- Requires `ANTHROPIC_API_KEY` in env: `export ANTHROPIC_API_KEY=...`
- Each `redteam generate && eval` run can cost a few dollars in API calls.
- Results land in `~/.promptfoo/output/`.

## Integration with /build

Run this scaffold whenever a change touches a prompt-bearing file — a
`skills/*/SKILL.md`, a subagent prompt, or any model system prompt — to catch
prompt-injection / PII-leak / jailbreak regressions before shipping:

```bash
cd evals/promptfoo && promptfoo redteam generate && promptfoo redteam eval
```

Wire this into `/build`'s verification phase as a "Prompt-Security Eval" step
(gated on a prompt-bearing diff) so it runs automatically on relevant PRs.
