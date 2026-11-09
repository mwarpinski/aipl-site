#!/usr/bin/env python3
"""The built site's own consistency (run after build.py): every local link and #anchor resolves, none uses the .html form
(Pages would redirect it), every page but the 404 has the canonical address it is served at, the social image exists,
and the host's files are well formed.

  python3 check_links.py
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from serve import PUBLIC, resolve, redirects, header_rules  # noqa: E402
from build import SITE, address  # noqa: E402

problems = []
pages = {p.name: p.read_text() for p in sorted(PUBLIC.glob("*.html"))}
redirect_sources = set(redirects())

for name, text in pages.items():
    for url in re.findall(r'(?:href|src)="([^"]+)"', text):
        if re.match(r"[a-z]+:", url) or url.startswith("//") or url.startswith("#") and url == "#":
            continue
        path, _, frag = url.partition("#")
        if path == "":
            target = PUBLIC / name
        elif path.startswith("/"):
            if path.endswith(".html"):
                problems.append(f"{name}: {url}: write {path[:-5] or '/'} (Pages redirects the .html form)")
                continue
            if path in redirect_sources:
                continue
            target = resolve(path)
        else:
            problems.append(f"{name}: {url}: a relative link (the pages are served from several depths; use /...)")
            continue
        if target is None or not target.is_file():
            problems.append(f"{name}: {url}: no such file")
        elif frag and target.suffix == ".html" and f'id="{frag}"' not in target.read_text():
            problems.append(f"{name}: {url}: no such anchor")
    if name == "404.html":
        if 'name="robots" content="noindex"' not in text:
            problems.append("404.html: not marked noindex")
    elif f'<link rel="canonical" href="{SITE}{address(name)}">' not in text:
        problems.append(f"{name}: no canonical address {SITE}{address(name)}")
    image = re.search(r'property="og:image" content="([^"]+)"', text)
    if not image or not image.group(1).startswith(SITE + "/") or not (PUBLIC / image.group(1)[len(SITE) + 1:]).is_file():
        problems.append(f"{name}: the og:image is not an absolute address of a file in public/")

for src, (dst, status) in redirects().items():
    if status not in (301, 302, 307, 308) or not src.startswith("/"):
        problems.append(f"_redirects: {src}: not a path with a redirect status")
    if resolve(src) is not None:
        problems.append(f"_redirects: {src}: a page is there already")

rules = dict(header_rules())
csp = rules.get("/*", {}).get("Content-Security-Policy", "")
if "default-src 'self'" not in csp or "unsafe-inline'" in csp.replace("style-src-attr 'unsafe-inline'", ""):
    problems.append("_headers: /* needs a Content-Security-Policy of 'self' only (inline allowed for style attributes alone)")
sitemap = (PUBLIC / "sitemap.xml").read_text()
for name in pages:
    if name != "404.html" and f"<loc>{SITE}{address(name)}</loc>" not in sitemap:
        problems.append(f"sitemap.xml: {name} is not listed")

if problems:
    sys.exit("\n".join(problems))
print(f"site ok: {len(pages)} pages, {len(redirect_sources)} redirects")
