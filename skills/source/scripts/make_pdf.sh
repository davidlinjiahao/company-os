#!/usr/bin/env bash
# make_pdf.sh — render a candidate list markdown into a PDF with real clickable links.
#
# Usage:
#   make_pdf.sh <markdown> [<output.pdf>]
#   make_pdf.sh --help
#
# Optional step. Needs pandoc + weasyprint (and pypdf for the link check).
# If they are absent — a plain sandbox usually has none of them — this exits 3
# with a clear message and the markdown remains the deliverable. Never treat a
# missing PDF as a failed sourcing run.
#
# After rendering it verifies the links are real /Link URI annotations rather
# than blue text, and prints the count.

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSS="$HERE/style.css"

case "${1:-}" in
  --help|-h|"") sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
esac

MD="${1/#\~/$HOME}"
[[ -f "$MD" ]] || { echo "ERROR: no such markdown file: $MD" >&2; exit 2; }
OUT="${2:-${MD%.*}.pdf}"; OUT="${OUT/#\~/$HOME}"

missing=()
for bin in pandoc weasyprint python3; do
  command -v "$bin" >/dev/null 2>&1 || missing+=("$bin")
done
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "PDF step skipped — not installed: ${missing[*]}" >&2
  echo "The markdown at $MD is the deliverable. Install with: brew install ${missing[*]}" >&2
  exit 3
fi

pandoc "$MD" -f gfm -t html5 --standalone \
  --metadata title="$(basename "${MD%.*}")" \
  --css "$CSS" --pdf-engine=weasyprint -o "$OUT" || exit 4
[[ -f "$OUT" ]] || { echo "ERROR: renderer produced no file" >&2; exit 4; }

PDF_PATH="$OUT" python3 - <<'PY'
import os, sys
try:
    from pypdf import PdfReader
except ImportError:
    print("PDF written, link check skipped (pypdf not installed).", file=sys.stderr)
    sys.exit(0)
reader = PdfReader(os.environ["PDF_PATH"])
uris = []
for page in reader.pages:
    for ref in page.get("/Annots") or []:
        try:
            obj = ref.get_object()
        except Exception:
            continue
        if obj.get("/Subtype") != "/Link":
            continue
        action = obj.get("/A")
        if action is None:
            continue
        uri = action.get_object().get("/URI") if hasattr(action, "get_object") else action.get("/URI")
        if uri:
            uris.append(str(uri))
print(f"pages: {len(reader.pages)}  clickable links: {len(uris)}")
for u in uris[:6]:
    print(f"  - {u}")
if not uris:
    print("WARN: zero clickable link annotations — the links are blue text only.", file=sys.stderr)
    sys.exit(5)
PY
rc=$?
echo "wrote $OUT"
exit $rc
