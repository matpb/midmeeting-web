#!/usr/bin/env python3
# Builds blog/*.html, blog/index.html, og-src blog cards, sitemap.xml from blog-src/.
import glob
import html
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG_SRC = ROOT / "blog-src"
BLOG_OUT = ROOT / "blog"
OG_SRC = ROOT / "og-src"
IMAGES_OG = ROOT / "images" / "og"
SITEMAP = ROOT / "sitemap.xml"
INDEX_HTML = ROOT / "index.html"

SITE = "https://midmeeting.com"
AUTHOR_NAME = "Mathieu-Philippe Bourgeois"
AUTHOR_URL = "https://matpb.com"
WORDS_PER_MINUTE = 220

REQUIRED_KEYS = (
    "slug", "title", "dek", "description", "eyebrow", "date",
    "word_count", "og_headline", "og_subtitle", "related",
)

DASH_RE = re.compile("[\u2013\u2014]")
TABLE_CAPTION_RE = re.compile(
    r'( *)<div class="table-wrap">\s*<table class="cmp-table">\s*<caption>(.*?)</caption>',
    re.DOTALL,
)
MONTHS = (
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
)


def fail(msg):
    raise SystemExit(f"build-blog.py: error: {msg}")


def warn(msg):
    print(f"build-blog.py: warning: {msg}", file=sys.stderr)


def esc(s):
    return html.escape(str(s), quote=True)


