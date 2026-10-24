# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Initial public release: `arc_to_chrome.py` exports Arc's `StorableSidebar.json`
  sidebar (folders, pinned and regular tabs) to a Netscape bookmarks HTML file.
- One top-level bookmarks folder per Arc Space, so the number of imported
  subfolders matches the number of Spaces in Arc, instead of one flat pile.
  Every root container Arc keeps for a Space (there's often more than one)
  is flattened directly into that Space's folder, no extra wrapper subfolder.
  Root containers are identified by their own declared type
  (`data.itemContainer.containerType`) rather than a Space's
  `containerIDs`/`newContainerIDs` marker words, which have proven
  unreliable/inconsistently ordered across real exports.
- Arc's "Top Apps" row (shown identically under every Space — shared rather
  than owned by any one of them) gets its own top-level folder, "Arc —
  Shared Pinned", instead of leaking into a generic untitled folder.
- `tools/sanitize_arc.py` to redact a sidebar file before sharing it.
- CLI arguments for input/output paths on both scripts (previously hardcoded).
- Test suite (`tests/`) and a synthetic sample fixture (`examples/`).
- GitHub Actions workflow running the test suite on Python 3.10–3.12.
- Project documentation (README in English and Russian, CONTRIBUTING, LICENSE).

### Fixed
- `tools/sanitize_arc.py` now maps each original value to a single stable
  placeholder, instead of a fresh one per occurrence — previously this broke
  `id`/`parentID` links in the sanitized output, making it structurally
  useless for reproducing folder-nesting bugs.
- `tools/sanitize_arc.py` now also redacts the "key" half of Arc's
  alternating `[id, object, id, object, ...]`-encoded collections (e.g.
  `sidebar.spaces`, `sidebar.items`) and `*device*`-named fields — these
  previously inherited their parent list/key's name, which didn't match the
  sensitive-key check, and leaked real UUIDs into the "sanitized" output.
