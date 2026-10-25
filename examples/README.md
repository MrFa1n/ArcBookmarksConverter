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

It models the real `data.itemContainer.containerType` shape Arc uses for
root containers (`spaceItems` per Space, `topApps` shared globally) rather
than the Space's own `containerIDs`/`newContainerIDs` lists, which have
proven unreliable (see `arc_to_bookmarks.py`'s docstring). It exercises:

- one top-level folder per Space, each named after the Space;
- nested folders preserved in source order (`Work` → `Research` → `Drafts`);
- within "Research", content ordered by its declared `childrenIds`
  (`Drafts` before the "Research Paper 1" tab) rather than by the order
  those records happen to appear in `sidebar.items`, which doesn't match;
- a pinned-like tab (`Work`'s "Mail") flattened directly into the Space
  folder, listed first, with no extra `Pinned` subfolder — `Work`'s whole
  container is found purely via the `itemContainer` scan (no
  `containerIDs`/`newContainerIDs` field on that Space at all);
- a second root container for `Personal` ("Calendar") that *isn't* listed
  in its `containerIDs`, to prove such containers are still picked up;
- Arc's "Top Apps" row (`tab-shared-news`), shared across Spaces rather
  than owned by one, landing in its own `Arc — Shared Pinned` folder;
- a tab with no reachable parent (`tab-orphan`), which still gets exported
  outside of any Space folder instead of being silently dropped.

`tests/test_arc_to_bookmarks.py` runs the exporter against this fixture and
asserts on exactly this structure.