def check_no_dash(value, where):
    if isinstance(value, str) and DASH_RE.search(value):
        fail(f"em or en dash found in {where}: {value!r}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            check_no_dash(v, f"{where}[{i}]")
    elif isinstance(value, dict):
        for k, v in value.items():
            check_no_dash(v, f"{where}.{k}")


def read(path):
    return path.read_text(encoding="utf-8")


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def human_date(iso):
    try:
        y, m, d = (int(x) for x in iso.split("-"))
    except Exception:
        fail(f"bad date {iso!r}, expected ISO YYYY-MM-DD")
    return f"{d} {MONTHS[m - 1]} {y}"


def read_minutes(word_count):
    return max(1, math.ceil(word_count / WORDS_PER_MINUTE))


def move_table_captions(body):
    # Caption inside .table-wrap scrolls and clips with the table; hoist it above the wrap.
    def repl(m):
        indent, caption = m.group(1), m.group(2)
        return (
            f'{indent}<p class="table-caption">{caption}</p>\n'
            f'{indent}<div class="table-wrap">\n'
            f'{indent}  <table class="cmp-table">'
        )

    return TABLE_CAPTION_RE.sub(repl, body)


def style_rev():
    text = read(INDEX_HTML)
    m = re.search(r'style\.css\?v=([0-9a-zA-Z]+)', text)
    if not m:
        fail("could not find style.css?v= revision in index.html")
    return m.group(1)


def meta_content(text, prop_or_name, key="property"):
    m = re.search(
        rf'<meta {key}="{re.escape(prop_or_name)}" content="([^"]*)">', text
    )
    return html.unescape(m.group(1)) if m else None


def home_og_image():
    matches = sorted(glob.glob(str(IMAGES_OG / "home.*.png")))
    if not matches:
        fail("no images/og/home.*.png found; run og-src/build.sh first")
    return Path(matches[0]).name


def blog_og_image(slug):
    matches = sorted(glob.glob(str(IMAGES_OG / f"blog-{slug}.*.png")))
    if matches:
        return Path(matches[0]).name
    warn(f"no images/og/blog-{slug}.*.png yet; falling back to the home card")
    return home_og_image()


def alt_from(text):
    t = text.strip().rstrip(".")
    if not t:
        return "MidMeeting"
    return f"MidMeeting card reading: {t[0].lower()}{t[1:]}."


WORDMARK_SVG = (
    '<svg viewBox="0 0 64 64" width="22" height="22" aria-hidden="true">'
    '<path d="M32.0,15.0 A17,17 0 0 1 48.17,26.75" fill="none" stroke="#64c2d0" stroke-width="8" stroke-linecap="butt"/>'
    '<path d="M48.17,26.75 A17,17 0 0 1 41.99,45.75" fill="none" stroke="#e0b25a" stroke-width="8" stroke-linecap="butt"/>'
    '<path d="M41.99,45.75 A17,17 0 0 1 22.01,45.75" fill="none" stroke="#7ea3d1" stroke-width="8" stroke-linecap="butt"/>'
    '<path d="M22.01,45.75 A17,17 0 0 1 15.83,26.75" fill="none" stroke="#7fae7a" stroke-width="8" stroke-linecap="butt"/>'
    '<path d="M15.83,26.75 A17,17 0 0 1 32.0,15.0" fill="none" stroke="#a58bd1" stroke-width="8" stroke-linecap="butt"/>'
    '<line x1="32.0" y1="19.2" x2="32.0" y2="10.8" stroke="#17141a" stroke-width="1.5" stroke-linecap="butt"/>'
    '<line x1="44.17" y1="28.04" x2="52.16" y2="25.45" stroke="#17141a" stroke-width="1.5" stroke-linecap="butt"/>'
    '<line x1="39.52" y1="42.36" x2="44.46" y2="49.15" stroke="#17141a" stroke-width="1.5" stroke-linecap="butt"/>'
    '<line x1="24.48" y1="42.36" x2="19.54" y2="49.15" stroke="#17141a" stroke-width="1.5" stroke-linecap="butt"/>'
    '<line x1="19.83" y1="28.04" x2="11.84" y2="25.45" stroke="#17141a" stroke-width="1.5" stroke-linecap="butt"/>'
    '<circle cx="32.0" cy="32.0" r="9" fill="#d1583f"/></svg>'
)


def build_nav():
    return f"""<header class="nav">
  <div class="wrap nav-row">
    <a class="wordmark" href="/">{WORDMARK_SVG}<span class="accent">Mid</span>Meeting</a>
    <nav class="nav-links">
      <a href="/#how">How it works</a>
      <a href="/getting-started.html">Getting started</a>
      <a href="/#agents">AI advisors</a>
      <a href="/agents">Agent bridge</a>
      <a href="/#privacy">Privacy</a>
      <a href="/#price">Price</a>
      <a href="/blog/" aria-current="page">Blog</a>
      <a class="pill" href="/#download">Download</a>
    </nav>
  </div>
</header>"""


def build_footer():
    return f"""<footer class="foot">
  <div class="wrap foot-row">
    <div class="foot-brand">
      <a class="wordmark" href="/">{WORDMARK_SVG}<span class="accent">Mid</span>Meeting</a>
      <p>Your meetings, written down live, on your own computer.</p>
    </div>
    <div class="foot-links">
      <a href="/privacy.html">Privacy</a>
      <a href="https://github.com/matpb/midmeeting-web">GitHub</a>
      <a href="https://matpb.com">matpb.com</a>
    </div>
  </div>
  <div class="wrap">
    <p class="copyright">&copy; 2026 Mathieu-Philippe Bourgeois</p>
  </div>
</footer>"""


def build_favicon_links():
    return """<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32">
<link rel="icon" href="/favicon-16.png" sizes="16x16">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">"""


def load_post(json_path):
    slug_from_name = json_path.stem
    try:
        data = json.loads(read(json_path))
    except json.JSONDecodeError as e:
        fail(f"{json_path.name}: invalid JSON ({e})")

    for key in REQUIRED_KEYS:
        if key not in data:
            fail(f"{json_path.name}: missing required key {key!r}")

    if data["slug"] != slug_from_name:
        fail(f"{json_path.name}: slug {data['slug']!r} does not match filename")

    if not isinstance(data["related"], list):
        fail(f"{json_path.name}: related must be a list")

    html_path = BLOG_SRC / f"{slug_from_name}.html"
    if not html_path.exists():
        fail(f"missing {html_path.name} for {json_path.name}")
    body = read(html_path)
    body = move_table_captions(body)

    check_no_dash(data, json_path.name)
    check_no_dash(body, html_path.name)

    for ref_id in re.findall(r'<sup class="fnref"><a href="#([^"]+)"', body):
        if f'id="{ref_id}"' not in body:
            fail(f"{html_path.name}: fnref target #{ref_id} has no matching id in the source")

    data.setdefault("order", 0)
    data["_body"] = body
    data["_minutes"] = read_minutes(data["word_count"])
    data["_human_date"] = human_date(data["date"])
    return data


def load_all_posts():
    posts = {}
    for json_path in sorted(BLOG_SRC.glob("*.json")):
        post = load_post(json_path)
        posts[post["slug"]] = post

    for post in posts.values():
        for rel in post["related"]:
            if rel not in posts:
                fail(f"{post['slug']}: related slug {rel!r} does not exist in blog-src/")

    return posts


def build_head(title, description, canonical, og_type, og_image_name,
               og_image_alt, extra_meta=""):
    og_image_url = f"{SITE}/images/og/{og_image_name}"
    return f"""<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="MidMeeting">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{og_image_url}">
<meta property="og:image:secure_url" content="{og_image_url}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(og_image_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{og_image_url}">
<meta name="twitter:image:alt" content="{esc(og_image_alt)}">
{extra_meta}<meta name="theme-color" content="#0d0b10">
{build_favicon_links()}
<link rel="stylesheet" href="../style.css?v={style_rev()}">"""


def extract_first_post_fig_svg(body):
    m = re.search(r'<figure class="post-fig[^"]*">.*?</figure>', body, re.DOTALL)
    if not m:
        return None
    fig = m.group(0)
    svg = re.search(r'<svg\b.*?</svg>', fig, re.DOTALL)
    return svg.group(0) if svg else None


def build_post_card(post):
    return f"""      <a class="post-card" href="{post['slug']}.html">
        <span class="card-meta">{post['_human_date']} &middot; {post['_minutes']} min read</span>
        <h3>{esc(post['title'])}</h3>
        <p>{esc(post['dek'])}</p>
      </a>"""


def build_related(post, posts_by_slug):
    if not post["related"]:
        return ""
    cards = "\n".join(build_post_card(posts_by_slug[slug]) for slug in post["related"])
    return f"""

<section class="related">
  <div class="wrap">
    <div class="related-head">
      <h2>Keep reading</h2>
      <a href="index.html">All posts</a>
    </div>
    <div class="related-grid">
{cards}
    </div>
  </div>
</section>"""


def build_post_page(post, posts_by_slug):
    slug = post["slug"]
    canonical = f"{SITE}/blog/{slug}"
    og_image_name = blog_og_image(slug)
    og_image_alt = alt_from(post["og_subtitle"])

    extra_meta = (
        f'<meta property="article:published_time" content="{post["date"]}">\n'
        f'<meta property="article:author" content="{AUTHOR_NAME}">\n'
    )
    head = build_head(
        f"{post['title']}: MidMeeting", post["description"], canonical,
        "article", og_image_name, og_image_alt, extra_meta,
    )

    jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": post["description"],
        "datePublished": post["date"],
        "dateModified": post["date"],
        "author": {"@type": "Person", "name": AUTHOR_NAME, "url": AUTHOR_URL},
        "publisher": {"@type": "Organization", "name": "MidMeeting", "url": SITE},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "image": f"{SITE}/images/og/{og_image_name}",
    }

    related_html = build_related(post, posts_by_slug)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{head}
