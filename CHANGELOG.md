# Changelog

All notable changes to License Generator are documented here.

The project follows semantic versioning.

## Unreleased

No unreleased changes yet.

## 1.2.0 - 2026-11-27

### Added

- Combine multiple licenses in one editable document. In the GUI, append templates to the existing text; in the CLI, repeat `--license` or enter a comma-separated selection, and use `--edit` to open the draft in your editor.
- Added a PNG app icon for the GUI window and Linux application menu.
- Added `make install` and `make uninstall` for direct installation from source. Debian and RPM builds can install missing packaging tools automatically.

### Changed

- The CLI and GUI fetch selected license texts from the SPDX API first and fall back to bundled templates if no valid online text is available.
- Interactive CLI generation asks for the project name and author. The CLI and GUI default the copyright year to the first Git commit's author year, or the current year if there is no commit.
- The GUI shows the destination before saving. Inside a Git working tree, it always targets `LICENSE` at the repository root; elsewhere, the project name suggests an editable filename.

## 1.1.0 - 2026-11-25

### Added

- Expanded the offline catalog from 13 to 187 templates in the CLI and GUI, covering all non-deprecated SPDX v3.29.0 entries marked OSI-approved or FSF-libre.
- Added `gfdl-1.3` and `lgpl-3.0` as aliases for the corresponding `-only` variants, completing coverage of the license template identifiers offered by GitHub's Choose a License catalog and GitLab.com.

## 1.0.0 - 2026-11-24

Initial Release
