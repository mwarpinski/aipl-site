#!/usr/bin/env python3
"""Stamps the shared header and footer (src/_header.html, src/_footer.html) around each page body in src/*.html and
writes the finished pages to the repository root, which is what gets hosted: no build step on the host.

  python3 build.py          # writes ./index.html, ./install.html, ...
  python3 build.py --check  # fails if a written page is out of date (for CI)

A page body starts with front matter lines `title:`, `description:`, `nav:` (which menu item is current), then a blank line.
"""
import html, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"

KEYWORDS = "module import fn req ens let while set! call if else and or not match struct union test assert return"
TYPES = "i32 i64 f32 f64 bool str void"
TOKEN = re.compile(
    r"(?P<c>;;[^\n]*)|(?P<s>\"(?:[^\"\\]|\\.)*\")|(?P<k>(?<=\()(?:%s)(?![\w.!?-]))|(?P<t>(?<=[:\s>\[])(?:%s)(?![\w.]))|(?P<n>(?<![\w.])\d+(?:\.\d+)?(?![\w.]))|(?P<d>[()\[\]])"
    % ("|".join(re.escape(w) for w in KEYWORDS.split()), "|".join(TYPES.split())))

def highlight(source):
    """AIPL source as HTML with the stylesheet's token classes (.c comment, .s string, .k keyword, .t type, .n number)."""
    out, at = [], 0
    for m in TOKEN.finditer(source):
        out.append(html.escape(source[at:m.start()], quote=False))
        out.append(f'<span class="{m.lastgroup}">{html.escape(m.group(), quote=False)}</span>')
        at = m.end()
    out.append(html.escape(source[at:], quote=False))
    return "".join(out)

def highlighted(body):
    """`<pre data-lang="aipl"><code>SOURCE</code></pre>` with SOURCE written as plain text, highlighted."""
    return re.sub(r'<pre data-lang="aipl"><code>(.*?)</code></pre>',
                  lambda m: '<pre><code>' + highlight(html.unescape(m.group(1))) + '</code></pre>', body, flags=re.S)

def render(path):
    head, body = path.read_text().split("\n\n", 1)
    meta = dict(line.split(": ", 1) for line in head.splitlines())
    header = (SRC / "_header.html").read_text()
    header = re.sub(r"\{\{cur:(\w+)\}\}", lambda m: ' aria-current="page"' if m.group(1) == meta.get("nav") else "", header)
    footer = (SRC / "_footer.html").read_text()
    title = meta["title"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta['description']}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/style.css">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta['description']}">
<meta property="og:type" content="website">
</head>
<body>
{header}<main id="main">
{highlighted(body.strip())}
</main>
{footer}</body>
</html>
"""

def main():
    stale = []
    for page in sorted(SRC.glob("[!_]*.html")):
        out = ROOT / page.name
        text = render(page)
        if "--check" in sys.argv:
            if not out.exists() or out.read_text() != text:
                stale.append(out.name)
        else:
            out.write_text(text)
            print("wrote", out.name)
    if stale:
        sys.exit("out of date (run python3 build.py): " + ", ".join(stale))

main()
