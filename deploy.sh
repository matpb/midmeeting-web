#!/usr/bin/env bash
# Deploy the public site to Cloudflare Pages.
#
# Deploys from a staging copy rather than the repo root: .assetsignore does not
# exclude anything on Pages, so README.md and DEPLOY.md would otherwise be served
# from midmeeting.com as text/markdown.
set -euo pipefail

: "${CLOUDFLARE_API_TOKEN:?set CLOUDFLARE_API_TOKEN (needs Account > Cloudflare Pages: Edit)}"
export CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-0888d7ae1c3473b4988db7211f7dbc9d}"

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

rsync -a \
  --exclude='.git' --exclude='.github' --exclude='.wrangler' \
  --exclude='README.md' --exclude='DEPLOY.md' --exclude='deploy.sh' \
  --exclude='.gitignore' --exclude='.assetsignore' \
  --exclude='shots' --exclude='node_modules' \
  "$repo/" "$stage/"

test -f "$stage/404.html" || { echo "404.html missing: Pages would soft-404 every unknown path"; exit 1; }

cd "$stage"
npx --yes wrangler@latest pages deploy . --project-name=midmeeting-web --branch=main --commit-dirty=true
