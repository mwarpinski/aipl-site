# aipl-site

The website for [AIPL](https://github.com/mwarpinski/AIPL), the AI Programming Language (aipl.sh). Plain HTML and CSS,
one small script, no framework and no external requests: the pages in the repository root are what gets hosted, on any
static host.

```sh
python3 build.py                 # stamps src/_header.html and src/_footer.html around src/*.html into ./*.html
python3 -m http.server 8000      # then open http://localhost:8000
python3 build.py --check         # CI: the pages in the root are up to date with src/
python3 check_links.py           # CI: every local link and anchor resolves
```

- `src/NAME.html`: a page body, after three front-matter lines (`title:`, `description:`, `nav:`). A
  `<pre data-lang="aipl"><code>` block is syntax-highlighted by `build.py`.
- `assets/`: `style.css` (colors are tokens on `:root`; dark follows the system), `site.js` (tabs and copy buttons; the
  pages read fine without it), `favicon.svg`.
- Everything the site says about the language is taken from the AIPL repository (README, FAQ, ROADMAP,
  docs/LAUNCH_NOTES.md). When those change, change the page.
- Edit `src/`, never the generated root files.

The code samples and compiler output on the home page are real (README.md of AIPL, "An example").
