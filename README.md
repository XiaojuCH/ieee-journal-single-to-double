# IEEE Journal Single-to-Double

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/XiaojuCH/ieee-journal-single-to-double?style=social)](https://github.com/XiaojuCH/ieee-journal-single-to-double/stargazers)
[![Compile examples](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml/badge.svg)](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml)

The missing guide to converting IEEE one-column drafts to two-column journal submissions.

IEEEtran one-column drafts are comfortable to write, but they hide the layout rules that decide whether a journal submission looks professional. The conversion becomes painful when conference-style author blocks, pinned `[H]` floats, overwide `\textwidth` figures, and final-submission biographies collide with two-column IEEE output. This repository packages the practical rules, source-backed references, examples, and an audit script so you can convert a draft without rediscovering every trap by hand.

## Before vs After

| Before: common one-column draft problem | After: two-column journal-safe pattern |
| --- | --- |
| `\documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran}` | `\documentclass[journal,twocolumn]{IEEEtran}` |
| `\IEEEauthorblockN` / `\IEEEauthorblockA` in journal mode | `\author{...\thanks{...}}` with affiliations and corresponding author in first-footnote text |
| `\begin{figure}[H]` with `\includegraphics[width=\textwidth]{...}` | Use `figure` + `width=\columnwidth` for one-column figures, or `figure*` + `width=\textwidth` for wide figures |
| `\begin{table}[H]` and manually stretched tables | Use floating `table` / `table*`, `adjustbox`, `\tabcolsep`, and font-size tuning |
| Author biographies and photo placeholders after references | For initial submission, end cleanly after references unless the journal asks otherwise |

## Quick Start

1. Copy this repository, or install `SKILL.md` and its resources into your Codex skills directory.
2. Run the audit script on your converted IEEEtran file:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\audit_ieee_twocolumn.ps1 -TexFile path\to\paper.tex
   ```
3. Fix any flagged conversion patterns, compile the PDF, visually inspect wide floats and the references page, then submit.

## Repository Layout

```text
.
├─ SKILL.md                              # Codex skill entry point
├─ agents\openai.yaml                    # Optional Codex UI metadata
├─ examples\README.md                    # Minimal before/after explanation
├─ examples\before\minimal.tex           # One-column draft with common conversion traps
├─ examples\after\minimal.tex            # Corrected two-column journal version
├─ references\ieee-conversion-patterns.md # Practical before/after conversion rules
├─ references\official-sources.md         # IEEE/CTAN source basis
└─ scripts\audit_ieee_twocolumn.ps1       # Lightweight structural audit script
```

## Start Here

- Use the Codex skill: [SKILL.md](SKILL.md)
- Read practical conversion patterns: [references/ieee-conversion-patterns.md](references/ieee-conversion-patterns.md)
- Check official source basis: [references/official-sources.md](references/official-sources.md)
- Compare minimal examples: [examples/before/minimal.tex](examples/before/minimal.tex) -> [examples/after/minimal.tex](examples/after/minimal.tex)

## Why This Exists

A lot of IEEE manuscripts begin as one-column review drafts because they are easier to read and revise. The hard part is that the final two-column journal version is governed by float placement, author-footnote conventions, and journal-mode IEEEtran behavior. This project is a small, opinionated conversion guide for that exact gap.

---

⭐ If this saved you an hour of debugging, a star helps others find it.
