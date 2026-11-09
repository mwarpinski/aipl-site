# aipl-site

The website for [AIPL](https://github.com/mwarpinski/AIPL), the AI Programming Language (aipl.sh). Plain HTML and CSS,
one small script, no framework and no external requests. `public/` is what gets hosted; the host runs no build.

```sh
python3 build.py              # writes public/ from src/, assets/ and static/
python3 build.py --check      # fails if public/ is not exactly what the sources make
python3 check_links.py        # every link and anchor, the canonical addresses, the host's files
python3 serve.py              # previews public/ at http://localhost:8000 the way Cloudflare Pages serves it
```

## Layout

| Path | What it is |
|---|---|
| `src/NAME.html` | a page body, after three front-matter lines (`title:`, `description:`, `nav:`). `src/_header.html` and `src/_footer.html` go around every page. A `<pre data-lang="aipl"><code>` block is syntax-highlighted by `build.py`. |
| `assets/` | the stylesheet, the script (tabs and copy buttons; the pages read fine without it), the icons and the social image. Copied to `public/assets/`. |
| `static/` | what the host reads: `_headers` (a strict Content-Security-Policy and other security headers, caching), `_redirects` (short addresses such as `/tour` and `/spec`), `robots.txt`. Copied to `public/`. |
| `public/` | the built site, committed. Edit the sources, never this folder: `build.py --check` fails when it differs. `sitemap.xml` is made here from the pages. |
| `serve.py` | a preview server with Cloudflare Pages' behaviour: pages without `.html` (`/x.html` is redirected to `/x`), the redirects, the headers. |

Pages are linked and canonical as `/install`, not `/install.html`, as Pages serves them; `check_links.py` fails on the
other form. The Content-Security-Policy allows nothing but this site's own files, and inline `style="..."` attributes
only (the benchmark bars): a page that needs a script or style in the page itself needs a change to `static/_headers`.

## Deploying (Cloudflare Pages)

Connect this repository to a Pages project with no build command and the output directory `public`. Every push to the
production branch then deploys. Add `aipl.sh` and `www.aipl.sh` as custom domains of the project. The code samples and
compiler output on the home page are real (README.md of AIPL, "An example"); what the site says about the language is
taken from the AIPL repository (README, FAQ, ROADMAP, docs/LAUNCH_NOTES.md), so when those change, change the page.
