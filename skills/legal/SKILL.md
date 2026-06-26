---
name: legal
description: Redline a contract document. Walks through material terms one-by-one to capture the user's position via AskUserQuestion, generates a redlined .docx with deletions struck and insertions in red (tone matched to the business goal), and produces a counterparty-facing summary PDF in concise plain English. Use when the user provides a contract (.docx or .pdf) and asks for a redline, contract review, term-by-term negotiation prep, or a discussion summary.
user-invocable: true
argument-hint: "[path to contract file]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# /legal — Contract Redline Workflow

Walk a contract section-by-section, capture the user's position on each material term, produce a clean redline, and generate a counterparty-facing summary PDF.

**Announce at start:** "I'm using the /legal skill to walk this contract term-by-term."

## When to invoke

User provides a contract (.docx or .pdf) and asks to:
- Redline / mark up / negotiate
- Review for problematic terms
- Prepare a counter-proposal
- Generate a discussion summary for a counterparty call

## Phase 1: Intake

1. Read the document
   - `.docx` → use `python-docx` to enumerate paragraphs with their indices
   - `.pdf` → use the `Read` tool with `pages:` parameter for large files
2. Extract paragraph-level structure; preserve original section numbers
3. Identify:
   - Counterparty name
   - Contract type (PO, MSA, NDA, SAFE, License, etc.)
   - User's role in the deal (Buyer, Seller, Customer, Vendor, Licensor, Licensee)
4. Report back briefly: "Read the [type] from [counterparty]. You are [role]. Found N material clauses. Walking them one at a time."

## Phase 2: Clarify Business Goals (term by term)

**Use AskUserQuestion. One term at a time. Do not batch.**

Start with two framing questions:

1. **Posture** — Partnership-friendly / Balanced / Defensive
2. **Closing pressure** — Time-sensitive (concede speed) / Standard / Patient (hold positions)

Then walk material terms in this order. Skip any clause not present in this contract.

| Order | Term | Question shape |
|---|---|---|
| 1 | Liability cap | Capped (12 mo fees / PO value / fixed amount)? Uncapped? Carve-outs? |
| 2 | Indemnification | Mutual or one-way? Carve-outs (IP, confidentiality, gross negligence)? Within or outside the cap? |
| 3 | Warranties | Bounded duration (months)? Repair/replace remedy? Disclaim implied warranties? Recall costs follow fault? |
| 4 | Acceptance / formation | Mutual signature required? Deemed acceptance? Lapse date? |
| 5 | Inspection / acceptance window | Bounded window with deemed acceptance? Right to revoke acceptance? |
| 6 | Cancellation | Cancel-for-convenience? Defect-based framework? Cure → return cascade? |
| 7 | Acceptance criteria | Subjective standard or material non-conformance? Cure period? |
| 8 | Payment | Net terms? Advance payment refundability? |
| 9 | Insurance | Specific limits or thin "commercially reasonable"? |
| 10 | Pricing structure | Flat? List + discount? Tied to follow-on commitments? |
| 11 | Most-Favored-Nation | Strike, accept, or limit? |
| 12 | Resale / sublicense | Allowed, restricted, or strike? |
| 13 | IP / data ownership | Who owns work product or captured data? License back? |
| 14 | Underlying / platform IP | Reverse-engineering prohibited? Third-party components? |
| 15 | Logo / marketing | Mutual logo license? Customer references? |
| 16 | Quiet use / injunctive relief waiver | Strike? Mutual? |
| 17 | Confidentiality | Term length? Mutual? |
| 18 | Governing law / venue | Acceptable as-is? |

For each, present the original clause and the user's options:
- "Original §X says: [plain English summary]. Your position: [options]"

Track decisions in a TodoList so the redline phase has a complete instruction set.

## Phase 3: Generate Redline

Apply edits using `python-docx`. Save to `~/Desktop/<original name> Redline.docx`.

Use the helper script at `redline_helper.py` (see `Helpers` section).

**Redline conventions:**
- Deletions: red text + strikethrough — `run.font.color.rgb = RGBColor(0xC0,0,0); run.font.strike = True`
- Insertions: red text, no strikethrough
- New section headers: red text, bold

**Tone matching the business posture:**

| If posture is... | Then... |
|---|---|
| **Partnership** | Title-case headers, "the parties shall," soft prohibitions ("Buyer will use commercially reasonable efforts to ensure that..."), no irreparable-harm language, no remote-disable / weaponized remedies, frame penalties as "true-ups" not "rescissions," reference neutral industry analogues ("same structure as comparable deals in this category") |
| **Balanced** | Standard contract phrasing, mutual where possible, specific carve-outs, neutral remedies |
| **Defensive** | All-caps section headers (matches the boilerplate convention), explicit prohibition lists "(i)...(ii)...(iii)..." structure, irreparable-harm language for IP/confidentiality, explicit injunctive-relief preservation |

**Filler to remove (always — regardless of posture):**

