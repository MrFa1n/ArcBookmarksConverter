# Example fixture

`StorableSidebar.example.json` is a small, hand-written, fully synthetic
sidebar file — it contains no real browsing data, just placeholder URLs and
titles (`example.com`, "Research Paper 1", etc.).

It's intentionally synthetic rather than a sanitized real export: Arc's
structure relies on `id`/`parentID` links, and a value-scrambling sanitizer
can't anonymize those without breaking them (which is also why
`tools/sanitize_arc.py` now keeps a stable per-value mapping — see its
docstring). A synthetic fixture lets us keep that structure both correct and
easy to read.

It models two Arc Spaces ("Work" and "Personal") to exercise:

- one top-level folder per Space, each named after the Space;
- nested folders preserved in source order (`Work` → `Research` → `Drafts`);
- a pinned tab collected into a `Pinned` subfolder (`Work` only — `Personal`
  has none, so it gets no `Pinned` subfolder at all);
- a tab with no reachable parent (`tab-orphan`), which still gets exported
  outside of any Space folder instead of being silently dropped.

`tests/test_arc_to_chrome.py` runs the exporter against this fixture and
asserts on exactly this structure.
