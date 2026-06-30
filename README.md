# IEEE Journal Single-to-Double

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/XiaojuCH/ieee-journal-single-to-double?style=social)](https://github.com/XiaojuCH/ieee-journal-single-to-double/stargazers)
[![Compile examples](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml/badge.svg)](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml)

**English** | **[中文说明](README_ZH.md)**

> The missing guide to converting IEEE one-column drafts to two-column journal submissions.

IEEEtran one-column drafts are comfortable to write, but they hide layout rules that decide whether a journal submission looks professional. The conversion becomes painful when conference-style author blocks, pinned `[H]` floats, overwide `\textwidth` figures, and final-submission biographies collide with two-column IEEE output. This repository packages the practical rules, source-backed references, working examples, and an audit script so you can convert without rediscovering every trap by hand.

## 📸 Before vs After

| One-column draft | Two-column journal |
|:---:|:---:|
| ![before](assets/before-page1.png) | ![after](assets/after-page1.png) |
| `draftclsnofoot,onecolumn` | `journal,twocolumn` |

## 🔄 Common Conversion Patterns

| One-column draft problem | Two-column journal fix |
| --- | --- |
| `\documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran}` | `\documentclass[journal,twocolumn]{IEEEtran}` |
| `\IEEEauthorblockN` / `\IEEEauthorblockA` in journal mode | `\author{...\thanks{...}}` with affiliations in footnotes |
| `\begin{figure}[H]` with `\includegraphics[width=\textwidth]{...}` | `figure` + `\columnwidth` (single-col) or `figure*` + `\textwidth` (full-width) |
| `\begin{table}[H]` and manually stretched tables | Floating `table` / `table*` with `adjustbox` or font-size tuning |
| Author biographies and photos after references | End cleanly after `\end{thebibliography}` for initial submission |

## 🚀 Quick Start

1. **Copy** the skill into your Codex skills directory, or clone this repo for reference.
2. **Audit** your converted file:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\audit_ieee_twocolumn.ps1 -TexFile path\to\paper.tex
   ```
3. **Fix** flagged patterns, compile the PDF, visually inspect wide floats and the references page, then submit.

## 📂 Repository Layout

```text
.
├─ SKILL.md                               # Codex skill entry point
├─ agents\openai.yaml                     # Optional Codex UI metadata
├─ assets\
│  ├─ before-page1.png                    # One-column draft preview
│  └─ after-page1.png                     # Two-column journal preview
├─ examples\
│  ├─ README.md                           # What the examples demonstrate
│  ├─ before\minimal.tex                  # Draft with common conversion traps
│  └─ after\minimal.tex                   # Corrected two-column version
├─ references\
│  ├─ ieee-conversion-patterns.md         # Practical before/after rules
│  └─ official-sources.md                 # IEEE/CTAN authoritative sources
└─ scripts\
   └─ audit_ieee_twocolumn.ps1            # Structural audit script
```

## 📖 Resources

| Resource | Description |
|---|---|
| [SKILL.md](SKILL.md) | Codex skill — invoke directly in your manuscript session |
| [references/ieee-conversion-patterns.md](references/ieee-conversion-patterns.md) | All practical patterns with before/after code blocks |
| [references/official-sources.md](references/official-sources.md) | IEEE Editorial Style Manual, IEEEtran on CTAN, sttools |
| [examples/before/minimal.tex](examples/before/minimal.tex) | Minimal compilable draft example |
| [examples/after/minimal.tex](examples/after/minimal.tex) | Corrected journal submission version |

## Why This Exists

Most IEEE manuscripts start as one-column drafts because they are easier to read during review. The gap between a draft and a valid two-column journal submission is small in concept but surprisingly tricky in practice: float placement, author-footnote conventions, and journal-mode IEEEtran behavior are poorly documented for the conversion path specifically. This project is an opinionated guide for exactly that gap.

---

⭐ If this saved you an hour of debugging, a star helps others find it.
