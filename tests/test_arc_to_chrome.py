"""Run with: python3 -m unittest discover -s tests"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "arc_to_chrome.py"
EXAMPLE = ROOT / "examples" / "StorableSidebar.example.json"


class ArcToChromeTests(unittest.TestCase):
    def test_converts_example_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bookmarks.html"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(EXAMPLE), "-o", str(output)],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Файл создан", result.stdout)
            self.assertTrue(output.exists())

            html = output.read_text(encoding="utf-8")
            self.assertTrue(html.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>"))
            self.assertIn("<DT><A HREF=", html)

    def test_missing_input_file_exits_with_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does_not_exist.json"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(missing)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Не найден файл", result.stderr)


if __name__ == "__main__":
    unittest.main()
