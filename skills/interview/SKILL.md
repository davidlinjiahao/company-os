---
name: interview
description: Use when you share a Plaud share URL (web.plaud.ai/s/pub_...) and want the key insights / notes from that recorded interview or call, in a terse bullet style. Also triggers on "notes from this interview", "insights from this Plaud", "/interview <url>".
user-invocable: true
disable-model-invocation: false
argument-hint: "<plaud share url> [more urls] [--notion]"
allowed-tools: Bash, Read, Write, WebFetch, Task, AskUserQuestion, mcp__plaud__*, mcp__notion__*
---

# Interview Skill

Turn a Plaud share URL into terse interview notes — the top 3-5 insights per call.

Context: these are usually customer-discovery / user interviews. You are the interviewer; focus on the **interviewee's** views (the other speaker), not your own.

## Quick Reference

```
/interview <plaud_url>                 # Notes from one call
/interview <url1> <url2> ...           # Batch — one block per call (fan out subagents)
/interview <url> --notion              # Also append to a Notion page
```

## Pipeline (per URL)

### 1. Resolve the share URL → Plaud file_id

The share page is JS-rendered — **WebFetch/curl return only the recording TITLE, never the transcript.** Use the title to find the file in your own Plaud account.

```bash
URL='<paste share url>'
curl -sL "$URL" | grep -oiE '<title>[^<]*</title>' | sed -E 's#</?title>##g'
```

That prints the exact recording title, e.g. `[Customer - Jane Doe Interview] 06-29 Product Discovery Call...`.

Then find its `file_id`:
- Note the `MM-DD` date in the title. Call `mcp__plaud__get_files` with `start_date`/`end_date` bracketing that date (ISO, e.g. `2026-06-29`), `limit: 300`.
- Match the returned `filename` to the title → grab its `id`. (Prefer the full-length recording over 5-second fragments with the same name.)

**Do NOT use `mcp__plaud__search_transcripts` for resolution** — it searches client-side and frequently returns empty even when the file exists.

**Dead-link guard:** if the extracted title is just the generic `Plaud.AI` (no `[...]`/`MM-DD` recording title), or the page's iframe `src` points to `.../nshare/invalid`, the share link is expired or invalid. Report that the link is dead and stop — do NOT fabricate a title, date, file_id, or notes.

### 2. Get the full transcript

Call `mcp__plaud__get_transcript(file_id)`.
- Long calls (>~40 min) exceed the token limit and are **persisted to a file** — the result tells you the path. Read the transcript from the `.transcript` field, not via Read offset/limit:
  ```bash
  python3 -c "import json,sys; print(json.load(open('<PATH>'))['transcript'])"
  ```
- Speaker labels may be generic (`Speaker 2`/`Speaker 3`). Infer which speaker is the interviewee vs the host (you are typically Speaker 1).

### 3. Extract the notes

Read the transcript **in full** before writing. Dispatch a subagent per call (Task tool) — giving it the transcript file path + the Output Contract below, returning the finished block — when the transcript was **persisted to a file** (large call) or you're processing **multiple URLs**, so raw transcripts stay out of the main context. If the transcript came back inline (short single call), extract inline.

## Output Contract (match this exactly)

Nested markdown bullets, one block per person:

```
        - <Name>, <Company/Role>
            - <insight 1>
            - <insight 2>
            - <insight 3>
            - <insight 4 (optional)>
            - <insight 5 (optional)>
            - 🔗 domain.com · domain.com   (only if tools/companies were named; omit otherwise)
```

**Header line:** exactly `- <Name>, <Company>` (or `<Name>, <Role>`). Do NOT append a company description or product blurb to the header — that belongs in a bullet only if it's an insight.

**Body:** exactly **3-5** insight bullets (hard cap — the 🔗 line does not count), then the optional 🔗 line. If you have more than 5, keep only the 5 most decision-relevant.

**Each insight bullet:**
- Terse, telegraphic, ~5-15 words. **First-person / interviewee voice** ("I override every alarm...", "wants a pulse on..."), NOT third-person bio ("Sam is a founder who..."). No sub-clauses, no hedging, no paragraphs.
- Is an **insight** — a pain, a want, a rejection, a trust/privacy stance, a form-factor opinion, or willingness-to-pay. Never spend a bullet on background or funding history.
- Grounded in something they actually said. Prefer **specific** (real numbers, names, tools, tactics, verbatim phrasing) and **non-obvious/contrarian** over generic.
- Coverage priority when choosing which 3-5: sharpest pain / drop-the-ball moment → what they *want* vs *reject* → trust/privacy stance → form-factor opinion → willingness-to-pay → tool stack.

**Style calibration — the target voice (illustrative):**
```
- Maya Okonkwo, Northwind
    - I want an assistant that tells me the one thing to do next, and why
    - Won't build it myself — every agent I wire up breaks and I forget it
    - Investors are a bad market; they don't adopt new tools
    - Reject the wrist; ambient audio is the only form factor I'd wear
    - 🔗 example-tool.com
- Devin Park, Beacon
    - Problem aware — built a company "second brain," team loves it
    - Wants a pulse on where things are and what to work on
    - Trying a new agent has real switching cost (re-connecting data)
    - Biggest pain is steering the team and staying focused
```

Deliver the block(s) in chat. **Flag that 🔗 URLs are speech-transcribed and approximate** — verify before relying.

## --notion

Append the block(s) to a Notion page using `mcp__notion__append_blocks` (the enhanced block API — never the markdown converter, which mangles bold to literal asterisks). Per person: a `heading_3` "Name, Company", one `bulleted_list_item` per insight, and a final `🔗 ...` bulleted item. Batch ≤100 blocks per call. Ask which page to append to (or create a new child page) if not obvious from context.

## Common Mistakes

- **Trusting WebFetch/browser for the transcript.** They only see the title. The transcript comes from `mcp__plaud__get_transcript`, not the web page.
- **Using `search_transcripts` to find the file.** Unreliable — resolve via `get_files` + title/date match instead.
- **Reading a persisted transcript with Read offset/limit.** It's one giant JSON blob; extract the `.transcript` field with python/jq.
- **Bullets that grow into paragraphs.** If a bullet has a clause after a comma explaining itself, cut it. Terse or it's wrong.
- **Summarizing the interviewer's side.** The value is the interviewee's pains, wants, and objections.