<script type="application/ld+json">{json.dumps(jsonld, indent=2)}</script>
</head>
<body>

<a class="skip" href="#main">Skip to content</a>

{build_nav()}

<main id="main">

<article>

<header class="post-head">
  <div class="wrap">
    <div class="post-head-inner">
      <p class="eyebrow">{esc(post['eyebrow'])}</p>
      <h1 class="post-title">{esc(post['title'])}</h1>
      <p class="post-dek">{esc(post['dek'])}</p>
      <p class="post-meta">
        <span class="author">{AUTHOR_NAME}</span>
        <span><time datetime="{post['date']}">{post['_human_date']}</time></span>
        <span>{post['_minutes']} min read</span>
      </p>
    </div>
  </div>
</header>

<div class="wrap post-body">

{post['_body']}
</div>

<footer class="wrap">
  <div class="author-card">
    <div class="author-avatar" aria-hidden="true">MPB</div>
    <div>
      <p class="author-name">{AUTHOR_NAME}</p>
      <p class="author-bio">Builds MidMeeting. Software engineer in Sherbrooke, Quebec. <a href="https://matpb.com">matpb.com</a></p>
    </div>
  </div>

  <div class="post-cta">
    <h2>Record the next one yourself.</h2>
    <p>Three free meetings of any length, then $39 once. The recording never leaves your computer.</p>
    <a class="btn btn-primary" href="/#download">Download free</a>
    <a class="btn btn-text" href="/#how">See how it works</a>
  </div>
</footer>

</article>{related_html}

</main>

{build_footer()}

</body>
</html>
"""


def build_featured(post):
    svg = extract_first_post_fig_svg(post["_body"])
    fig_html = ""
    if svg:
        fig_html = f"""    <div class="featured-fig" aria-hidden="true">
      {svg}
    </div>
