"""Run with: python3 -m unittest discover -s tests"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "arc_to_chrome.py"
EXAMPLE = ROOT / "examples" / "StorableSidebar.example.json"


def run_exporter(input_file: Path, output_file: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(input_file), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )


class ArcToChromeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name) / "bookmarks.html"
        result = run_exporter(EXAMPLE, self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.stdout = result.stdout
        self.html = self.output.read_text(encoding="utf-8")

    def test_produces_valid_netscape_bookmarks_file(self) -> None:
        self.assertTrue(self.html.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>"))
        self.assertIn("Файл создан", self.stdout)

    def test_one_top_level_folder_per_space(self) -> None:
        # The fixture has two Spaces: "Work" and "Personal".
        self.assertIn("<DT><H3>Work</H3>", self.html)
        self.assertIn("<DT><H3>Personal</H3>", self.html)

    def test_folder_nesting_and_order_preserved_within_a_space(self) -> None:
        # Inside "Work": the pinned "Mail" tab first, then "Research"
        # (containing "Drafts"), then the "Dashboard" tab — in source order.
        work_start = self.html.index("<DT><H3>Work</H3>")
        personal_start = self.html.index("<DT><H3>Personal</H3>")
        work_section = self.html[work_start:personal_start]

        mail_pos = work_section.index('HREF="https://example.com/mail"')
        research_pos = work_section.index("<DT><H3>Research</H3>")
        drafts_pos = work_section.index("<DT><H3>Drafts</H3>")
        dashboard_pos = work_section.index('HREF="https://example.com/dashboard"')

        self.assertTrue(mail_pos < research_pos < drafts_pos < dashboard_pos)

    def test_pinned_tabs_are_flattened_into_the_space_folder(self) -> None:
        # No extra "Pinned" wrapper folder anywhere in the output.
        self.assertNotIn("<DT><H3>Pinned</H3>", self.html)

        work_start = self.html.index("<DT><H3>Work</H3>")
        personal_start = self.html.index("<DT><H3>Personal</H3>")
        work_section = self.html[work_start:personal_start]
        self.assertIn('HREF="https://example.com/mail"', work_section)

    def test_space_without_pinned_tabs_still_exports_its_other_tabs(self) -> None:
        personal_start = self.html.index("<DT><H3>Personal</H3>")
        personal_section = self.html[personal_start:]
        self.assertIn('HREF="https://example.com/recipes"', personal_section)

    def test_tab_pinned_directly_to_a_space_lands_in_that_spaces_folder(self) -> None:
        # "tab-personal-pinned-direct" has parentID == the Space's own id
        # (pinned straight to the Space, not in a folder, not in the
        # "pinned" container) and must not fall into the fallback folder.
        personal_start = self.html.index("<DT><H3>Personal</H3>")
        personal_section = self.html[personal_start:]
        self.assertIn('HREF="https://example.com/calendar"', personal_section)
        self.assertNotIn("Arc — Shared Pinned", self.html)

    def test_orphan_tab_not_tied_to_any_space_still_exported(self) -> None:
        self.assertIn('HREF="https://example.com/orphan"', self.html)

    def test_missing_input_file_exits_with_error(self) -> None:
        missing = Path(self.tmp.name) / "does_not_exist.json"
        result = run_exporter(missing, self.output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Не найден файл", result.stderr)


if __name__ == "__main__":
    unittest.main()
