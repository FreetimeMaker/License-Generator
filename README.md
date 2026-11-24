# License Generator

An interactive open-source license generator for Linux, inspired by [anth0nycodes/license-generator](https://github.com/anth0nycodes/license-generator). It is written in Python and includes a PyQt6 desktop interface. Both the CLI and GUI work offline and share the same templates and settings.

## Installation

Download the package for your distribution from GitHub Releases and install it with your package manager:

```sh
# Debian or Ubuntu
sudo apt install ./license-gen_*_all.deb

# Fedora
sudo dnf install ./license-gen-*.noarch.rpm
```

The packages install PyQt6 as a dependency. To run from source, use `python3 license_gen.py` (Python 3.9 or later). To open the GUI, install PyQt6 and run `python3 license_gen.py --gui`.

## Usage

```sh
generate-license                     # Open the interactive menu
generate-license --ls                # List license identifiers
generate-license -i mit              # Show the original license text
generate-license --sl mit            # Save the default license
generate-license --sa 'Ada Example'  # Save the default author
generate-license -q                  # Generate LICENSE without prompting
generate-license -q --license bsd-3-clause --year 2024-2026 --project 'My Project'
generate-license --sc                # Show saved defaults
generate-license --rc                # Clear saved defaults
license-gen --gui                     # Or select License Generator from the application menu
```

For MIT and BSD licenses, the app suggests the saved author or the name from `git config user.name`. The year defaults to the current year. Quick mode only overwrites existing files with `--force`. The GUI lets you preview, copy, and save licenses, and set defaults shared by both interfaces. Settings are stored in `~/.config/license-gen/config.json` or in `license-gen/config.json` under `$XDG_CONFIG_HOME`.

Enter an optional project name in the interactive menu, with `--project`, or in the GUI. It changes only the suggested filename (for example, `LICENSE-My-Project`), not the license text. Without a project name, the filename defaults to `LICENSE`. Use `-o LICENSE` to keep that filename even when a project name is provided.

The 13 templates match the reference app's license selection. They are bundled from the [SPDX License List v3.26.0](https://github.com/spdx/license-list-data/tree/v3.26.0/text), except for GPL-3.0, which comes from this repository's `LICENSE`. The app fills in copyright details for MIT and BSD. Other templates, including their examples and appendices, are used unchanged. Check whether your project needs separate source file headers, copyright statements, or `NOTICE` files.

## Building and publishing packages

- Debian or Ubuntu: run `sudo apt install make dpkg-dev`, then `make deb`.
- Fedora: run `sudo dnf install make rpm-build`, then `make rpm`.
- Tests: run `python3 -m unittest -v`.

The finished `.deb` and `.rpm` packages land in the project root next to the `Makefile`. Build intermediates go into `build/` by default, not your home directory. If `dpkg-deb` reports incorrect permissions when building on a Windows drive under WSL, run `make deb DEB_WORK=/tmp` to stage the files on the Linux filesystem. The finished package still lands in the project root.

To publish a release, update the version in the `Makefile`, build both packages locally, and manually attach the tested packages to the GitHub release.
