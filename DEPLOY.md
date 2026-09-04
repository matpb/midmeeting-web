# Deploy runbook: midmeeting-web

Static site, no build step, served from the repository root on **Cloudflare Pages**.

Note that this does NOT follow the `wspr-app` pattern. getwspr.com is served by **GitHub
Pages**, with Cloudflare only doing DNS in front of it. That is why `wspr-app` carries a
`CNAME` file. This project is on Cloudflare Pages proper, which is what makes `_headers`
available at all.

## Current state

| | |
|---|---|
| Pages project | `midmeeting-web` (account `Bourgeois.mat@gmail.com's Account`) |
| Production branch | `main` |
| Build command | none |
| Output directory | `/` |
| Domains | `midmeeting.com`, `www.midmeeting.com`, `midmeeting-web.pages.dev` |
| DNS | both hostnames proxied `CNAME -> midmeeting-web.pages.dev` |

## Deploying

Every other Pages project on this account deploys `ad_hoc` from the CLI rather than through the
Git integration, and so does this one:

```sh
export CLOUDFLARE_API_TOKEN=...        # needs Account > Cloudflare Pages: Edit
export CLOUDFLARE_ACCOUNT_ID=0888d7ae1c3473b4988db7211f7dbc9d
./deploy.sh
```

**Deploy through `deploy.sh`, not from the repo root.** `.assetsignore` does not exclude
anything on Pages, verified on whotalked-web, `README.md` was served as `text/markdown` from
the live domain after a root deploy. `deploy.sh` rsyncs the public files into a staging
directory and deploys that, so the exclusion holds by construction.

`404.html` is required. Without it Pages answers every unknown path with `200` and the
homepage body, which is a soft 404 on every typo and bad backlink.

Pushing to GitHub does **not** deploy. The repo and the live site are updated separately, so
push and deploy together or they drift.

## Cache-Control

`_headers` cannot set `Cache-Control` on Pages, verified on whotalked-web: an extension glob
and an exact path were both tried and neither changed the served value, which stays `public,
max-age=14400`. Only the security headers from `_headers` take effect.

## The updater manifest

Not published yet. MidMeeting has no `update.json` and no release binaries to point one at, so
there is nothing to pin a Cache Rule for. Add this section back, following the whotalked-web
pattern, once a release exists.

## Checks before any deploy

```sh
# no external requests: only the canonical/OG URLs, GitHub and matpb.com should match
grep -ohE 'https?://[^"'"'"' ]+' *.html | sort -u

# every internal link resolves
grep -ohE 'href="[^"]+"' *.html | sed 's/href="//;s/"//' | sort -u
```
