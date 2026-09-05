#!/bin/sh
# Installs midmeeting-bridge. curl -fsSL https://midmeeting.com/bridge.sh | sh
set -eu

VERSION="v1.0.2"
BASE_URL="https://github.com/matpb/midmeeting-web/releases/download/${VERSION}"
BIN_DIR="${MIDMEETING_BIN_DIR:-$HOME/.local/bin}"

os="$(uname -s)"
arch="$(uname -m)"

case "$os $arch" in
  "Linux x86_64")
    asset="midmeeting-bridge-linux-x86_64"
    ;;
  "Darwin arm64")
    asset="midmeeting-bridge-macos-arm64"
    ;;
  *)
    echo "midmeeting-bridge has no build for $os $arch." >&2
    echo "Supported: Linux x86_64 and macOS Apple Silicon (arm64)." >&2
    echo "Windows: run in PowerShell: irm https://midmeeting.com/bridge.ps1 | iex" >&2
    echo "Intel Macs are not supported yet." >&2
    exit 1
    ;;
esac

mkdir -p "$BIN_DIR"
dest="$BIN_DIR/midmeeting-bridge"
url="$BASE_URL/$asset"

echo "Downloading $asset..."
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$url" -o "$dest"
elif command -v wget >/dev/null 2>&1; then
  wget -q "$url" -O "$dest"
else
  echo "Need curl or wget to download midmeeting-bridge." >&2
  exit 1
fi

chmod +x "$dest"

if "$dest" --help >/dev/null 2>&1 || [ "$?" -eq 2 ]; then
  echo "Installed to $dest"
else
  echo "Downloaded binary at $dest did not run. Check the download and try again." >&2
  exit 1
fi

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Add $BIN_DIR to your PATH: export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac
