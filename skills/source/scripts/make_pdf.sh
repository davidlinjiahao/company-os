#!/usr/bin/env bash
# make_pdf.sh — render a candidate-list markdown into a clickable PDF.
#
# Usage:
#   make_pdf.sh [<markdown_path>] [<output_pdf_path>]
#
#   $1  markdown source. Default: newest ~/Desktop/*_Candidates.md
#   $2  output PDF path.  Default: same dir/name as the markdown, .pdf extension
#
# Pipeline: pandoc (gfm -> html5) + weasyprint, styled by style.css that sits
# next to this script. After rendering it runs a pypdf check that proves the
# links are REAL clickable /Link URI annotations (not just blue text), prints
# the page count, a few sample URLs, and linkedin/github link counts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSS="${SCRIPT_DIR}/style.css"

# ---- resolve input markdown ------------------------------------------------
MD="${1:-}"
MD="${MD/#\~/$HOME}"   # expand a leading ~ even if it arrived inside quotes
if [[ -z "${MD}" ]]; then
  # newest *_Candidates.md on the Desktop
  MD="$(ls -t "${HOME}"/Desktop/*_Candidates.md 2>/dev/null | head -n1 || true)"
  if [[ -z "${MD}" ]]; then
    echo "FAIL: no markdown argument given and no ~/Desktop/*_Candidates.md found." >&2
    exit 1
  fi
  echo "No input given; using newest Desktop candidate file:"
  echo "  ${MD}"
fi

if [[ ! -f "${MD}" ]]; then
  echo "FAIL: markdown file not found: ${MD}" >&2
  exit 1
fi
if [[ ! -f "${CSS}" ]]; then
  echo "FAIL: style.css not found next to script: ${CSS}" >&2
  exit 1
fi

# ---- resolve output pdf ----------------------------------------------------
OUT="${2:-}"
OUT="${OUT/#\~/$HOME}"   # expand a leading ~ even if it arrived inside quotes
if [[ -z "${OUT}" ]]; then
  OUT="${MD%.*}.pdf"
fi

# ---- check deps ------------------------------------------------------------
for bin in pandoc weasyprint python3; do
  if ! command -v "${bin}" >/dev/null 2>&1; then
    echo "FAIL: required tool not on PATH: ${bin}" >&2
    echo "  install with: brew install ${bin}" >&2
    exit 1
  fi
done

# ---- render ----------------------------------------------------------------
echo "Rendering: ${MD}"
echo "      ->  ${OUT}"
pandoc "${MD}" \
  -f gfm \
  -t html5 \
  --standalone \
  --metadata title="$(basename "${MD%.*}")" \
  --css "${CSS}" \
  --pdf-engine=weasyprint \
  -o "${OUT}"

if [[ ! -f "${OUT}" ]]; then
  echo "FAIL: pandoc/weasyprint did not produce ${OUT}" >&2
  exit 1
fi

# ---- verify clickable link annotations with pypdf --------------------------
echo
echo "Verifying clickable link annotations (pypdf)..."
set +e   # capture the verifier's exit code without set -e aborting first
PDF_PATH="${OUT}" python3 - <<'PY'
import os, sys
try:
    from pypdf import PdfReader
except ImportError:
    print("FAIL: pypdf not installed (pip install pypdf).", file=sys.stderr)
    sys.exit(1)

path = os.environ["PDF_PATH"]
reader = PdfReader(path)
pages = len(reader.pages)

uris = []
for page in reader.pages:
    annots = page.get("/Annots")
    if not annots:
        continue
    for ref in annots:
        try:
            obj = ref.get_object()
        except Exception:
            continue
        if obj.get("/Subtype") != "/Link":
            continue
        action = obj.get("/A")
        if not action:
            continue
        uri = action.get_object().get("/URI") if hasattr(action, "get_object") else action.get("/URI")
        if uri:
            uris.append(str(uri))

total = len(uris)
linkedin = sum(1 for u in uris if "linkedin.com" in u.lower())
github = sum(1 for u in uris if "github.com" in u.lower())

print(f"  pages:            {pages}")
print(f"  clickable links:  {total}")
print(f"  linkedin links:   {linkedin}")
print(f"  github links:     {github}")

if uris:
    print("  sample URLs:")
    for u in uris[:6]:
        print(f"    - {u}")

if total == 0:
    print("WARN: zero clickable link annotations found. Links may be blue text only.", file=sys.stderr)
    sys.exit(2)
PY
RC=$?
set -e

echo
if [[ "${RC}" -eq 0 ]]; then
  echo "SUCCESS: wrote ${OUT} with verified clickable links."
else
  echo "DONE WITH WARNINGS: wrote ${OUT} but link verification flagged an issue (rc=${RC})."
fi
exit "${RC}"
