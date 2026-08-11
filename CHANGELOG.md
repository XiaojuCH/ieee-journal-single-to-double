# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project uses semantic versioning for public releases.

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
