"""Run with: python3 -m unittest discover -s tests"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "arc_to_bookmarks.py"
EXAMPLE = ROOT / "examples" / "StorableSidebar.example.json"


def run_exporter(input_file: Path, output_file: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(input_file), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )


class ArcToBookmarksTests(unittest.TestCase):
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
        # Inside "Work": "Mail" first, then "Research" (containing
        # "Drafts"), then the "Dashboard" tab — in source order. "Work"'s
        # containers are discovered purely via itemContainer scanning (no
        # containerIDs/newContainerIDs field at all on that Space record).
        work_start = self.html.index("<DT><H3>Work</H3>")
        personal_start = self.html.index("<DT><H3>Personal</H3>")
        work_section = self.html[work_start:personal_start]

        mail_pos = work_section.index('HREF="https://example.com/mail"')
        research_pos = work_section.index("<DT><H3>Research</H3>")
        drafts_pos = work_section.index("<DT><H3>Drafts</H3>")
        dashboard_pos = work_section.index('HREF="https://example.com/dashboard"')

        self.assertTrue(mail_pos < research_pos < drafts_pos < dashboard_pos)

    def test_childrenids_order_wins_over_file_appearance_order(self) -> None:
        # "folder-work-research" declares childrenIds =
        # ["folder-work-drafts", "tab-work-research-1"] — the reverse of the
        # order those two records actually appear in sidebar.items. Arc's
        # own childrenIds is authoritative, so "Drafts" must come first.
        work_start = self.html.index("<DT><H3>Work</H3>")
        personal_start = self.html.index("<DT><H3>Personal</H3>")
        work_section = self.html[work_start:personal_start]

        drafts_pos = work_section.index("<DT><H3>Drafts</H3>")
        research_1_pos = work_section.index('HREF="https://example.com/research1"')
        self.assertTrue(drafts_pos < research_1_pos)

    def test_container_not_listed_in_containerids_is_still_picked_up(self) -> None:
        # "Personal" only declares "personal-declared-root" in containerIDs;
        # "personal-extra-root" (holding the "Calendar" tab) is a second
        # spaceItems container for the same Space, found only via the
        # itemContainer scan, and must still land inside "Personal".
        personal_start = self.html.index("<DT><H3>Personal</H3>")
        shared_pinned_start = self.html.index("<DT><H3>Arc — Shared Pinned</H3>")
        personal_section = self.html[personal_start:shared_pinned_start]
        self.assertIn('HREF="https://example.com/recipes"', personal_section)
        self.assertIn('HREF="https://example.com/calendar"', personal_section)

    def test_pinned_like_tab_is_flattened_with_no_extra_subfolder(self) -> None:
        # No "Pinned" wrapper folder anywhere in the output — pinned-ish
        # tabs are listed directly inside their Space's folder.
        self.assertNotIn("<DT><H3>Pinned</H3>", self.html)

    def test_top_apps_go_into_their_own_shared_pinned_folder(self) -> None:
        # Arc's global "Top Apps" row isn't owned by either Space, so it
        # gets its own top-level folder instead of leaking into a generic
        # "Папка Arc" folder or either Space's folder.
        self.assertIn("<DT><H3>Arc — Shared Pinned</H3>", self.html)
        shared_pinned_start = self.html.index("<DT><H3>Arc — Shared Pinned</H3>")
        shared_pinned_section = self.html[shared_pinned_start:]
        self.assertIn('HREF="https://example.com/news"', shared_pinned_section)

        work_start = self.html.index("<DT><H3>Work</H3>")
        personal_start = self.html.index("<DT><H3>Personal</H3>")
        self.assertNotIn('HREF="https://example.com/news"', self.html[work_start:personal_start])
        self.assertNotIn(
            'HREF="https://example.com/news"', self.html[personal_start:shared_pinned_start]
        )

    def test_orphan_tab_not_tied_to_any_space_still_exported(self) -> None:
        self.assertIn('HREF="https://example.com/orphan"', self.html)

    def test_missing_input_file_exits_with_error(self) -> None:
        missing = Path(self.tmp.name) / "does_not_exist.json"
        result = run_exporter(missing, self.output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Не найден файл", result.stderr)


if __name__ == "__main__":
    unittest.main()