"""
    return f"""  <a class="featured" href="{post['slug']}.html">
{fig_html}    <div class="featured-body">
      <p class="eyebrow">Latest</p>
      <h2>{esc(post['title'])}</h2>
      <p>{esc(post['dek'])}</p>
      <span class="card-meta">{post['_human_date']} &middot; {post['_minutes']} min read &middot; <b>Read the article</b></span>
    </div>
  </a>"""


def build_list_item(post):
    return f"""    <li>
      <a href="{post['slug']}.html">
        <span class="card-meta"><time datetime="{post['date']}">{post['_human_date']}</time></span>
        <span>
          <h2>{esc(post['title'])}</h2>
          <p>{esc(post['dek'])}</p>
        </span>
        <span class="read">{post['_minutes']} min read</span>
      </a>
    </li>"""


def build_index_page(posts_sorted):
    canonical = f"{SITE}/blog/"
    description = (
        "Notes on meeting recording, live transcription and using AI during "
        "a call, written by the person building MidMeeting."
    )
    og_image_name = home_og_image()
    index_text = read(INDEX_HTML)
    og_image_alt = meta_content(index_text, "og:image:alt") or alt_from(description)

    head = build_head(
        "Blog: MidMeeting", description, canonical, "website",
        og_image_name, og_image_alt,
    )

    jsonld = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "MidMeeting blog",
        "url": canonical,
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": p["title"],
                "url": f"{SITE}/blog/{p['slug']}",
                "datePublished": p["date"],
            }
            for p in posts_sorted
        ],
    }

    featured_html = ""
    list_items = ""
    if posts_sorted:
        featured_html = build_featured(posts_sorted[0])
        list_items = "\n".join(build_list_item(p) for p in posts_sorted[1:])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{head}
<script type="application/ld+json">{json.dumps(jsonld, indent=2)}</script>
</head>
<body>

<a class="skip" href="#main">Skip to content</a>

{build_nav()}

<main id="main">

<section class="blog-head">
  <div class="wrap">
    <p class="eyebrow">Blog</p>
    <h1>Notes from the margin.</h1>
    <p class="lead">{esc(description)}</p>
  </div>
</section>

<section class="wrap">

{featured_html}

  <ul class="post-list">
{list_items}
  </ul>

</section>

<section class="sec closing">
  <div class="wrap wrap-narrow">
    <h2>Record the next one yourself.</h2>
    <a class="btn btn-primary" href="/#download">Download free</a>
    <a class="btn btn-text" href="/#how">See how it works</a>
  </div>
</section>

</main>

{build_footer()}

</body>
</html>
"""


def build_og_cards(posts):
    for slug, post in posts.items():
        for template_name, out_suffix in (
            ("_template.html", ""), ("_template_nofont.html", "_nofont"),
        ):
            template = read(OG_SRC / template_name)
            rendered = template.replace(
                "__HEADLINE__", esc(post["og_headline"])
            ).replace(
                "__SUBTITLE__", esc(post["og_subtitle"])
            )
            write(OG_SRC / f"blog-{slug}{out_suffix}.html", rendered)


def update_sitemap(posts):
    text = read(SITEMAP)
    close_tag = "</urlset>"
    if close_tag not in text:
        fail("sitemap.xml missing </urlset>")

    block_re = re.compile(r"  <url>.*?</url>\n", re.DOTALL)
    blocks = block_re.findall(text)

    other_blocks = []
    for block in blocks:
        m = re.search(r"<loc>(.*?)</loc>", block)
        loc = m.group(1) if m else ""
        if loc.startswith(f"{SITE}/blog"):
            continue
        other_blocks.append(block)

    desired = [(f"{SITE}/blog/", "0.7")]
    for slug in sorted(posts):
        desired.append((f"{SITE}/blog/{slug}", "0.6"))

    blog_blocks = [
        f"  <url>\n    <loc>{url}</loc>\n    <changefreq>monthly</changefreq>\n"
        f"    <priority>{priority}</priority>\n  </url>\n"
        for url, priority in desired
    ]

    first_url_pos = text.find("  <url>")
    close_pos = text.find(close_tag)
    header = text[:first_url_pos] if first_url_pos != -1 else text[:close_pos]
    footer = text[close_pos:]

    new_text = header + "".join(other_blocks) + "".join(blog_blocks) + footer
    if new_text != text:
        write(SITEMAP, new_text)


def main():
    if not BLOG_SRC.exists():
        fail(f"{BLOG_SRC} does not exist")

    posts = load_all_posts()
    if not posts:
        warn("no posts found in blog-src/, nothing to build")

    for slug, post in posts.items():
        page = build_post_page(post, posts)
        write(BLOG_OUT / f"{slug}.html", page)

    posts_sorted = sorted(
        posts.values(), key=lambda p: (-date.fromisoformat(p["date"]).toordinal(), p["order"])
    )
    write(BLOG_OUT / "index.html", build_index_page(posts_sorted))

    build_og_cards(posts)
    update_sitemap(posts)

    print(f"built {len(posts)} post(s), blog/index.html, og-src cards, sitemap.xml")


if __name__ == "__main__":
    main()
