# IEEE Paper Doctor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/XiaojuCH/ieee-journal-single-to-double?style=social)](https://github.com/XiaojuCH/ieee-journal-single-to-double/stargazers)
[![Test IEEE Paper Doctor](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml/badge.svg)](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml)

**English** | **[中文说明](README_ZH.md)**

Safely convert an IEEEtran one-column draft into a two-column journal manuscript—with project-wide checks, a reviewable diff, and compile evidence. Scientific content stays untouched.

Changing `onecolumn` to `twocolumn` is one line. Fixing the author block, wide figures, pinned tables, float queues, and bibliography page is not. IEEE Paper Doctor combines a Codex skill with a dependency-free CLI so the mechanical changes are reproducible and the judgment calls stay reviewable.

## Start in 30 seconds

Install the CLI directly from GitHub:

```bash
pipx install git+https://github.com/XiaojuCH/ieee-journal-single-to-double.git
```

Audit a single-file manuscript without changing it:

```bash
ieee-paper-doctor check path/to/main.tex --strict
```

For a multi-file project, pass its directory. The CLI discovers the IEEEtran main file and recursively follows `\input`, `\include`, and `\subfile`:

```bash
ieee-paper-doctor check path/to/project --strict
ieee-paper-doctor check path/to/project --report paper-audit.md
```

Preview conservative fixes as a unified diff:

```bash
ieee-paper-doctor fix path/to/main.tex
```

Write a separate converted source, then compile and verify it:

```bash
ieee-paper-doctor fix path/to/main.tex --output path/to/main.twocolumn.tex
ieee-paper-doctor verify path/to/main.twocolumn.tex --compile --strict
```

`fix` never overwrites the input unless you explicitly pass `--write`.

## Use as a Codex skill

Ask Codex to install the skill from this repository:

```text
$skill-installer Install ieee-paper-doctor from https://github.com/XiaojuCH/ieee-journal-single-to-double/tree/master/skills/ieee-paper-doctor
```

Then invoke it on a paper project:

```text
$ieee-paper-doctor Convert my IEEEtran draft to a two-column journal submission. Preserve scientific content, show me the diff, compile it, and report remaining layout risks.
```

The repository is also packaged as an installable Codex plugin through `.codex-plugin/plugin.json`.

## What it catches

- `draftcls`, `draftclsnofoot`, `onecolumn`, and conflicting class options in any order.
- Conference-style `\IEEEauthorblockN` / `\IEEEauthorblockA` in journal mode.
- `[H]` figures, tables, and algorithms that need placement review.
- `\textwidth` and overwide `1.x\textwidth` sizing inside one-column floats.
- Biographies and photo placeholders that may not belong in the current submission stage.
- Material left after the bibliography.
- Missing or dynamically generated included TeX files.
- Undefined `\ref` targets across scanned source files, before compilation.
- Compile failures, oversized floats, horizontal/vertical overflow, and undefined references.

Use `--format json` for machine-readable diagnostics, `--format github` for inline GitHub Actions annotations, and `--strict` to make warnings fail CI. `--report` writes a shareable Markdown audit with every scanned file and finding.

## Project-aware audit

Version 1.2 understands real multi-file papers instead of treating only `main.tex` as the manuscript. It automatically locates one IEEEtran root file in a directory, resolves includes from both the project root and the current source directory, scans sections once even when includes form a cycle, and attributes every finding to its source file and line. If a directory contains multiple possible roots, it stops and asks for the intended main file rather than guessing.

```bash
# Human-readable project audit
ieee-paper-doctor check ./paper --strict

# CI annotations on the exact source lines
ieee-paper-doctor check ./paper --strict --format github

# Compile the discovered root and save an audit artifact
ieee-paper-doctor verify ./paper --compile --report ieee-audit.md
```

## What it fixes automatically

The CLI deliberately limits automatic edits to transformations that are easy to review:

- normalize IEEEtran journal class options for explicit two-column output;
- replace obvious `\textwidth` sizing inside unstarred floats with `\columnwidth`;
- preserve all scientific prose, equations, captions, labels, citations, and results;
- produce an idempotent diff before any write.

Choosing `figure` versus `figure*`, rebuilding author affiliations, removing biographies, and adding float packages remain skill-guided decisions because they depend on the paper and target journal.

## Before and after

| One-column draft | Corrected two-column manuscript |
|:---:|:---:|
| ![One-column draft page](assets/before-page1.png) | ![Two-column result page](assets/after-page1.png) |
| ![Pinned draft float](assets/before-page2.png) | ![Corrected float layout](assets/after-page2.png) |

The complete examples live in [`examples/before`](examples/before), [`examples/after`](examples/after), and the multi-file [`examples/project`](examples/project).

## Scope and safety

IEEE Paper Doctor targets IEEEtran LaTeX journal manuscripts. It does not convert Word files or ACM, Springer, Elsevier, or arbitrary LaTeX templates.

Journal requirements override this tool. Before judgment-based edits, confirm the publication and whether the manuscript is an initial, revision, or final submission. The skill points to IEEE's Template Selector, LaTeX Analyzer, and PDF Checker for final validation.

## Development

```bash
python -m unittest discover -s tests -v
python skills/ieee-paper-doctor/scripts/ieee_paper_doctor.py check examples/project --strict
```

The GitHub workflow runs unit tests, smoke-tests the installed CLI, verifies both corrected fixtures, confirms that the bad fixture fails, and compiles the LaTeX examples.

Contributions are welcome—especially minimal reproducible IEEEtran failures and anonymized real-world conversion cases. See [CONTRIBUTING.md](CONTRIBUTING.md).

If IEEE Paper Doctor saves you a formatting round-trip, a star helps the next author find it.
