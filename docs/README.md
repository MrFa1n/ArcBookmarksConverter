# Web version (GitHub Pages)

A static, dependency-free page that does the same conversion as
`arc_to_chrome.py` entirely in the browser — no upload, no server, no
build step.

- `index.html` — the page (drop zone, stats, download button).
- `arc-converter.js` — the conversion logic. This is a deliberate,
  function-for-function port of `arc_to_chrome.py` at the repo root; see
  that file's docstrings for *why* each step exists. Keep the two in sync
  when fixing a bug or changing behavior in one — both are validated to
  produce byte-identical output against `examples/StorableSidebar.example.json`.
- `app.js` — DOM wiring only (file picker, drag & drop, rendering stats,
  triggering the download). No conversion logic belongs here.

## Running it locally

```bash
cd docs && python3 -m http.server 8000
```

Then open `http://localhost:8000/`.

## Verifying the JS port against the Python original

```bash
python3 arc_to_chrome.py examples/StorableSidebar.example.json -o /tmp/py.html
node -e '
const { convertArcSidebarToBookmarksHtml } = require("./docs/arc-converter.js");
const fs = require("fs");
const source = JSON.parse(fs.readFileSync("examples/StorableSidebar.example.json", "utf-8"));
fs.writeFileSync("/tmp/js.html", convertArcSidebarToBookmarksHtml(source).html);
'
diff /tmp/py.html /tmp/js.html && echo IDENTICAL
```

## Enabling GitHub Pages

In the repo's Settings → Pages, set Source to "Deploy from a branch",
branch `main`, folder `/docs`.
