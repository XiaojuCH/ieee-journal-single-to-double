# ieee-journal-single-to-double

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/XiaojuCH/ieee-journal-single-to-double?style=social)](https://github.com/XiaojuCH/ieee-journal-single-to-double/stargazers)
[![Compile examples](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml/badge.svg)](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml)

**English** | **[中文说明](README_ZH.md)**

Converting an IEEEtran draft from `onecolumn` to `twocolumn` is supposed to be a one-line change. It never is. Conference-style author blocks silently break in journal mode, `[H]`-pinned floats overflow columns, `\textwidth` figures are too wide for a single column, and biographies don't belong in initial submissions. Each trap takes a while to find. This repo is the guide I wish had existed before I spent that time.

## ⚡ Using an AI assistant?

Paste this into Codex, Kiro, Cursor, or similar — it will clone the repo, read the workflow, and start converting your manuscript:

```
Use the skill at https://github.com/XiaojuCH/ieee-journal-single-to-double — clone it, read SKILL.md, then help me convert my IEEEtran draft from onecolumn to twocolumn journal format. Start by running the audit script on my .tex file or ask me for the path.
```

## Before and after

### Page 1 — author block

| Draft | Submission |
|:---:|:---:|
| ![before p1](assets/before-page1.png) | ![after p1](assets/after-page1.png) |
| Conference-style `\IEEEauthorblockN/A` | Journal `\author{...\thanks{...}}` footnotes |

### Page 2 — float placement

| Draft | Submission |
|:---:|:---:|
| ![before p2](assets/before-page2.png) | ![after p2](assets/after-page2.png) |
| `figure[H]` + `\textwidth` fills one column | `figure*[t!]` spans both; `figure` + `\columnwidth` stays in one |

## What changes

| Draft | Submission |
| --- | --- |
| `\documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran}` | `\documentclass[journal,twocolumn]{IEEEtran}` |
| `\IEEEauthorblockN` / `\IEEEauthorblockA` | `\author{...\thanks{...}}` with footnote affiliations |
| `\begin{figure}[H]` with `width=\textwidth` | `figure` + `\columnwidth`, or `figure*` + `\textwidth` for wide |
| `\begin{table}[H]` and stretched tables | Floating `table` / `table*` with `adjustbox` |
| Biographies after references | Remove for initial submission |

## Usage

Run the audit script on your `.tex` file first:

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File scripts\audit_ieee_twocolumn.ps1 -TexFile path\to\paper.tex
```

```bash
# Linux / macOS
bash scripts/audit_ieee_twocolumn.sh path/to/paper.tex
```

Fix what it flags. Compile. Inspect the PDF for wide floats and the references page. Submit.

## Files

```
SKILL.md                                  AI assistant skill (Codex, Kiro, etc.)
examples/before/minimal.tex              Draft with all the common traps
examples/after/minimal.tex               What the submission should look like
references/ieee-conversion-patterns.md   All patterns with before/after code
references/official-sources.md           IEEE style manual, IEEEtran CTAN, sttools
scripts/audit_ieee_twocolumn.ps1         Audit script (Windows)
scripts/audit_ieee_twocolumn.sh          Audit script (Linux/macOS)
```

---

If this saved you some time, a star helps others find it.
