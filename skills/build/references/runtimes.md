# Two runtimes: local Claude Code and the restricted sandbox

`/build` has to produce the same *decisions* in both places. What differs is the tooling
available to execute them — so every phase has a degraded path, and no phase is allowed to
hard-require anything beyond a shell, a filesystem, `curl`, and environment variables.

**Detect the runtime once, at Phase 0, and say which one you are in.** Getting this wrong
wastes a whole run on tool calls that will never resolve.

```bash
# Cheap runtime probe — no failures, just facts
command -v git    >/dev/null && echo "git: yes"    || echo "git: no"
command -v python3 >/dev/null && echo "python3: yes" || echo "python3: no"
[ -d "$HOME/.claude/skills" ] && echo "local skill dir: yes" || echo "local skill dir: no"
[ -n "${ANTHROPIC_API_KEY:-}" ] && echo "api key: present" || echo "api key: absent"
```

---

## Capability matrix

| Capability | Local Claude Code | restricted sandbox | Degraded path when absent |
|------------|-------------------|-----------|---------------------------|
| Practice skills (superpowers, frontend-design, dataviz) | Yes | Usually yes — bundled with the agent, not the machine | If a skill will not load, follow its phase from `routing.md` by hand and record that you did |
| Sub-runner fan-out for parallel work | Yes | Often unavailable | Run the tasks serially in one session; the ordering guarantees are unchanged, only the wall-clock |
| Interactive question-asking of the user | Yes | No — the run is unattended | Choose the option you would have recommended, record the assumption in `ACCEPTANCE.md` under "Assumptions", and flag it in the summary |
| Connected data services (Notion, Drive, calendar, vault) | Yes | **No** | Never make one a prerequisite. Read what you need from files in the repo, or state the input as missing |
| Browser automation / visual QA | Yes | No | Emit a manual QA checklist instead of screenshots |
| Workflow gate hook, TDD Guard hook | If installed | No | Guarded commands no-op; enforce the same rules conversationally (see `safety.md`) |
| Prompt-security suite | If installed | Usually no | Skip and record the gap in the summary |
| `git` | Yes | Yes | — |
| `curl` + API keys from env | Yes | Yes | This is the only sanctioned network path in the sandbox |
| LLM judge for eval cases | Yes | Only with a key in env | Mark judge cases `JUDGE-PENDING`. Never score them as passes |

---

## The guarding rule

Any step that depends on something outside {shell, filesystem, git, curl, env vars} is
written as a conditional with a stated fallback. The shape is always the same:

```bash
if command -v promptfoo >/dev/null 2>&1; then
  promptfoo redteam eval
else
  echo "SKIPPED: prompt-security suite not installed — recorded as a gap in the summary"
fi
```

Three things make this correct rather than decorative:

1. **The absent branch says something.** A silent skip is indistinguishable from a pass.
2. **The gap reaches the summary.** The user prices the risk; you do not price it for them.
3. **The check is on the capability, not the runtime name.** `command -v promptfoo` keeps
   working when the sandbox gains the tool next month. `if [ "$RUNTIME" = "qm" ]` does not.

---

## What never changes between runtimes

The sandbox is a smaller toolbox, not a lower standard. All of the following hold in both:

- Acceptance is pre-registered before implementation.
- TDD is the spine: failing test, red output shown, then code.
- The five CRITICAL safety items are reviewed on the real diff.
- No secrets in source.
- Claims are backed by fresh command output, pasted, not remembered.
- Every skipped phase is named in the run log with its reason.

If a constraint cannot be met in the sandbox, the run does not lower the bar — it stops and
reports what it could not verify. "Unverified" is a legitimate outcome. "Assumed fine" is not.
