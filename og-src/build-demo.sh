#!/usr/bin/env bash
# Renders the 22s hero demo (mp4 + gif + poster) from demo.html at 24fps,
# crops chrome's short-viewport headless bug, encodes, hashes, verifies.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$DIR/../images"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

CHROME=/usr/bin/google-chrome
FFMPEG=/usr/bin/ffmpeg
FFPROBE=/usr/bin/ffprobe

FPS=24
FRAMES=528
DEMO_URL="file://$DIR/demo.html"

render_frame() {
  local i="$1"
  local t=$(( i * 1000 / FPS ))
  local raw="$TMP/raw_$(printf '%04d' "$i").png"
  local final="$TMP/frame_$(printf '%04d' "$i").png"
  "$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --force-device-scale-factor=1 --default-background-color=0d0b10ff \
    --window-size=1200,840 --virtual-time-budget=1500 \
    --screenshot="$raw" "${DEMO_URL}?t=${t}" >/dev/null 2>&1
  python3 - "$raw" "$final" <<'PYEOF'
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
im.crop((0, 0, 1200, 750)).save(sys.argv[2], format="PNG")
PYEOF
}
export -f render_frame
export CHROME DEMO_URL TMP FPS

echo "== rendering $FRAMES frames at ${FPS}fps =="
seq 0 $((FRAMES - 1)) | xargs -P 8 -I{} bash -c 'render_frame "$@"' _ {}

missing=0
for i in $(seq 0 $((FRAMES - 1))); do
  f="$TMP/frame_$(printf '%04d' "$i").png"
  [ -s "$f" ] || { echo "MISSING $f"; missing=1; }
done
[ "$missing" -eq 0 ] || { echo "frame render failed"; exit 1; }

echo "== poster (t=12600) =="
POSTER_RAW="$TMP/poster_raw.png"
"$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --force-device-scale-factor=1 --default-background-color=0d0b10ff \
  --window-size=1200,840 --virtual-time-budget=1500 \
  --screenshot="$POSTER_RAW" "${DEMO_URL}?t=12600" >/dev/null 2>&1
python3 - "$POSTER_RAW" "$TMP/poster.png" <<'PYEOF'
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
im.crop((0, 37, 1200, 713)).save(sys.argv[2], format="PNG")
PYEOF

echo "== mp4 =="
"$FFMPEG" -y -framerate "$FPS" -i "$TMP/frame_%04d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset slow -movflags +faststart \
  -vf "crop=1200:676:0:37" "$TMP/demo.mp4" -loglevel error

echo "== hero mp4 (the app window only, the site supplies the frame) =="
"$FFMPEG" -y -framerate "$FPS" -i "$TMP/frame_%04d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset slow -movflags +faststart \
  -vf "crop=1040:416:80:167" "$TMP/demo-hero.mp4" -loglevel error
python3 - "$POSTER_RAW" "$TMP/poster-hero.png" <<'PYEOF'
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
im.crop((80, 167, 1120, 583)).save(sys.argv[2], format="PNG")
PYEOF

echo "== gif (two-pass palette) =="
"$FFMPEG" -y -framerate "$FPS" -i "$TMP/frame_%04d.png" \
  -vf "fps=15,crop=1200:676:0:37,scale=960:-1:flags=lanczos,palettegen=max_colors=128:stats_mode=diff" \
  "$TMP/palette.png" -loglevel error
"$FFMPEG" -y -framerate "$FPS" -i "$TMP/frame_%04d.png" -i "$TMP/palette.png" \
  -lavfi "fps=15,crop=1200:676:0:37,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" \
  "$TMP/demo.gif" -loglevel error

gif_size=$(stat -c%s "$TMP/demo.gif")
if [ "$gif_size" -gt $((8 * 1024 * 1024)) ]; then
  echo "gif over 8MB ($gif_size bytes), retrying at 8fps"
  "$FFMPEG" -y -framerate "$FPS" -i "$TMP/frame_%04d.png" \
    -vf "fps=8,crop=1200:676:0:37,scale=960:-1:flags=lanczos,palettegen=max_colors=128:stats_mode=diff" \
    "$TMP/palette.png" -loglevel error
  "$FFMPEG" -y -framerate "$FPS" -i "$TMP/frame_%04d.png" -i "$TMP/palette.png" \
    -lavfi "fps=8,crop=1200:676:0:37,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" \
    "$TMP/demo.gif" -loglevel error
  gif_size=$(stat -c%s "$TMP/demo.gif")
fi
if [ "$gif_size" -gt $((8 * 1024 * 1024)) ]; then
  echo "gif still over 8MB ($gif_size bytes), retrying at 8fps / 840px wide"
  "$FFMPEG" -y -framerate "$FPS" -i "$TMP/frame_%04d.png" \
    -vf "fps=8,crop=1200:676:0:37,scale=840:-1:flags=lanczos,palettegen=max_colors=128:stats_mode=diff" \
    "$TMP/palette.png" -loglevel error
  "$FFMPEG" -y -framerate "$FPS" -i "$TMP/frame_%04d.png" -i "$TMP/palette.png" \
    -lavfi "fps=8,crop=1200:676:0:37,scale=840:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" \
    "$TMP/demo.gif" -loglevel error
  gif_size=$(stat -c%s "$TMP/demo.gif")
  echo "final gif at 8fps/840px: $gif_size bytes"
fi

echo "== ffprobe mp4 =="
"$FFPROBE" -v error -select_streams v:0 \
  -show_entries stream=width,height,pix_fmt,duration -of default=noprint_wrappers=1 \
  "$TMP/demo.mp4"

echo "== hashing and installing =="
mkdir -p "$OUT"

hash_mp4="$(sha256sum "$TMP/demo.mp4" | cut -c1-8)"
final_mp4="$OUT/demo.$hash_mp4.mp4"
rm -f "$OUT"/demo.*.mp4
cp "$TMP/demo.mp4" "$final_mp4"

hash_gif="$(sha256sum "$TMP/demo.gif" | cut -c1-8)"
final_gif="$OUT/demo.$hash_gif.gif"
rm -f "$OUT"/demo.*.gif
cp "$TMP/demo.gif" "$final_gif"

hash_poster="$(sha256sum "$TMP/poster.png" | cut -c1-8)"
final_poster="$OUT/demo-poster.$hash_poster.png"
rm -f "$OUT"/demo-poster.*.png
cp "$TMP/poster.png" "$final_poster"

hash_hero="$(sha256sum "$TMP/demo-hero.mp4" | cut -c1-8)"
final_hero="$OUT/demo-hero.$hash_hero.mp4"
rm -f "$OUT"/demo-hero.*.mp4
cp "$TMP/demo-hero.mp4" "$final_hero"

hash_hposter="$(sha256sum "$TMP/poster-hero.png" | cut -c1-8)"
final_hposter="$OUT/demo-hero-poster.$hash_hposter.png"
rm -f "$OUT"/demo-hero-poster.*.png
cp "$TMP/poster-hero.png" "$final_hposter"

echo "== final filenames =="
echo "hero=$(basename "$final_hero") ($(stat -c%s "$final_hero") bytes)"
echo "hero_poster=$(basename "$final_hposter") ($(stat -c%s "$final_hposter") bytes)"
echo "mp4=$(basename "$final_mp4") ($(stat -c%s "$final_mp4") bytes)"
echo "gif=$(basename "$final_gif") ($(stat -c%s "$final_gif") bytes)"
echo "poster=$(basename "$final_poster") ($(stat -c%s "$final_poster") bytes)"
