# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Initial public release: `arc_to_chrome.py` exports Arc's `StorableSidebar.json`
  sidebar (folders, pinned and regular tabs) to a Netscape bookmarks HTML file.
- `tools/sanitize_arc.py` to redact a sidebar file before sharing it.
- CLI arguments for input/output paths on both scripts (previously hardcoded).
- Test suite (`tests/`) and a sanitized sample fixture (`examples/`).
- GitHub Actions workflow running the test suite on Python 3.10–3.12.
- Project documentation (README in English and Russian, CONTRIBUTING, LICENSE).
