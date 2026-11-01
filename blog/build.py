#!/usr/bin/env python3
"""Builds blog/<slug>/index.html, blog/index.html and sitemap.xml from blog/_src/*.html.

Each source file starts with a JSON header line:
{"slug": "...", "title": "...", "h1": "...", "description": "...", "date": "YYYY-MM-DD", "minutes": 6}
followed by the article body HTML.
Run: python3 blog/build.py
"""
import html, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://getchessai.com"
APP = "https://apps.apple.com/app/id6790178402"

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}/assets/shot-analysis.png">
<link rel="icon" href="/assets/icon.png">
<link rel="apple-touch-icon" href="/assets/icon.png">
<link rel="stylesheet" href="/blog/blog.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-8JG1S0FTK3"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-8JG1S0FTK3', {{ page_title: {ga_title} }});
  document.addEventListener('click', function (e) {{
    var a = e.target.closest('a[href*="apps.apple.com"]');
    if (a) gtag('event', 'blog_appstore_clicked', {{ post: {ga_title} }});
  }});
</script>
{jsonld}
</head>
<body>
<nav>
  <div class="wrap">
    <a class="brand" href="/"><img src="/assets/icon.png" alt="">Chess AI</a>
    <div class="links">
      <a href="/blog/">Blog</a>
      <a class="cta" href="{app}">Get the app</a>
    </div>
  </div>
</nav>
"""

FOOT = """<footer>
  <div class="wrap">
    <span>© 2026 Hensu LLC</span>
    <a href="/blog/">Blog</a>
    <a href="/creators/">Creators</a>
    <a href="/support.html">Support</a>
    <a href="/privacy.html">Privacy</a>
    <a href="/terms.html">Terms</a>
  </div>
</footer>
</body>
</html>
"""

CTA = """<aside class="appcta">
  <img src="/assets/icon.png" alt="">
  <div>
    <strong>Chess AI for iPhone</strong>
    <p>Play an opponent that adapts to your level, then see every mistake explained. Unlimited free game review; AI coaching with a 7-day free trial.</p>
  </div>
  <a class="cta" href="{app}">Download free</a>
</aside>
"""


def page(meta, body, url, og_type, jsonld=""):
    return HEAD.format(
        title=html.escape(meta["title"]), description=html.escape(meta["description"]),
        url=url, og_type=og_type, site=SITE, app=APP,
        ga_title=json.dumps(meta.get("ga", meta["title"])), jsonld=jsonld,
    ) + body + FOOT


def main():
    posts = []
    for src in sorted((ROOT / "blog/_src").glob("*.html")):
        header, body = src.read_text().split("\n", 1)
        meta = json.loads(header)
        posts.append((meta, body))
    posts.sort(key=lambda p: p[0]["date"], reverse=True)

    for meta, body in posts:
        url = f"{SITE}/blog/{meta['slug']}/"
        ld = {
            "@context": "https://schema.org", "@type": "Article",
            "headline": meta["h1"], "description": meta["description"],
            "datePublished": meta["date"], "dateModified": meta["date"],
            "author": {"@type": "Organization", "name": "Chess AI"},
            "publisher": {"@type": "Organization", "name": "Hensu LLC",
                          "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/icon.png"}},
            "mainEntityOfPage": url, "image": f"{SITE}/assets/shot-analysis.png",
        }
        jsonld = f'<script type="application/ld+json">{json.dumps(ld)}</script>'
        article = (
            f'<main class="wrap post">\n<p class="crumbs"><a href="/blog/">Blog</a></p>\n'
            f'<h1>{meta["h1"]}</h1>\n<p class="meta">{meta["minutes"]} min read</p>\n'
            + body.replace("<!--cta-->", CTA.format(app=APP))
            + "\n" + CTA.format(app=APP) + "</main>\n"
        )
        out = ROOT / "blog" / meta["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(meta, article, url, "article", jsonld))

    cards = "\n".join(
        f'<a class="card" href="/blog/{m["slug"]}/"><h2>{m["h1"]}</h2><p>{html.escape(m["description"])}</p></a>'
        for m, _ in posts
    )
    index_meta = {"title": "Chess improvement blog — Chess AI",
                  "description": "Practical guides to getting better at chess: ratings, blunders, tilt, training plans and free game review.",
                  "ga": "Blog"}
    index = (f'<main class="wrap post"><h1>Get better at chess</h1>\n'
             f'<p class="lede">Straight answers for players who want to climb, from the team behind Chess AI.</p>\n'
             f'<div class="cards">{cards}</div></main>\n')
    (ROOT / "blog/index.html").write_text(page(index_meta, index, f"{SITE}/blog/", "website"))

    # /c/ (creator code landing pages) is deliberately not listed — see robots.txt.
    urls = [f"{SITE}/", f"{SITE}/blog/", f"{SITE}/creators/", f"{SITE}/daily/"] + [f"{SITE}/blog/{m['slug']}/" for m, _ in posts]
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (ROOT / "sitemap.xml").write_text(sitemap)
    print(f"built {len(posts)} posts")


if __name__ == "__main__":
    main()
