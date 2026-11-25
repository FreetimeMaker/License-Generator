# License Generator

## This Repo is sponsored by

[![Sponsor](https://readme.cash/i/gg9k963fkf.svg)](https://readme.cash/c/gg9k963fkf)

License Generator is a free and open-source tool for creating license files on Linux. It provides an interactive terminal menu and a graphical desktop app. Both work offline and share the same templates and settings.

Built with **Python 3** and **PyQt6**. The command-line interface uses only the Python standard library. Inspired by [anth0nycodes/license-generator](https://github.com/anth0nycodes/license-generator).

## Features

### Supported Licenses

- **187 offline templates** covering every non-deprecated entry in the [SPDX License List v3.29.0](https://github.com/spdx/license-list-data/tree/v3.29.0) marked OSI-approved or FSF-libre.
- **GitHub and GitLab coverage**: Includes the licenses offered by [GitHub's Choose a License catalog](https://github.com/github/choosealicense.com/tree/gh-pages/_licenses) and the [GitLab.com license templates API](https://gitlab.com/api/v4/templates/licenses). The generator uses its own bundled texts, not byte-for-byte copies of the platform templates.
- **Short identifiers**: `gpl-3.0`, `gfdl-1.3`, and `lgpl-3.0` select their `-only` variants. Use the explicit SPDX ID to select an `-or-later` variant. Deprecated SPDX IDs and exceptions are not separate templates.

### Key Capabilities

- **Preview, copy, and save** license text from the desktop app, or generate a license directly from the terminal.
- **Copyright details**: Fill in the holder and year for MIT, BSD-2-Clause, and BSD-3-Clause. The holder defaults to the saved author or Git user name, and the year defaults to the current year.
- **Shared defaults**: Settings are stored in `$XDG_CONFIG_HOME/license-gen/config.json` or `~/.config/license-gen/config.json`.
- **Project-specific filenames**: The optional project name changes the suggested filename (for example, `LICENSE-My-Project`), not the license text. The default filename is `LICENSE`.
- **Overwrite protection**: Interactive mode asks before replacing a file. Quick mode requires `--force` to overwrite one.

## Installation

### Linux

Download the package for your distribution from [GitHub Releases](https://github.com/FreetimeMaker/License-Generator/releases). The package manager installs Python and PyQt6 as runtime dependencies.

#### Debian / Ubuntu (APT)

Download the `.deb` file or use the APT Repository:

```bash
sudo cd /etc/apt/keyrings
curl -fSLo freetime-repository.gpg https://repo.free-time.me/public.gpg
gpg --show-keys --with-fingerprint freetime-repository.gpg
```

after that do:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
sudo install -m 0644 freetime-repository.gpg /etc/apt/keyrings/freetime-repository.gpg
printf '%s\n' 'deb [arch=amd64 signed-by=/etc/apt/keyrings/freetime-repository.gpg] https://repo.free-time.me/apt/ stable main' | sudo tee /etc/apt/sources.list.d/freetime-repository.list
sudo apt update
```

then run:

```bash
sudo apt install license-gen
```

#### Fedora / Red Hat (RPM)

Download the `.rpm` file or use the YUM Repository:

```bash
curl -fSLo freetime-repository.asc https://repo.free-time.me/yum/x86_64/public.asc
gpg --show-keys --with-fingerprint freetime-repository.asc
```

then do:

```bash
sudo nano /etc/yum.repos.d/freetime-repository.repo
```

then add:

```text
[freetime-repository]
name=Freetime Repository
baseurl=https://repo.free-time.me/yum/x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://repo.free-time.me/yum/x86_64/public.asc

```

then run:

```bash
sudo dnf --refresh makecache
sudo dnf install license-gen
```

Open **License Generator** from the application menu or run `license-gen --gui`. For the interactive terminal menu, run `generate-license`.

To remove a packaged installation, run `sudo apt remove license-gen` or `sudo dnf remove license-gen`.

## Running from Source

Run these commands from the repository root with Python 3.9 or newer:

```sh
python3 license_gen.py          # Terminal menu
python3 license_gen.py --gui    # Desktop app; requires PyQt6
```

Install PyQt6 separately for the desktop app, for example with `sudo apt install python3-pyqt6` on Debian or Ubuntu, or `sudo dnf install python3-pyqt6` on Fedora.

## Makefile Commands

### Install and Uninstall

```sh
sudo make install
sudo make uninstall
```

Direct installation uses `/usr/local` by default and expects the runtime dependencies to be installed separately. To install without `sudo`, run `make install PREFIX="$HOME/.local"` and make sure `$HOME/.local/bin` is on your `PATH`. Use the same `PREFIX` to uninstall. Both targets honor `DESTDIR`; uninstalling leaves user settings intact.

### Build Packages

```sh
make deb    # Debian / Ubuntu
make rpm    # Fedora
```

`make` must already be installed. If the selected packaging tool is missing, the build installs `dpkg` via `apt-get` or `rpm-build` via `dnf`. This requires access to the package repositories and uses `sudo` when not running as root. Pass `AUTO_INSTALL_DEPS=0` to use only preinstalled tools.

Packages appear in the repository root; intermediate files go into `build/`. If Debian packaging fails on a Windows-mounted filesystem under WSL, try `make deb DEB_WORK=/tmp` to stage the files on the Linux filesystem.

## Command Line Options

| Command                               | What it does                           |
| ------------------------------------- | -------------------------------------- |
| `generate-license`                    | Opens the interactive terminal menu.   |
| `generate-license --ls`               | Lists available license identifiers.   |
| `generate-license --info MIT`         | Shows the original license text.       |
| `generate-license --sl MIT`           | Saves the default license.             |
| `generate-license --sa 'Ada Example'` | Saves the default author.              |
| `generate-license --sc`               | Shows saved defaults.                  |
| `generate-license --rc`               | Clears saved defaults.                 |
| `generate-license -q`                 | Generates a license without prompting. |
| `license-gen --gui`                   | Opens the desktop app.                 |

Generate a BSD-3-Clause license with explicit copyright details:

```sh
generate-license -q --license BSD-3-Clause --holder 'Ada Example' \
  --year 2024-2026 --project 'My Project'
```

Use `-o LICENSE` to override the project-specific filename. Use `generate-license --help` for all options.

## Contribute

### Support the Project

If you find this tool useful, you can support development via [Open Collective](https://opencollective.com/freetimemaker) or the [donation page](https://donation.free-time.me/).

### Development

Run the tests from the repository root with `make test` or `python3 -m unittest -v`. Bug reports and pull requests are welcome on [GitHub](https://github.com/FreetimeMaker/License-Generator). See the [changelog](CHANGELOG.md) for release notes.

To publish a release, update the version in the `Makefile`, build both packages, and attach the tested artifacts to the GitHub release.

## License

The generator is licensed under [GPL-3.0-only](LICENSE). Bundled templates retain their own terms. The 174 newer templates come from SPDX v3.29.0; the original 13 use SPDX v3.26.0 texts except for GPL-3.0-only, which uses this repository's `LICENSE`.

Before publishing a generated license, check for placeholders and any required copyright notices, source headers, or `NOTICE` files. The generator only substitutes copyright details for MIT, BSD-2-Clause, and BSD-3-Clause.
