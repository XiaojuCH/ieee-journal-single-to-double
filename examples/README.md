# Examples: Before and After

These two files show the same paper skeleton converted from a typical
one-column IEEEtran draft to a clean two-column journal submission.

## What each file demonstrates

### `before/minimal.tex` — common one-column draft traps

| # | Pattern shown | Why it breaks in two-column |
|---|---|---|
| 1 | `\documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran}` | Wrong class options for journal submission |
| 2 | `\IEEEauthorblockN` / `\IEEEauthorblockA` + `\hfill` email | Conference-style blocks unsupported in journal mode |
| 3 | Wide overview `figure[H]` sized to `\textwidth` | `[H]` disables LaTeX placement; `\textwidth` overflows a column |
| 4 | Narrow detail `figure[H]` sized to `\textwidth` | Also unnecessarily oversized for a single-column figure |
| 5 | `table[H]` with four columns | Pinned float breaks two-column pagination |
| 6 | Wide ablation `table[H]` with seven columns | Overflows the column and collides with adjacent text |
| 7 | Wide results `figure[H]` (four-panel comparison) | Needs full page width; `[H]` prevents promotion to `figure*` |
| 8 | `\begin{IEEEbiography}` after references | Must be removed for initial submission to most IEEE journals |

### `after/minimal.tex` — corrected two-column patterns

| # | Fix applied | Rule |
|---|---|---|
| 1 | `\documentclass[journal,twocolumn]{IEEEtran}` | Minimal journal class options |
| 2 | `\author{...\thanks{...}}` footnote style | IEEE journal standard for affiliations |
| 3 | Wide overview → `figure*[t!]` + `\textwidth` | `figure*` spans both columns; floats to top/bottom |
| 4 | Narrow detail → `figure[htbp]` + `\columnwidth` | Single-column figure; sized to fit one column |
| 5 | `table[htbp]` (four columns) | Allow LaTeX to place naturally |
| 6 | Wide ablation → `table*[t!]` + `adjustbox{max width=\textwidth}` | Spans columns; `adjustbox` prevents overflow |
| 7 | Wide results → `figure*[t!]` + `\textwidth` | Same as fix 3 |
| 8 | Biography section removed | Clean ending after `\end{thebibliography}` |

## Compiling

Both files are self-contained (no external images) and compile with a
standard TeX Live or MiKTeX installation:

```bash
pdflatex examples/before/minimal.tex
pdflatex examples/after/minimal.tex
```

The CI workflow (`.github/workflows/compile.yml`) runs both on every push.