| Don't write | Why |
|---|---|
| `[REVISED — ...]`, `[FLAG — ...]`, `[PROPOSED — ...]` brackets | Editor's notes, not contract text |
| `(revised)` markers in section titles | Strikethroughs already show the change |
| Lawyer-stack adjectives ("perpetual, irrevocable, worldwide, fully paid-up, sublicensable, royalty-free") | "Non-exclusive royalty-free" + "survives termination" gets the same legal effect |
| Exhaustive enumeration when 2-3 examples cover it | Long lists read as defensive |
| Internal commentary ("This protects us from...") | Contract is for the counterparty, not for the lawyer |
| "Buyer shall ensure that its consignees... shall not" | Use "Buyer will use commercially reasonable efforts to ensure that... do not" instead |

**Don't volunteer concessions.** If the user didn't ask for it (source escrow, AI status, specific insurance limits, SLAs, AR/waiver of subrogation), don't add it. Volunteering teaches the counterparty to ask for more.

**Verify after every batch of edits:** Re-open the saved .docx, confirm strikes landed and red insertions exist for each intended change. Curly apostrophes (U+2019) are the most common silent failure — try both `'` and `'` when matching strings.

## Phase 4: Generate Summary PDF

Use ReportLab to create `~/Desktop/<original name> Summary.pdf` in landscape letter format.

Use the helper at `summary_pdf.py`.

**Columns:** `# | Section | <Counterparty> Version | <User-org> Version | Discussion`

**Structure:**
1. Brief intro paragraph (1-2 sentences) — what this is, organized in suggested discussion order, what's NOT changing (commercial deal economics)
2. Group rows by topic with section header bars in this order:
   1. Commercial structure (pricing, follow-ons, core deal terms)
   2. Risk allocation & liability (warranty, cap, indemnity, insurance)
   3. Operational mechanics (acceptance, inspection, payment, termination)
   4. Partnership architecture / new sections (data, IP, logo, mutual licenses)
   5. Cleanup (struck items)
3. Brief sign-off line at end ("Looking forward to talking through this. — [name]")

**Cell content rules:**
- Each cell ≤ 2 sentences. Vital elements only.
- "Counterparty Version" = what the original PO said in plain English (e.g., "Lowest-price-ever guarantee, retroactive.")
- "User Version" = what we propose in plain English (e.g., "Struck.")
- "Discussion" = ONE-LINE rationale ("Standard hardware warranty.", "Industry standard.", "Closes a refund loophole.")
- The Discussion column is for the counterparty to read, not the user. No internal coaching, no "they'll never agree to this," no negotiation tactics.
- Highlight nothing. Let the order do the emphasis.

**Defaults:**
- Page: landscape letter, 0.4" margins
- Font: 9pt body, 10pt group headers, 16pt title
- Colors: navy header `#1F3A5F`, light blue group bars `#D9E2EC`, light gray banding `#F4F6FA`

## Phase 5: Output & Hand-off

Tell the user:
1. Redline saved to `~/Desktop/<name> Redline.docx`
2. Summary saved to `~/Desktop/<name> Summary.pdf`
3. One-paragraph recap: number of edits by category (struck / replaced / new sections)
4. Any open questions that came up during drafting that they should think about (e.g., "Confirm with broker that umbrella is bound before sending")

Do not auto-send to the counterparty. Drafting → human review → user sends.

## Helpers

Two reusable Python helpers live in this skill directory:

- `redline_helper.py` — `RedlineDoc` class wrapping `python-docx`:
  - `strike_substring(p, text)` — strikethrough + red color a substring within a paragraph (handles multi-run text)
  - `replace_paragraph_text(p, old, new_red)` — combined strike + insert
  - `strike_paragraph(p)` — strike entire paragraph
  - `add_section_after(anchor, header, body)` — clean new-section insertion
  - `verify_edits(checks)` — post-save verification

- `summary_pdf.py` — `build_summary_pdf(groups, output_path, title, intro, signoff)` — produces the standard landscape table format

## Common pitfalls

1. **Curly apostrophes.** Source contracts use `'` (U+2019), not `'`. Check both when matching.
2. **Multi-run text.** A `.docx` paragraph may span dozens of runs at formatting boundaries. When replacing text, capture run-level format data, modify the concatenated text, then rebuild runs grouping consecutive characters with identical formatting.
3. **Don't volunteer concessions.** See Phase 3.
4. **Tone drift in the summary.** The Discussion column ships to the counterparty. Every cell should be defensible if quoted back.
5. **One question at a time.** Batching ten questions into one `AskUserQuestion` creates decision fatigue and produces worse positions. Walk them.
6. **Verify after every edit batch.** Strikes silently fail when text doesn't match exactly (whitespace, curly quotes, run boundaries). Always re-read and check.
7. **The summary is not the redline.** The redline is for the counterparty's lawyer. The summary is for the counterparty's business owner. Different audience, different language.

## Quick Reference

| Phase | When to skip | Output |
|---|---|---|
| 1. Intake | - | Section count + counterparty + role identified |
| 2. Clarify (term-by-term AskUserQuestion) | Never skip | TodoList of decisions |
| 3. Generate redline | - | `<name> Redline.docx` on Desktop |
| 4. Generate summary | If user only wants the redline | `<name> Summary.pdf` on Desktop |
| 5. Hand-off | Never skip | Recap + open questions |
