# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project uses semantic versioning for public releases.

## [1.2.0] - 2026-08-11

### Added

- Project-directory input with automatic IEEEtran main-file discovery.
- Recursive, cycle-safe scanning for `\input`, `\include`, and `\subfile` sources.
- Source file and line attribution for diagnostics across multi-file papers.
- Project-root and current-file-relative include resolution with cycle protection.
- Static detection of undefined `\ref` targets across included source files.
- GitHub Actions annotation output through `--format github`.
- Shareable Markdown audit reports through `--report`.
- Horizontal overflow detection from `Overfull \hbox` compiler warnings.
- Missing reference keys in compiler diagnostics for faster remediation.
- The first actionable compiler error in JSON and Markdown output when `latexmk` fails.
- A clean multi-file example project and project-level regression tests.

### Changed

- `check` and `verify` now accept either a main TeX file or a project directory.
- JSON output preserves the legacy `file` field and adds the discovered main file, tool version, and complete scanned-file list.
- Skill guidance now begins with project-wide discovery instead of main-file-only checks.
- `fix` now rechecks all discovered sources after transforming the main file, so included-file risks remain visible.

## [1.1.0] - 2026-08-11

### Added

- Installable `ieee-paper-doctor` Codex plugin and nested skill structure.
- Dependency-free Python CLI with `check`, safe `fix`, `verify`, JSON output, strict CI mode, reviewable diffs, and optional `latexmk` compilation.
- Unit tests for option-order handling, inline comments, fixture diagnostics, safe transformations, idempotence, and non-writing defaults.
- Python package metadata and the `ieee-paper-doctor` console command.

### Changed

- Repositioned the project from a static conversion guide to a conservative conversion and verification tool.
- Rewrote English and Chinese onboarding around one-command checks and Codex installation.
- Updated the skill to ask for the target journal and submission stage before judgment-based edits.
- Expanded CI to test the CLI before compiling the LaTeX fixtures.

### Removed

- Duplicated PowerShell and Bash auditors, replaced by one cross-platform implementation.

## [1.0.0] - 2026-06-30

### Added

- Root README with project pitch, badges, pain points, before/after table, quick start workflow, file tree, and links to the skill and references.
- Chinese README (`README_ZH.md`) for bilingual project onboarding.
- Minimal before/after IEEEtran examples showing one-column draft problems and corrected two-column journal patterns.
- Screenshot comparison assets for before/after rendered pages.
- GitHub Actions CI for compiling the LaTeX examples on push and pull requests.
- Lightweight contributing guide for new conversion patterns.
- Official-source and conversion-pattern references for IEEE journal single-to-double conversion.
- PowerShell and bash audit scripts for checking common IEEE two-column submission issues.
