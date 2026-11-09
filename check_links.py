#!/usr/bin/env python3
"""Every local link (href and src starting with /) in the built pages resolves to a file, and every #fragment to an id."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent
pages = {p.name: p.read_text() for p in ROOT.glob("*.html")}
bad = []
for name, text in pages.items():
    for url in re.findall(r'(?:href|src)="([^"]+)"', text):
        if re.match(r"[a-z]+:", url) or url.startswith("//"):
            continue
        path, _, frag = url.partition("#")
        target = name if path == "" else ("index.html" if path == "/" else path.lstrip("/"))
        if not (ROOT / target).is_file():
            bad.append(f"{name}: {url}: no such file")
        elif frag and f'id="{frag}"' not in (pages.get(target) or (ROOT / target).read_text()):
            bad.append(f"{name}: {url}: no such anchor")
if bad:
    sys.exit("\n".join(bad))
print(f"links ok: {len(pages)} pages")
