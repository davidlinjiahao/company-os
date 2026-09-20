# Agent lanes and loop mechanics

Read during **Phase 5**. The scripts cover feeds. These prompts cover everything a feed cannot reach — which is where the A-players are.

## How to dispatch

One subagent per lane, in parallel, each with its own context. Every agent gets the same four things and returns the same shape:

**Give each agent:**
1. The **mission paragraph** and the **A-bar legs, verbatim** — not a paraphrase.
2. The **exclusions** list.
3. Its lane's specific instruction (below).
4. The names already found, so it does not re-report them.

**Require back from each agent — nothing else:**
```
A-GRADE
  <name> — <profile url>
    L1: <verdict> — "<quoted evidence>" <url>
    L2: ...
    route-in: <warm intro path, or cold>
    one-line why: <the single strongest reason>

HOLD
  <name> — missing <Ln>; <what would settle it>

EXCLUDED (counts only)
  <reason>: <n>

LANE STATUS
  swept: <what was actually covered>   blocked: <what stopped, and why>
```

Instruct every agent explicitly: **absence of evidence is UNSUPPORTED, not PASS.** Returning three real candidates is a success. Returning twenty maybes is a failure that costs the orchestrator more work than the agent saved.

---

## Lane prompts

**Competitor employees.** "For each of these companies, find named engineers currently in <function>. Exclude founders and C-level — not recruitable. For each person, find public evidence for each A-bar leg with a URL. Prioritise people whose *personal* work matches the legs, not people whose employer sounds impressive."

**Targeted web / Exa.** "Find people who have publicly demonstrated <the exact thing leg L1 and L2 describe> — conference talks, technical blog posts, launch threads, papers, or a repo they own. Search for the artefact, not the job title. Then check the remaining legs on each person found."

**LinkedIn graph.** "Search 1st and 2nd-degree connections for <role keywords + geography>. Return network distance and the shared connection for each. Do not assert work history from a LinkedIn headline — headlines are self-written marketing. Verify every leg against an independently openable source and cite that instead."

**GitHub deep-dive.** "Beyond the script's curated repos: for each of these repos, read the contributor list, then read the top contributors' own repositories and recent commits. A person's own projects say more about what they will do here than a drive-by pull request on a famous repo."

**Boards and communities.** "Sweep <boards>. Report honestly if a board is gated, empty, or dead — an un-swept lane recorded as swept is worse than no lane at all."

---

## Looping to depletion

Sourcing converges; it does not finish. Each round:

1. Dispatch the lanes not yet run, or re-run a source that refreshes (HN monthly, Reddit continuously).
2. **Dedupe** against the running list by name *and* profile URL.
3. **Append** to the output file — never rewrite it from scratch.
4. Update the depletion tracker.

**Stop when** two consecutive rounds add no new A-grade or HOLD candidate, **or** every named lane is resolved or dead-ended. Then write the closing summary. Do not keep looping for the appearance of effort.

### Depletion tracker (goes in the deliverable)

```
## Source depletion — round N

SWEPT       hn (6 threads) · github curated (22 repos) · waas jobs · competitor employees (4 of 6 companies)
PENDING     competitor employees (2 companies) · conference talks 2024-25
BLOCKED     waas candidates — WAAS_COOKIE not set
            r/forhire — feed 403 from this network
            <private community> — login-walled, not scrapeable

NEEDS YOU   1. WAAS_COOKIE (unlocks the YC candidate side)
            2. GITHUB_TOKEN (60 → 5000 req/hr; the curated lane is currently crawling at 3 repos)
            3. Warm intro to <person> — reaches <n> of the Tier-1 candidates
```

The **NEEDS YOU** section is the most valuable part of the tracker. It converts your blocked lanes into a short list of actions only the user can take. Always include it, even when it is empty — an empty one is itself information.
