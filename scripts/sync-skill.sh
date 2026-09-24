#!/usr/bin/env bash
# Regenerates the skill-pre blocks in the site from their SKILL.md sources.
# Idempotent; --check exits 1 without writing if any block is stale.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pairs=(
  "$repo/skills/midmeeting/SKILL.md|$repo/agents.html|<!-- skill:begin -->|<!-- skill:end -->"
  "$repo/skills/midmeeting-advisors/SKILL.md|$repo/agents.html|<!-- advisors-skill:begin -->|<!-- advisors-skill:end -->"
)

mode="write"
for arg in "$@"; do
  case "$arg" in
    --check) mode="check" ;;
    *) echo "usage: $(basename "$0") [--check]" >&2; exit 2 ;;
  esac
done

status=0
for pair in "${pairs[@]}"; do
  IFS='|' read -r skill html begin end <<< "$pair"
  test -f "$skill" || { echo "missing $skill" >&2; exit 1; }
  test -f "$html" || { echo "missing $html" >&2; exit 1; }

  set +e
  python3 - "$skill" "$html" "$mode" "$begin" "$end" <<'PY'
import sys

skill_path, html_path, mode, begin, end = sys.argv[1:6]

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
  rc=$?
  set -e

  if [ "$rc" -ne 0 ]; then
    if [ "$mode" = "check" ]; then
      status=1
    else
      exit "$rc"
    fi
  fi
done

exit "$status"
