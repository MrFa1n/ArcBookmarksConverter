# Example fixture

`StorableSidebar.example.json` is a real Arc sidebar export that has been run
through `tools/sanitize_arc.py` (twice) to strip all URLs, titles, and
identifying values. It's used by the test suite in `tests/` and is safe to
inspect — it contains no real browsing data.

Structure (spaces, folders, parent/child relationships) is preserved, which is
what makes it useful for testing `arc_to_chrome.py`.
