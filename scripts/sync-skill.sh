#!/usr/bin/env bash
# Regenerate the skill-pre block in agents.html from skills/midmeeting/SKILL.md.
#
# skills/midmeeting/SKILL.md is the single source of truth. agents.html embeds
# an HTML-escaped copy between the <!-- skill:begin --> / <!-- skill:end -->
# markers so it never drifts. Idempotent: running it twice makes no further
# change. --check exits 1 without writing when agents.html is stale.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill="$repo/skills/midmeeting/SKILL.md"
html="$repo/agents.html"

mode="write"
for arg in "$@"; do
  case "$arg" in
    --check) mode="check" ;;
    *) echo "usage: $(basename "$0") [--check]" >&2; exit 2 ;;
  esac
done

test -f "$skill" || { echo "missing $skill" >&2; exit 1; }
test -f "$html" || { echo "missing $html" >&2; exit 1; }

python3 - "$skill" "$html" "$mode" <<'PY'
import sys

skill_path, html_path, mode = sys.argv[1], sys.argv[2], sys.argv[3]
begin, end = "<!-- skill:begin -->", "<!-- skill:end -->"

with open(skill_path, encoding="utf-8") as f:
    skill_text = f.read()

escaped = skill_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
rendered = '<pre class="skill-pre">' + escaped + "</pre>"

with open(html_path, encoding="utf-8") as f:
    html = f.read()

if begin not in html or end not in html:
    sys.stderr.write(f"markers {begin} / {end} not found in {html_path}\n")
    sys.exit(1)

start = html.index(begin) + len(begin)
stop = html.index(end, start)
new_html = html[:start] + "\n    " + rendered + "\n    " + html[stop:]

if mode == "check":
    sys.exit(0 if new_html == html else 1)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(new_html)
PY
