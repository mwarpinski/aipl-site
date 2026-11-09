#!/usr/bin/env python3
"""Previews public/ the way Cloudflare Pages serves it: pages without their .html (and /x.html sent to /x), the answers
of public/_redirects, the headers of public/_headers, and 404.html for a missing page.

  python3 serve.py [PORT]        # default 8000; then open http://localhost:8000
"""
import fnmatch, http.server, os, sys
from pathlib import Path

PUBLIC = Path(__file__).parent / "public"


def resolve(path):
    """The file in public/ that a request path is served from, or None: / is index.html, /x is x.html or the file x."""
    rel = path.strip("/")
    if rel == "":
        rel = "index"
    for candidate in (rel + ".html", rel):
        f = PUBLIC / candidate
        if f.is_file() and f.resolve().is_relative_to(PUBLIC.resolve()):
            return f
    return None


def redirects():
    out = {}
    f = PUBLIC / "_redirects"
    for line in f.read_text().splitlines() if f.exists() else []:
        line = line.strip()
        if line and not line.startswith("#"):
            src, dst, status = line.split()
            out[src] = (dst, int(status))
    return out


def header_rules():
    """[(pattern, {header: value})] from public/_headers: a line that starts at column 0 is a path pattern, and the
    indented lines under it are headers."""
    rules, current = [], None
    f = PUBLIC / "_headers"
    for line in f.read_text().splitlines() if f.exists() else []:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            current = (line.strip(), {})
            rules.append(current)
        else:
            name, value = line.strip().split(":", 1)
            current[1][name.strip()] = value.strip()
    return rules


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0].split("#")[0]
        if path.endswith(".html"):
            return self.send(308, location=path[:-len(".html")] or "/")
        if path in redirects():
            dst, status = redirects()[path]
            return self.send(status, location=dst)
        f = resolve(path)
        if f is None:
            return self.send(404, body=(PUBLIC / "404.html").read_bytes(), kind="text/html; charset=utf-8")
        kind = {".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".png": "image/png",
                ".svg": "image/svg+xml", ".xml": "application/xml", ".txt": "text/plain"}.get(f.suffix, "application/octet-stream")
        self.send(200, body=f.read_bytes(), kind=kind, served=path)

    do_HEAD = do_GET

    def send(self, status, body=b"", kind="text/plain", location=None, served=None):
        self.send_response(status)
        if location:
            self.send_header("Location", location)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        for pattern, headers in header_rules():
            if fnmatch.fnmatch(served or self.path, pattern):
                for name, value in headers.items():
                    self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"serving public/ at http://localhost:{port}")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
