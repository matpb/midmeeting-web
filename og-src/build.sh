#!/usr/bin/env bash
# Renders the four OG cards, crops chrome's short-viewport headless bug away,
# verifies them, hashes the filenames, and prints the final names.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$DIR/../images/og"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

CHROME=/usr/bin/google-chrome
CARDS=(home agents privacy thanks)

render() {
  local html="$1" out="$2"
  "$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --force-device-scale-factor=1 --default-background-color=0d0b10ff \
    --window-size=1200,720 --virtual-time-budget=3000 \
    --screenshot="$out" "file://$html" >/dev/null 2>&1
}

mkdir -p "$OUT"

for name in "${CARDS[@]}"; do
  echo "== $name =="
  render "$DIR/$name.html" "$TMP/$name.raw.png"
  python3 "$DIR/verify.py" crop "$TMP/$name.raw.png" "$TMP/$name.png"

  render "$DIR/${name}_nofont.html" "$TMP/${name}_nofont.raw.png"
  python3 "$DIR/verify.py" crop "$TMP/${name}_nofont.raw.png" "$TMP/${name}_nofont.png"

  python3 "$DIR/verify.py" diff "$TMP/$name.png" "$TMP/${name}_nofont.png"
done

echo "== hashing and installing =="
declare -A FINAL
for name in "${CARDS[@]}"; do
  hash="$(sha256sum "$TMP/$name.png" | cut -c1-8)"
  final="$OUT/$name.$hash.png"
  rm -f "$OUT/$name".*.png
  cp "$TMP/$name.png" "$final"
  python3 "$DIR/verify.py" assertsize "$final"
  size_bytes="$(stat -c%s "$final")"
  echo "$name -> $(basename "$final") (${size_bytes} bytes)"
  FINAL[$name]="$(basename "$final")"
done

echo "== final filenames =="
for name in "${CARDS[@]}"; do
  echo "$name=${FINAL[$name]}"
done
