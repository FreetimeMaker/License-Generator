import io
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import license_gen as app


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        app.license_text.cache_clear()
        self.addCleanup(app.license_text.cache_clear)
        offline = patch.object(app, "urlopen", side_effect=OSError("Offline"))
        self.urlopen = offline.start()
        self.addCleanup(offline.stop)

    def test_online_text_preferred_and_cached(self):
        self.urlopen.side_effect = None
        self.urlopen.return_value = io.BytesIO(
            json.dumps(
                {
                    "licenseId": "MIT",
                    "licenseText": "Online text\nCopyright (c) <year> <copyright holders>\n",
                }
            ).encode("utf-8")
        )
        with patch.object(
            app, "template", side_effect=AssertionError("Unexpected fallback")
        ):
            self.assertEqual(
                app.render("mit", "Ada", "2026"),
                "Online text\nCopyright (c) 2026 Ada\n",
            )
            self.assertTrue(app.license_text("mit").startswith("Online text"))
        self.urlopen.assert_called_once_with(
            "https://spdx.org/licenses/MIT.json", timeout=2
        )

    def test_wrong_online_id_uses_fallback(self):
        self.urlopen.side_effect = None
        self.urlopen.return_value = io.BytesIO(
            b'{"licenseId":"MIT","licenseText":"Wrong text"}'
        )
        self.assertEqual(app.license_text("apache-2.0"), app.template("apache-2.0"))

    def test_catalog(self):
        self.assertEqual(len(app.LICENSES), 187)
        self.assertEqual(
            set(app.LICENSES.values()),
            {path.stem for path in app.TEMPLATES_DIR.glob("*.txt")},
        )
        self.assertEqual(app.license_key("GPL-3.0-only"), "gpl-3.0")
        self.assertEqual(app.license_key("GPL-3.0-OR-LATER"), "gpl-3.0-or-later")
        self.assertEqual(app.license_key("EUPL-1.2"), "eupl-1.2")

    def test_platform_aliases(self):
        for alias in ("gfdl-1.3", "lgpl-3.0"):
            with self.subTest(alias=alias):
                self.assertEqual(app.license_key(alias.upper()), f"{alias}-only")
                self.assertEqual(
                    app.license_key(f"{alias}-or-later"), f"{alias}-or-later"
                )

    def test_templates(self):
        for key, spdx in app.LICENSES.items():
            with self.subTest(key=key):
                self.assertEqual(app.license_key(spdx), key)
                output = app.render(key, "Müller", "2024-2026")
                self.assertTrue(output.strip())
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

    def test_combined_cli_with_editor(self):
        editor = shlex.join(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; import sys; p = Path(sys.argv[1]); "
                "p.write_text('Licensing notice\\n\\n' + p.read_text(encoding='utf-8'), encoding='utf-8')",
            ]
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict("os.environ", {"XDG_CONFIG_HOME": directory, "VISUAL": editor}),
        ):
            output = Path(directory) / "LICENSE"
            self.assertEqual(
                app.main(
                    [
                        "-q",
                        "--edit",
                        "--license",
                        "MIT",
                        "--license",
                        "Apache-2.0",
                        "--holder",
                        "Ada",
                        "--year",
                        "2026",
                        "-o",
                        str(output),
                    ]
                ),
                0,
            )
            expected = "Licensing notice\n\n" + app.render("mit", "Ada", "2026")
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                expected + "\n" + app.render("apache-2.0"),
            )

    @unittest.skipUnless(shutil.which("git"), "Git is required")
    def test_copyright_year_from_first_commit(self):
        with tempfile.TemporaryDirectory() as directory:

            def git(*args):
                subprocess.run(
                    ["git", *args], cwd=directory, check=True, capture_output=True
                )

            git("init", "-q")
            git(
                "-c",
                "user.name=Ada",
                "-c",
                "user.email=ada@example.test",
                "commit",
                "--allow-empty",
                "--date=2014-06-01T12:00:00+00:00",
                "-m",
                "First",
            )
            git(
                "-c",
                "user.name=Ada",
                "-c",
                "user.email=ada@example.test",
                "commit",
                "--allow-empty",
                "--date=2025-06-01T12:00:00+00:00",
                "-m",
                "Second",
            )
            self.assertEqual(app.copyright_year(directory), "2014")

    def test_interactive_selection(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(app, "load_config", return_value={}),
            patch.object(app, "git_author", return_value="Default author"),
            patch.object(app, "copyright_year", return_value="2026"),
            patch(
                "builtins.input",
                side_effect=["1, Apache-2.0", "My Project", "Ada", "y", "yes"],
            ),
        ):
            output = Path(directory) / "LICENSE"
            output.write_text("Existing license", encoding="utf-8")
            self.assertEqual(app.main(["-o", str(output)]), 0)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                app.render("mit", "Ada", "2026") + "\n" + app.render("apache-2.0"),
            )

    def test_project_filename(self):
        self.assertEqual(app.license_filename(""), "LICENSE")
        self.assertEqual(app.license_filename("My Project"), "LICENSE-My-Project")
        self.assertEqual(app.license_filename("../My/Project"), "LICENSE-My-Project")
