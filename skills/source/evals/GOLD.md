# /source — Pre-registered acceptance (GOLD)

**Frozen: 2026-08-03, before any rebuild work.** Nothing below may be edited to make a run pass.
If a criterion turns out to be wrong, it is recorded as wrong in `RESULTS.md` and re-frozen for the *next* pass — never softened retroactively.

Maps to `evals/ACCEPTANCE.md` → **B6 source-v2**:
- `[auto]` 10 candidates for the test role: blind WHO-scorecard judge rates ≥ 8/10 A-grade with evidence
- `[auto]` 100% of evidence links resolve (HTTP 200)

---

## 1. The test role (frozen)

> **Founding Full-Stack Engineer — consumer AI hardware startup — San Francisco or remote US.**

Seed-stage, 6 people, shipping a physical consumer device with a companion app and a cloud backend. First non-founder engineering hire. Comp band $170–220k + 0.5–2.0%.

Machine-readable profile: `evals/fixtures/test-role.json` (frozen with this document).

### 1.1 Mission

Own the entire software surface between the device and the customer — companion app, device-facing API, provisioning/OTA plumbing, and the web funnel — so the company can put a working product in a stranger's hands and keep it working without a platform team. Success in 12 months = a shipped consumer product whose software failures are no longer the thing blocking hardware iterations.

### 1.2 Outcomes (ranked, measurable, time-bound)

| # | Outcome | A-player bar (already shipped this exact thing) | Weight |
|---|---|---|---|
| 1 | Companion app in both app stores, crash-free sessions ≥ 99.0%, by month 4 | Has personally shipped an app to a public store and owned its crash budget | High |
| 2 | Device↔cloud path live: provisioning, auth, telemetry ingest, OTA rollback, by month 5 | Has built software that talks to real hardware over BLE/USB/serial/Wi-Fi and survived a bad OTA | High |
| 3 | Backend that holds at 10k devices with p95 API < 300ms, by month 8 | Has run a production backend they personally designed, with real users | High |
| 4 | Public site + checkout + support flows converting, by month 3 | Has shipped a revenue-carrying web funnel end to end | Med |
| 5 | Second engineer onboarded and productive within 2 weeks of joining, by month 10 | Has been the person others onboarded onto a codebase they wrote | Med |

### 1.3 Competencies

**A. Technical** — full-stack ownership (frontend + backend + deploy, no handoffs); hardware-adjacent software (BLE/USB/serial/OTA/device telemetry); production operations (on-call, incident, rollback); pragmatic breadth over depth-in-one-layer.

**B. Cultural** — ships without a spec; talks to customers directly; writes down decisions; comfortable being the only person who knows a subsystem; does not require an existing platform.

### 1.4 A-BAR — the five legs (this is the filter)

A candidate is **A-grade only if every leg passes with cited, checkable evidence.** No averaging past a missing leg.

| Leg | Requirement | What counts as evidence |
|---|---|---|
| **L1 Shipped end-to-end** | Personally shipped a consumer-facing product covering frontend **and** backend **and** deploy | Named product + a public URL (store listing, live site, repo, launch post) |
| **L2 Hardware-adjacent** | Built software that talks to physical devices or real-time device data: BLE, USB/serial, MQTT, firmware/OTA, camera or sensor streams, robotics telemetry | Named project/role with a link or a first-person write-up |
| **L3 Startup autonomy** | Founder, founding/first-5 engineer, employee at a <20-person company, **or** solo maintainer of a real OSS project (≥ 200 stars or equivalent shipped-alone proof) | Title + company size, or repo link with star count |
| **L4 Geography** | SF Bay Area **or** explicitly available for US-remote (stated US work authorization or stated US-remote availability) | Profile location field, post text, or stated relocation |
| **L5 Checkable** | ≥ 2 distinct public evidence URLs, all resolving | The URLs themselves |

**Explicit exclusions (must appear in the excluded bucket with a reason, never in the ranked list):** ML researchers with no shipped product; pure mechanical/EE/PCB engineers; agency or contract-shop profiles with no owned product; founders currently fundraising (not recruitable); candidates whose only evidence is a login-walled resume; anyone failing L4 with no stated US-remote availability.

**Borderline handling:** exactly one failed leg with plausible-but-unshown evidence → **HOLD** bucket, naming the missing leg. Two or more → excluded.

---

## 2. Decision rule (frozen)

The rebuild is **ACCEPTED** only if:

1. **G1 (judge):** a submitted list of exactly 10 ranked candidates for the test role scores **≥ 8/10 A-grade** under the blind judge below, **and**
2. **G2 (links):** **100%** of evidence URLs in that list return HTTP 200 (redirect chains allowed; final status must be 200), **and**
3. **G3–G14 (deterministic):** every deterministic case below passes.

