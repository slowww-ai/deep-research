# Deep Research

Static, mobile-first reading site for the deep-research reports produced by the
map-first research pipeline. One clean page per report + a landing index, hosted
on GitHub Pages so the reports can be read from anywhere.

**Live:** https://slowww-ai.github.io/deep-research/

## What's here

- `index.html` — landing page, one card per report.
- `<slug>.html` — one self-contained page per report (sidebar Contents, section
  filter, scroll-spy, light/dark, mobile-collapsible menu). All CSS/JS inline →
  loads instantly, works offline.
- `build_pages.py` — the generator.
- `.nojekyll` — serve files as-is (no Jekyll processing).

## Regenerate after editing a report

The generator reads each `../<slug>/report/REPORT.md` and rewrites the HTML here:

```bash
/Users/gieunkwak/Data_Analytics/SlowAI/contents_database/.venv/bin/python build_pages.py
```

Reports currently published (edit the `PROJECTS` list in `build_pages.py` to add/remove):

- `forward-deployed-engineering-korea`
- `stock-investing`
- `bioprocess-e2e`
- `second-brain`

## Deploy

The repo is connected to GitHub Pages (branch `main`, root). Just push:

```bash
git add -A && git commit -m "update reports" && git push
```

Pages redeploys automatically in ~1 minute.
