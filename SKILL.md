---
name: ieee-journal-single-to-double
description: Convert IEEEtran journal manuscripts from one-column or draftclsnofoot format into clean two-column IEEE journal/Transactions submissions, especially for JBHI-style initial submissions. Use when working on IEEE LaTeX papers, changing \documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran} to \documentclass[journal,twocolumn]{IEEEtran}, fixing wide figures/tables, replacing conference-style author blocks, removing biographies for initial submission, and validating final PDF layout.
---

# IEEE Journal Single-to-Double Conversion

Use this skill to convert an IEEEtran one-column draft into a two-column journal manuscript without breaking floats, author metadata, references, or the final PDF layout.

## Workflow

1. Inspect the source:
   - Find `\documentclass`, `\maketitle`, `\author`, bibliography style, all `figure/table` environments, and any `IEEEbiography` blocks.
   - Compare with any existing double-column version if provided.
   - Preserve user edits and do not rewrite scientific content unless requested.

2. Convert the document class:
   - One-column draft:
     ```latex
     \documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran}
     ```
   - Two-column journal:
     ```latex
     \documentclass[journal,twocolumn]{IEEEtran}
     ```

3. Add two-column float support only when needed:
   ```latex
   \usepackage{stfloats}
   \usepackage{tabularx}
   ```
   Keep `float` only if the manuscript still needs `[H]` for narrow, intentionally pinned items. Do not use `[H]` for normal two-column journal floats.

4. Fix the author area:
   - For IEEE journal/Transactions mode, prefer `\author{... \thanks{...}}`.
   - Do not use `\IEEEauthorblockN` or `\IEEEauthorblockA`; those are conference-style blocks and commonly collapse affiliations in journal mode.
   - Put affiliations, funding, and corresponding author information in `\thanks{}` first-footnote text.

5. Convert floats by width:
   - Full-width architecture figures, large qualitative grids, and large multi-metric tables: use `figure*` or `table*` and size to `\textwidth`.
   - Single-column plots and compact tables: use `figure` or `table` and size to `\columnwidth`.
   - Replace `\makebox[\textwidth][c]{\includegraphics[width=1.25\textwidth]{...}}` with a proper `figure*` unless the target journal explicitly allows overwide one-column draft figures.

6. Remove final-submission-only material for initial submission:
   - Delete or comment out `IEEEbiography`, `IEEEbiographynophoto`, photo placeholders, and "PLACE PHOTO HERE" content.
   - Ensure `\end{thebibliography}` or `\bibliography{...}` is followed directly by `\end{document}`.

7. Compile and verify:
   - Run `latexmk -pdf -g -interaction=nonstopmode -halt-on-error <main.tex>`.
   - Check the log for `LaTeX Error`, undefined citations/references, `Float too large`, and `Overfull \vbox`.
   - Render or inspect the PDF. Confirm title page, wide floats, table legibility, and final references page.

## Decision Rules

- Do not blindly turn every `figure` into `figure*`. Wide floats consume full-width slots and may drift several pages.
- Do not keep `[H]` from the one-column draft unless there is a specific layout reason. In two-column IEEEtran, `[t]`, `[b]`, `[p]`, `[htbp]`, and `figure*`/`table*` usually behave better.
- Use `\columnwidth` for one-column figures, not `\textwidth`.
- Use `\textwidth` inside `figure*`/`table*`.
- Keep captions concise; long captions can push wide floats to later pages.
- For initial submissions, prioritize clean structure over final-publication extras such as biographies and author photos.

## Detailed Patterns

When converting a real manuscript, read `references/ieee-conversion-patterns.md` for before/after snippets, float conversion patterns, and the final QA checklist.

When a user asks for standards, citations, or rationale, read `references/official-sources.md` and ground the answer in IEEE/CTAN sources.

## Optional Audit Script

Run the bundled PowerShell audit from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File path\to\ieee-journal-single-to-double\scripts\audit_ieee_twocolumn.ps1 -TexFile Paper_Final_EN_Double.tex
```

The script checks common structural mistakes: wrong class options, conference author blocks, lingering biographies, overwide one-column graphics, and missing `\maketitle`.
