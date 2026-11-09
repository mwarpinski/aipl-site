#!/usr/bin/env python3
"""Builds the site into public/, the folder that gets hosted (Cloudflare Pages serves it; the host runs no build).

  python3 build.py          # writes everything in public/
  python3 build.py --check  # fails if public/ is not exactly what the sources make (for CI)

What goes into public/:
  - each page body in src/NAME.html, after the shared header and footer (src/_header.html, src/_footer.html);
  - assets/ as it is, and static/ (the host's files: _headers, _redirects, robots.txt) as it is;
  - sitemap.xml, made from the pages.
A page body starts with front matter lines `title:`, `description:`, `nav:` (which menu item is current), then a blank
line. A `<pre data-lang="aipl"><code>` block is syntax-highlighted. Pages are served without their .html (Cloudflare
Pages does this and redirects the other form), so links and canonical addresses are /install, not /install.html.
"""
import html, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC, OUT = ROOT / "src", ROOT / "public"
SITE = "https://aipl.sh"
SITE_NAME = "AIPL"
IMAGE = {"path": "/assets/og.png", "width": 1200, "height": 630, "alt": "AIPL, the AI Programming Language"}

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


def address(name):
    """The address a page is served at: index.html is /, install.html is /install."""
    stem = name[:-len(".html")]
    return "/" if stem == "index" else "/" + stem


def render(path):
    head, body = path.read_text().split("\n\n", 1)
    meta = dict(line.split(": ", 1) for line in head.splitlines())
    header = (SRC / "_header.html").read_text()
    header = re.sub(r"\{\{cur:(\w+)\}\}", lambda m: ' aria-current="page"' if m.group(1) == meta.get("nav") else "", header)
    footer = (SRC / "_footer.html").read_text()
    title, description = html.escape(meta["title"]), html.escape(meta["description"])
    if path.name == "404.html":
        # a missing page is not a page to index, and has no address of its own
        where = '<meta name="robots" content="noindex">\n'
    else:
        url = SITE + address(path.name)
        where = (f'<link rel="canonical" href="{url}">\n<meta property="og:url" content="{url}">\n')
    image = SITE + IMAGE["path"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="color-scheme" content="light dark">
{where}<link rel="icon" href="/assets/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/style.css">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="{IMAGE['width']}">
<meta property="og:image:height" content="{IMAGE['height']}">
<meta property="og:image:alt" content="{html.escape(IMAGE['alt'])}">
<meta name="twitter:card" content="summary_large_image">
</head>
<body>
{header}<main id="main">
{highlighted(body.strip())}
</main>
{footer}</body>
</html>
"""


def sitemap(pages):
    urls = "".join(f"  <url><loc>{SITE}{address(p.name)}</loc></url>\n" for p in pages if p.name != "404.html")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'


def expected():
    """Every file public/ must hold, as {path relative to public/: bytes}."""
    files = {}
    pages = sorted(SRC.glob("[!_]*.html"))
    for page in pages:
        files[page.name] = render(page).encode()
    for folder in ("assets", "static"):
        for f in sorted((ROOT / folder).rglob("*")):
            if f.is_file():
                rel = f.relative_to(ROOT / folder)
                files[(rel if folder == "static" else Path("assets") / rel).as_posix()] = f.read_bytes()
    files["sitemap.xml"] = sitemap(pages).encode()
    return files


def main():
    files = expected()
    if "--check" in sys.argv:
        have = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()} if OUT.is_dir() else set()
        problems = [f"missing: {n}" for n in sorted(set(files) - have)]
        problems += [f"not made from any source: {n}" for n in sorted(have - set(files))]
        problems += [f"out of date: {n}" for n in sorted(files) if n in have and (OUT / n).read_bytes() != files[n]]
        if problems:
            sys.exit("public/ is not what the sources make (run python3 build.py):\n  " + "\n  ".join(problems))
        print(f"public/ is up to date: {len(files)} files")
        return
    import shutil
    if OUT.exists():
        shutil.rmtree(OUT)
    for name, data in files.items():
        target = OUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(f"wrote {len(files)} files to public/")


if __name__ == "__main__":
    main()
