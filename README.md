# Arc to Chrome Bookmarks

Export [Arc browser](https://arc.net/)'s sidebar (spaces, folders, pinned and
regular tabs) into a standard Netscape bookmarks HTML file that any browser —
Chrome, Firefox, Safari, Edge, Brave, etc. — can import.

Arc stores its sidebar state in a `StorableSidebar.json` file with a fairly
gnarly internal structure (alternating key/value pairs, virtual containers for
pinned tabs, parent/child relationships by ID). This tool walks that
structure and produces a clean, folder-preserving bookmarks file.

*(Читать на русском: [README.ru.md](README.ru.md))*

## Why

Arc is shutting down / you're switching browsers, and you don't want to lose
years of organized tabs and folders. Browsers don't talk to each other
directly, but they all understand the Netscape bookmarks HTML format — so
that's the bridge.

## Usage

Requires Python 3.10+, no third-party dependencies.

1. Find `StorableSidebar.json` on your machine. On macOS it's typically under:
   ```
   ~/Library/Application Support/Arc/StorableSidebar.json
   ```
2. Run the exporter:
   ```bash
   python3 arc_to_chrome.py "/path/to/StorableSidebar.json" -o arc_bookmarks.html
   ```
   Or, if you copy `StorableSidebar.json` next to the script, just:
   ```bash
   python3 arc_to_chrome.py
   ```
3. Import `arc_bookmarks.html` into your new browser:
   - **Chrome**: `chrome://bookmarks` → ⋮ menu → *Import bookmarks*
   - **Firefox**: Bookmarks → Manage Bookmarks → Import and Backup → Import Bookmarks (HTML)
   - **Safari**: File → Import From → Bookmarks HTML File

### What gets exported

- Regular Arc folders, preserved via their parent/child relationships.
- Tabs that Arc's folder tree doesn't directly expose (e.g. pinned tabs living
  in a virtual container) are collected into a fallback folder named
  *"Arc — отдельные и закреплённые вкладки"* ("Arc — standalone and pinned
  tabs") so nothing gets silently dropped.
- Duplicate entries (same ID, or same title+URL) are skipped.

## Sanitizing a sidebar file before sharing it

If you want to attach your `StorableSidebar.json` to a bug report, or
contribute a new sample fixture, **don't share it raw** — it contains your
real browsing history, tab titles, and internal identifiers. Use the included
helper to redact it first:

```bash
python3 tools/sanitize_arc.py StorableSidebar.json -o StorableSidebar.sanitized.json
```

This replaces URLs, titles, and anything that looks like an email address,
ID, token, or similar sensitive value with predictable placeholders, while
keeping the JSON structure intact (so it's still useful as a test fixture).
**Always double-check the output by hand before sharing it** — this is a
best-effort filter, not a guarantee.

## Project layout

```
arc_to_chrome.py        # the exporter — StorableSidebar.json -> bookmarks HTML
tools/sanitize_arc.py   # redacts a sidebar file before sharing it
examples/                # a sanitized sample StorableSidebar.json for testing
tests/                   # test suite (stdlib unittest, no dependencies)
```

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0 — see [LICENSE](LICENSE).
