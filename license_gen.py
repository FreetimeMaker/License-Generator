"""Online-first license generator with offline templates and an optional PyQt6 GUI."""

import argparse
import json
import os
import re
import shlex
import subprocess
import tempfile
from datetime import date
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

VERSION = "1.2.0"

LICENSES = dict(
    zip(
        "mit apache-2.0 bsd-2-clause bsd-3-clause agpl-3.0 bsl-1.0 cc0-1.0 epl-2.0 gpl-2.0 gpl-3.0 lgpl-2.1 mpl-2.0 unlicense".split(),
        "MIT Apache-2.0 BSD-2-Clause BSD-3-Clause AGPL-3.0-only BSL-1.0 CC0-1.0 EPL-2.0 GPL-2.0-only GPL-3.0-only LGPL-2.1-only MPL-2.0 Unlicense".split(),
    )
)
TEMPLATES_DIR = Path(__file__).with_name("templates")
# Preserve existing menu positions and short IDs when adding SPDX templates.
_legacy_ids = set(LICENSES.values())
LICENSES.update(
    (path.stem.lower(), path.stem)
    for path in sorted(TEMPLATES_DIR.glob("*.txt"), key=lambda path: path.stem.lower())
    if path.stem not in _legacy_ids
)
PERSONALIZED = {
    "mit": "<copyright holders>",
    "bsd-2-clause": "<owner>",
    "bsd-3-clause": "<owner>",
}


# GitHub and GitLab still use these unsuffixed keys for their GNU templates.
PLATFORM_ALIASES = {
    "gfdl-1.3": "gfdl-1.3-only",
    "lgpl-3.0": "lgpl-3.0-only",
}


def license_key(value):
    normalized = value.lower()
    normalized = PLATFORM_ALIASES.get(normalized, normalized)
    for key, spdx in LICENSES.items():
        if normalized in (key, spdx.lower()):
            return key
    raise ValueError(f"Unknown license: {value}")


def template(key):
    return (TEMPLATES_DIR / (LICENSES[key] + ".txt")).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def license_text(key):
    spdx = LICENSES[key]
    try:
        url = f"https://spdx.org/licenses/{quote(spdx, safe='')}.json"
        with urlopen(url, timeout=2) as response:
            data = json.loads(response.read(2_000_000))
        if isinstance(data, dict) and data.get("licenseId") == spdx:
            text = data.get("licenseText")
            if isinstance(text, str) and text.strip():
                return text
    except (OSError, ValueError):
        pass
    return template(key)


def render(key, holder="", year=""):
    values = {}
    if key in PERSONALIZED:
        holder, year = holder.strip(), year.strip()
        if not holder or len(holder.splitlines()) != 1:
            raise ValueError("Enter a copyright holder on one line.")
        if not re.fullmatch(r"[0-9]{4}(?:-[0-9]{4})?", year) or year[:4] > year[-4:]:
            raise ValueError(
                "Enter a year (YYYY) or a year range (YYYY-YYYY) in ascending order."
            )
        values = {"<year>": year, PERSONALIZED[key]: holder}
    text = license_text(key)
    if values:
        text = re.sub(
            "|".join(map(re.escape, values)), lambda match: values[match[0]], text
        )
    return text.rstrip("\n") + "\n"


def config_path():
    return (
        Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        / "license-gen"
        / "config.json"
    )


def load_config():
    try:
        data = json.loads(config_path().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict) or any(
        not isinstance(value, str) for value in data.values()
    ):
        raise ValueError("Invalid configuration file. Use --rc to reset it.")
    return data


def save_config(data):
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def git_author():
    try:
        return subprocess.run(
            ["git", "config", "--get", "user.name"],
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def git_root(directory):
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return Path(result.stdout.rstrip("\n")) if result.returncode == 0 else None


def copyright_year(directory=None):
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--max-parents=0",
                "--format=%ad",
                "--date=format:%Y",
                "HEAD",
            ],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return str(date.today().year)
    years = re.findall(r"^[0-9]{4}$", result.stdout, re.MULTILINE)
    return min(years) if result.returncode == 0 and years else str(date.today().year)


def write_license(path, text, confirm, force=False):
    try:
        with path.open("x", encoding="utf-8", newline="\n") as output:
            output.write(text)
    except FileExistsError:
        if not force and not confirm():
            return False
        with path.open("w", encoding="utf-8", newline="\n") as output:
            output.write(text)
    return True


