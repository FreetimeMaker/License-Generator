import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import license_gen as app


class GeneratorTests(unittest.TestCase):
    def test_templates(self):
        for key, spdx in app.LICENSES.items():
            with self.subTest(key=key):
                self.assertEqual(app.license_key(spdx), key)
                output = app.render(key, "Müller", "2024-2026")
                self.assertTrue(output.endswith("\n"))
                if key in app.PERSONALIZED:
                    self.assertIn("Copyright (c) 2024-2026 Müller", output)
                else:
                    self.assertEqual(output, app.template(key).rstrip("\n") + "\n")

    def test_invalid_year_and_holder(self):
        for holder, year in [
            ("Ada", "2026-2024"),
            ("Ada", "24"),
            ("Ada\nBob", "2026"),
            ("", "2026"),
        ]:
            with self.subTest(holder=holder, year=year), self.assertRaises(ValueError):
                app.render("mit", holder, year)

    def test_config_and_quick_overwrite_protection(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict("os.environ", {"XDG_CONFIG_HOME": directory}),
        ):
            output = Path(directory) / "LICENSE"
            args = ["-q", "--year", "2026", "-o", str(output)]
            self.assertEqual(app.main(["--sl", "MIT"]), 0)
            self.assertEqual(app.main(["--sa", "Ada"]), 0)
            self.assertEqual(app.main(args), 0)
            self.assertEqual(app.main(args + ["--holder", "Bob"]), 1)
            self.assertIn("2026 Ada", output.read_text(encoding="utf-8"))
            self.assertEqual(app.main(args + ["--holder", "Bob", "--force"]), 0)
            self.assertIn("2026 Bob", output.read_text(encoding="utf-8"))
            self.assertEqual(app.main(["--rc"]), 0)
            self.assertEqual(app.load_config(), {})

    def test_interactive_selection(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(app, "load_config", return_value={}),
            patch.object(app, "git_author", return_value="Ada"),
            patch(
                "builtins.input",
                side_effect=["1", "", "2026", "My Project", "y", "yes"],
            ),
        ):
            output = Path(directory) / "LICENSE"
            output.write_text("Existing license", encoding="utf-8")
            self.assertEqual(app.main(["-o", str(output)]), 0)
            self.assertIn("2026 Ada", output.read_text(encoding="utf-8"))

    def test_project_filename(self):
        self.assertEqual(app.license_filename(""), "LICENSE")
        self.assertEqual(app.license_filename("My Project"), "LICENSE-My-Project")
        self.assertEqual(app.license_filename("../My/Project"), "LICENSE-My-Project")
