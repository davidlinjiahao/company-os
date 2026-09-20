# Source reference

Read during **Phase 5**. Honest yields, not brochure claims.

The single most important distinction: **public job-seeker feeds find people who are looking; targeted lanes find people who are good.** A-players are usually in the second group. Run both, but do not mistake volume from the first for progress.

---

## The scripts

All in `scripts/`. Standard library only — no pip install, so they run unchanged in a sandbox. Every one takes `--profile <role.json>` and supports `--dry-run` (prints the exact queries, makes no network calls) and `--help`.

| Script | Source | Auth | Honest yield |
|---|---|---|---|
| `hn_hired.py` | HN "Who wants to be hired" monthly threads, ~6 months back | none | Good for generalist and US-remote roles. People self-describe in mainstream terms, so niche specialisms are near-invisible here. |
| `reddit_forhire.py` | r/forhire + role-relevant subs via RSS | none | Medium and getting worse — RSS returns ~25 posts, no pagination, and Reddit 403s datacentre IPs. A trickle source to re-run, not a sweep. Blocked feeds are reported, not hidden. |
| `v2ex_cv.py` | V2EX `/go/cv` self-posted CVs | none | Off by default. Enable only when the role genuinely accepts that market, and put the matching non-English terms in the profile yourself. |
| `github_contributors.py` | Curated repos + trending, per language | `GITHUB_TOKEN` recommended | **Best script lane.** The curated-repo half is high signal; the trending half is noisy breadth. Without a token you get 60 req/hr and a tiny crawl. |
| `yc_waas.py --mode jobs` | YC Work at a Startup public board | none | Mostly calibration: who else is hiring this role, what they pay, where. Use it in Phase 4. |
| `yc_waas.py --mode candidates` | WaaS candidate side | `WAAS_COOKIE` | Real candidate profiles when the cookie is live. Cookies expire; the script detects the login bounce and says so. |
| `merge.py` | all of the above | none | Cross-source identity dedupe (email, lone GitHub handle, lone X handle). Anyone appearing in 2+ independent sources gets ranked first. |
| `verify_links.py` | — | none | Resolves every URL in a finished list. Exit 0 only if all return 200. |
| `judge_list.py` | — | `OPENAI_API_KEY` | Optional. Has a different model family grade the finished list blind against the same A-bar legs. |
| `sweep.sh` | orchestrator | — | Runs every lane, merges, then prints which lanes were un-swept. |
| `make_pdf.sh` | — | pandoc + weasyprint | Optional clickable PDF. Exits 3 with a clear message when the tools are absent. |

## Lanes with no script (run these as agents — see `references/agents.md`)

| Lane | How | Honest yield |
|---|---|---|
| **Competitor employees** | From Phase 4, enumerate named engineers in the target function at each comparable company. Exclude founders — not recruitable. | **Usually the highest-value pool in the whole sweep.** Nobody here is publicly looking, which is precisely why they are still available. |
| **Targeted web / Exa** | People search + company-roster crawls. MCP locally; `EXA_API_KEY` over curl in a sandbox. | Solid for named people and rosters. Person-search endpoints time out under load — fall back to general web search with a people-shaped query. |
| **LinkedIn graph (Unipile)** | 1st/2nd-degree search, mutual connections, warm-intro routing. Needs `UNIPILE_DSN` + `UNIPILE_API_KEY`. | Good for *warmth*, weak for *proof*: profile responses often lack work history, so verify every A-bar leg elsewhere. LinkedIn URLs are bot-walled and fail link verification — cite something openable instead. |
| **Conference talks, papers, patents, changelogs** | Search for who *presented* the thing your outcome describes. | Slow, small, and disproportionately A-players. Worth an hour on a senior role. |
| **Communities behind a login** (Discords, Slack groups, alumni lists) | Not scrapeable. Ask the user to look, or skip. | Report as a blind spot needing the user, never as swept. |

---

## Credentials

Resolution order: **environment variable → `~/.hiring-scraper/credentials.json`**. Environment always wins, which is how a sandbox supplies them. Override the file path with `HIRING_SCRAPER_CREDENTIALS`. Copy `scripts/credentials.example.json` to get started; every field is optional.

No script reads a personal vault, a keychain, or a hardcoded path. A missing credential **skips one lane with a printed message** and never fails the sweep — but the skipped lane must appear in the depletion tracker.

Refreshing `WAAS_COOKIE`: open workatastartup.com logged in → DevTools → Network → any request → Request Headers → copy the entire `Cookie:` value.

---

## Reading the sweep output

Reports land in `./candidates/` (or `$SOURCE_OUT_DIR`, or `--out`), named `<date>_<role-slug>_<source>.md`. `merge.py` writes `<date>_<role-slug>_merged.md`.

The keyword `score` in these files is a **triage number**, not a grade. It says "a human should look at this", nothing more. High score with no A-bar evidence is a reject. Low score with an obvious A-bar hit is a list entry. The bar is the legs, always.