def choose(default):
    keys = list(LICENSES)
    for index, key in enumerate(keys, 1):
        print(f"{index:2}. {LICENSES[key]}")
    raw = input(f"Licenses (comma-separated numbers or IDs) [{default}]: ").strip()
    selected = []
    for item in (raw or default).split(","):
        item = item.strip()
        if item.isdecimal() and 1 <= int(item) <= len(keys):
            selected.append(keys[int(item) - 1])
        else:
            selected.append(license_key(item))
    return selected


def edit_text(text):
    editor = shlex.split(os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi")
    if not editor:
        raise ValueError("Set VISUAL or EDITOR to a valid editor command.")
    with tempfile.TemporaryDirectory() as directory:
        draft = Path(directory) / "LICENSE"
        draft.write_text(text, encoding="utf-8")
        result = subprocess.run([*editor, str(draft)])
        if result.returncode != 0:
            raise ValueError(
                f"Editor exited with status {result.returncode}; license not saved."
            )
        text = draft.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("The edited license is empty; license not saved.")
    return text.rstrip("\n") + "\n"


def license_filename(project):
    name = re.sub(r"[^\w-]+", "-", project.strip()).strip("-_")
    return f"LICENSE-{name[:50]}" if name else "LICENSE"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate open-source licenses.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-q", "--quick", action="store_true", help="Generate without prompting"
    )
    mode.add_argument("--gui", action="store_true", help="Open the PyQt6 interface")
    mode.add_argument("--ls", action="store_true", help="List available licenses")
    mode.add_argument(
        "-i", "--info", metavar="LICENSE", help="Show the original license text"
    )
    mode.add_argument("--sl", metavar="LICENSE", help="Save the default license")
    mode.add_argument("--sa", metavar="NAME", help="Save the default author")
    mode.add_argument("--sc", action="store_true", help="Show saved defaults")
    mode.add_argument("--rc", action="store_true", help="Clear saved defaults")
    parser.add_argument(
        "--license", action="append", help="Specify a license ID (repeat to combine)"
    )
    parser.add_argument(
        "--edit", action="store_true", help="Edit the license text before saving"
    )
    parser.add_argument("--holder", help="Specify the copyright holder")
    parser.add_argument("--year", help="Specify the year or year range")
    parser.add_argument("--project", help="Project name for the suggested filename")
    parser.add_argument("-o", "--output", type=Path, help="Specify the output file")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite the existing output file"
    )
    args = parser.parse_args(argv)
    if args.edit and any(
        (
            args.gui,
            args.ls,
            args.info is not None,
            args.sl is not None,
            args.sa is not None,
            args.sc,
            args.rc,
        )
    ):
        parser.error("--edit is only available when generating a license from the CLI")
    try:
        if args.ls:
            for key, spdx in LICENSES.items():
                print(f"{key}: {spdx}")
            return 0
        if args.info is not None:
            print(license_text(license_key(args.info)).rstrip())
            return 0
        if args.rc:
            config_path().unlink(missing_ok=True)
            return 0
        config = load_config()
        if args.sl is not None or args.sa is not None:
            if args.sl is not None:
                config["license"] = license_key(args.sl)
            else:
                config["author"] = args.sa.strip()
            save_config(config)
            return 0
        if args.sc:
            print(json.dumps(config, ensure_ascii=False, indent=2))
            return 0
        if args.gui:
            from license_gui import run

            return run(config, args.project or "")
        default = config.get("license", "mit")
        keys = (
            [license_key(value) for value in args.license]
            if args.license is not None
            else ([license_key(default)] if args.quick else choose(default))
        )
        labels = ", ".join(LICENSES[key] for key in keys)
        holder = (
            args.holder
            if args.holder is not None
            else config.get("author") or git_author()
        )
        project = args.project
        if not args.quick:
            if project is None:
                project = input("Project name (optional): ")
            if args.holder is None:
                prompt = (
                    f"Author / copyright holder [{holder}]: "
                    if holder
                    else "Author / copyright holder: "
                )
                holder = input(prompt).strip() or holder
        year = args.year if args.year is not None else copyright_year()
        text = (
            "\n\n".join(render(key, holder, year).rstrip("\n") for key in keys) + "\n"
        )
        if args.edit:
            text = edit_text(text)
        output = args.output or Path(license_filename(project or ""))
        if not args.quick and input(
            f"Write {labels} to {output}? [y/N] "
        ).strip().lower() not in {"y", "yes"}:
            return 0
        if not write_license(
            output,
            text,
            lambda: (
                not args.quick
                and input(f"Overwrite {output}? [y/N] ").strip().lower() in {"y", "yes"}
            ),
            args.force,
        ):
            print(f"File unchanged: {output}")
            return 1
        print(f"{labels} saved to: {output}")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nCanceled.")
        return 130
    except (OSError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
