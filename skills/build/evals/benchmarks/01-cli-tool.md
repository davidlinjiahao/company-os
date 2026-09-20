# Benchmark 01 — CLI tool

**Task type:** greenfield, single-file, no UI, no network.
**Runtime:** must complete in both local Claude Code and the restricted sandbox.

## Brief

Build `dupefind`, a command-line tool that reports duplicate files in a directory tree.

```
dupefind [PATH] [--min-size BYTES] [--json] [--follow-symlinks]
```

- Groups files by identical content, not by name.
- Default output: one group per blank-line-separated block, largest group first, each line
  a path. Exit 0 when duplicates are found, 0 when none (finding nothing is not an error).
- `--json` emits `[{"hash": "...", "size": 123, "paths": [...]}, ...]` to stdout.
- `--min-size` skips files smaller than N bytes (default 1 — never report empty files).
- Symlinks are not followed unless `--follow-symlinks`; a symlink loop must not hang.
- Unreadable files are reported on stderr and skipped; the run still exits 0.
- No third-party dependencies. Python 3.11+ standard library only.

## Acceptance

The run is accepted when all of these are true:

1. `ACCEPTANCE.md` and `evals/cases.json` exist and were committed **before** the first
   commit containing implementation code (check with `git log --diff-filter=A`).
2. A loop driver (`loop.sh` + `acceptance_check.sh`) exists and is executable.
3. `acceptance_check.sh` exits 0, and it runs a real test suite — not `echo ok`.
4. Test suite covers, at minimum: identical content with different names; a file that is a
   prefix of another (must not collide); `--min-size` filtering; empty files excluded by
   default; symlink loop terminates; unreadable file skipped without a non-zero exit.
5. The first test commit precedes the first implementation commit for every unit of work.
6. `dupefind --json` output parses as JSON in a fresh shell.
7. No network access and no third-party imports anywhere in the tool.

## Expected artifact set

```
ACCEPTANCE.md
evals/cases.json
loop.sh                 (executable)
acceptance_check.sh     (executable)
progress.md
<source> + <tests>
```

## What is being measured

Routing (does `brainstorming` fire before code? is `writing-plans` skipped for a task this
small?), TDD discipline, acceptance-first discipline, and code quality under the judge rubric.
