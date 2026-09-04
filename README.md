# midmeeting-web

The public website for [MidMeeting](https://midmeeting.com), a local-first desktop meeting
recorder with a live transcript and an AI copilot that weighs in.

**This repository contains no product source code.** MidMeeting itself is private. What is
here is the marketing site. That split mirrors [matpb/wspr-app](https://github.com/matpb/wspr-app)
and [matpb/whotalked-web](https://github.com/matpb/whotalked-web).

## Layout

```
index.html      the homepage: how it works, agents, ask, bring your own brain, privacy, price, FAQ
privacy.html    what the app stores, what it sends and only to the provider you chose
style.css       every style on the site, one file, no build step
404.html        soft-404 catch, required by Cloudflare Pages
robots.txt sitemap.xml favicon.* apple-touch-icon.png site.webmanifest
fonts/          self-hosted Fraunces, Source Serif 4, JetBrains Mono, woff2
images/         icon-512.png
```

There is no `package.json`, no bundler and no framework. Every page is a static file served
from the repository root, and the site makes **zero external requests**: no CDN, no web fonts
loaded live, no analytics, no trackers. That is not an aesthetic choice; a site that sells a
never-leaves-your-machine product has no business phoning home.

## Deploying

See [DEPLOY.md](DEPLOY.md).
