# Contributing

Contributions are welcome — bug reports, fixes for folder/tab edge cases,
new test fixtures, or documentation improvements.

## Setup

No dependencies to install. You need Python 3.10+.

```bash
git clone <this repo>
cd ArcToHtml
python3 -m unittest discover -s tests -v
```

## Reporting a bug

Arc's internal JSON structure has a lot of quirks (virtual containers,
pairwise-encoded lists, inconsistent nesting). If `arc_to_chrome.py` mishandles
your sidebar, please open an issue and include:

1. What went wrong (missing tabs, wrong folder structure, a crash/traceback).
2. A **sanitized** copy of your `StorableSidebar.json`, produced with:
   ```bash
   python3 tools/sanitize_arc.py StorableSidebar.json -o StorableSidebar.sanitized.json
   ```
   Please double-check the sanitized file by hand before attaching it — never
   attach the raw file.

## Adding a test fixture

If you find a structural edge case not covered by `examples/StorableSidebar.example.json`,
a minimal sanitized fixture reproducing it is very welcome. Keep fixtures as
small as possible while still reproducing the issue.

## Pull requests

- Keep changes focused; avoid unrelated reformatting.
- Add or update a test in `tests/` for behavior changes.
- Run the test suite before submitting:
  ```bash
  python3 -m unittest discover -s tests -v
  ```
- Describe *why* the change is needed, not just what it does.

## Code style

Plain, typed, dependency-free Python (stdlib only). No linter is enforced,
but please keep functions small and match the existing style.