Any FAIL ⇒ not accepted. Any un-run case ⇒ `RESULTS.md` says PENDING and **must not** say ACCEPTED.

A full live sourcing sweep is **optional for this pass**. If skipped, G1 is `JUDGE-PENDING` and G2 is `RUN-PENDING`, and the rebuild is *not* accepted — it is "deterministics green, acceptance run pending".

---

## 3. Judge protocol (G1) — frozen

- **Judge model:** `gpt-5.6` (OpenAI). Different family from the generator (Claude). Key from `OPENAI_API_KEY`.
- **Blind:** the judge receives only §1.1–§1.4 of this file and the candidate list. It is never told which system produced the list, that a rebuild is being evaluated, or what the pass threshold is.
- **Temperature:** 0. **Runs:** 3, majority vote per candidate (ties → not-A).
- **Per candidate the judge must output:** `{name, legs: {L1..L5: {verdict: PASS|FAIL|UNSUPPORTED, quote}}, grade: A|HOLD|REJECT}`.
- **Grade rule given to the judge:** `A` iff all five legs are `PASS` with a quote drawn from the submitted entry. Any `UNSUPPORTED` ⇒ not `A`. Charitable inference is forbidden; absence of evidence is `UNSUPPORTED`.
- **Score:** `A_count = #{candidates with grade == A}` out of exactly 10. Threshold `A_count ≥ 8`.
- Runner: `scripts/judge_list.py --list <md> --scorecard evals/GOLD.md`.

## 4. Link resolution (G2) — frozen

- Extract every URL from the submitted candidate list.
- `GET` (fall back to `HEAD`→`GET`) with redirects followed, 15s timeout, 3 retries with backoff.
- **Pass = 100% final status 200.** 403 from a bot-walled host (LinkedIn) counts as **FAIL** for this metric — the skill must therefore cite evidence a reviewer can actually open. This is deliberate and is not to be relaxed.
- Runner: `scripts/verify_links.py --input <md>`.

---

## 5. Deterministic cases (G3–G14) — frozen

| ID | Check | Pass condition |
|---|---|---|
| G3 | No prior-company residue anywhere in `skills/source/` — case-insensitive recursive grep for the prior company name (exact pattern assembled in `run_cases.py`, constant `PRIOR_CO`, so this document does not trip its own check) | 0 hits |
| G4 | No personal absolute paths or personal-vault references in `skills/source/` (exact pattern in `run_cases.py`, constant `PERSONAL_PATHS`) | 0 hits |
| G5 | No hardcoded role/stack targets in `skills/source/scripts/`: `grep -riE 'kotlin|camerax|camera2|ncnn|tensorrt|vllm|libuvc|v4l2|shenzhen|嵌入式|固件'` | 0 hits |
| G6 | Every executable in `scripts/` runs `--help` | exit 0 for all |
| G7 | Every scraper runs `--dry-run` with no network | exit 0, stdout contains `DRY RUN`, for all |
| G8 | Parameterization is real: same scraper, two different profiles, `--dry-run` config dumps differ | non-empty diff |
| G9 | Profile validation rejects a malformed profile (`evals/fixtures/bad-role.json`) | exit ≠ 0, stderr names the missing field |
| G10 | Scripts are stdlib-only (no pip install needed to run the sweep) | AST import scan finds no third-party module outside an optional-guarded `try:` |
| G11 | `scripts/credentials.example.json` exists, parses, and holds no real secret | all values empty or `<...>` placeholders |
| G12 | Credentials resolve from env and from `~/.hiring-scraper/credentials.json`, env winning | unit check exits 0 |
| G13 | SKILL.md: valid frontmatter (`name`, `description` non-empty), ≤ 200 lines, ≥ 3 files in `references/` | all true |
| G14 | Both runtimes documented: SKILL.md matches `/qm|sandbox/` **and** every MCP-dependent step is marked optional/guarded | regex present; manual read confirms |

**Network-dependent supplementary cases (recorded, not blocking):**

| ID | Check | Pass condition |
|---|---|---|
| N1 | `verify_links.py` self-test: known-200 URL passes, known-404 URL fails | exit 0 then exit ≠ 0 |
| N2 | Live smoke: HN scraper, 1 thread, test-role profile | exit 0, writes a report file |
| N3 | `judge_list.py` harness self-test on `evals/fixtures/judge-smoke.md` | returns parseable per-leg JSON for every entry |

N1–N3 prove the harness works. They do **not** substitute for G1/G2.

---

## 6. What is explicitly NOT tested this pass

- Real candidate quality from a live multi-source sweep (that is G1/G2, deferred by choice).
- Auth-gated sources (YC WaaS candidate side, LinkedIn/Unipile) — no credentials in the eval environment.
- PDF rendering (`make_pdf.sh`) — depends on `pandoc`/`weasyprint` being installed; recorded as environment-dependent, not blocking.
