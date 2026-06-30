# IEEEtran One-Column to Two-Column Patterns

For source-backed rationale, see official-sources.md. This file focuses on practical conversion patterns.

## 1. Preamble

Before:

```latex
\documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran}
\usepackage{float}
```

After:

```latex
\documentclass[journal,twocolumn]{IEEEtran}
\usepackage{stfloats}   % figure*/table* at page bottom; load before adjustbox
\usepackage{adjustbox}  % wide tables: \begin{adjustbox}{max width=\textwidth}
\usepackage{placeins}   % provides \FloatBarrier; do NOT use [section] option —
                        % that forces floats out at every section break and
                        % creates whitespace gaps that hurt page density

% High-density float fractions: allow up to 90% of a page to be floats.
% Tune down to 0.8/0.7 if the journal reviewer complains about float-heavy pages.
\renewcommand{\topfraction}{0.9}
\renewcommand{\dbltopfraction}{0.9}
\renewcommand{\floatpagefraction}{0.8}
\renewcommand{\dblfloatpagefraction}{0.8}
```

Do not keep `\usepackage{float}` unless specific `[H]` overrides are still needed. In two-column IEEEtran, `[H]` breaks multi-column flow and is almost never the right choice.

## 2. Author Block

Bad for IEEE journal mode:

```latex
\author{
  \IEEEauthorblockN{A\textsuperscript{1}, B\textsuperscript{2}}
  \IEEEauthorblockA{\textsuperscript{1}Affiliation\\
  \textsuperscript{2}Affiliation}
}
```

Preferred journal mode:

```latex
\author{First~Author,
        Second~Author,
        and~Last~Author%
\thanks{This work was supported by ... (Corresponding author: Last Author.)}%
\thanks{First Author and Last Author are with ... (e-mail: ...).}%
\thanks{Second Author is with ... .}}
```

Rules:

- Use nonbreaking spaces inside names, for example `First~Author`.
- Put `%` after the final author name and each `\thanks{...}` line to avoid unwanted spaces.
- Do not use `\hfill` inside author footnotes; it can push email text to the page edge.

## 3. Figure Conversion

One-column draft pattern:

```latex
\begin{figure}[H]
\centering
\makebox[\textwidth][c]{\includegraphics[width=1.25\textwidth]{fig.pdf}}
\caption{...}
\label{fig:arch}
\end{figure}
```

Two-column full-width pattern:

```latex
\begin{figure*}[t!]
\centering
\includegraphics[width=\textwidth]{fig.pdf}
\caption{...}
\label{fig:arch}
\end{figure*}
```

Two-column single-column pattern:

```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=\columnwidth]{fig.pdf}
\caption{...}
\label{fig:compact}
\end{figure}
```

Use `figure*` for architecture diagrams, qualitative comparison grids, wide scatter panels, and figures whose labels become unreadable at `\columnwidth`.

## 4. Table Conversion

One-column overwide draft pattern:

```latex
\begin{table}[H]
\makebox[\textwidth][c]{%
\begin{adjustbox}{max width=1.15\textwidth}
...
\end{adjustbox}}
\end{table}
```

Two-column full-width pattern:

```latex
\begin{table*}[t!]
\centering
\begin{adjustbox}{max width=\textwidth}
\begin{threeparttable}
...
\end{threeparttable}
\end{adjustbox}
\end{table*}
```

For compact tables:

```latex
\begin{table}[htbp]
\centering
\small
\setlength{\tabcolsep}{3pt}
...
\end{table}
```

Rules:

- Keep `threeparttable` inside `adjustbox` when footnotes belong to the table.
- Use `\footnotesize`, `\scriptsize`, and `\tabcolsep` before reducing scientific content.
- If a table is still unreadable in one column, promote it to `table*`.

## 5. Float Placement

Common conversion choices:

| One-column draft | Two-column journal |
| --- | --- |
| `[H]` architecture figure | `figure* [t!]` |
| `[H]` wide results table | `table* [t!]` |
| `[H]` compact metric table | `table [htbp]` or `table [b!]` |
| `width=\textwidth` in `figure` | `width=\columnwidth` |
| `width=1.25\textwidth` | `figure*` with `width=\textwidth` |

Avoid using many consecutive `figure*`/`table*` floats. Wide floats can only appear at top/bottom float slots and may move away from their first citation.

**Placement specifiers and density:**

- `[t!]` — page top only, ignores `\topfraction` cap. Best for density: LaTeX packs text below the float on the same page.
- `[htbp]` — flexible, good default for single-column floats.
- `[tbp]` — allows dedicated float pages. Use when a float keeps drifting past important text, at the cost of some page density.
- Never use `[section]{placeins}` — it inserts automatic barriers at every `\section` call, which forces early float output and leaves whitespace gaps.

## 6. Bibliography and Column Balance

**Preventing floats from interrupting the reference list:**

Any `figure*` or `table*` still in LaTeX's float queue when the bibliography starts will be inserted at the top of bibliography pages. Fix with a single `\FloatBarrier` right before `\begin{thebibliography}`:

```latex
% Flush all pending wide floats before references start.
% Use \FloatBarrier from the placeins package (loaded without [section]).
\FloatBarrier
\begin{thebibliography}{15}
...
\end{thebibliography}
```

**Balancing the two reference columns on the last page:**

IEEEtran provides `\IEEEtriggeratref{N}` to insert a column break before reference N. Place it just before `\begin{thebibliography}` and adjust N until both columns are roughly the same height:

```latex
\FloatBarrier
\IEEEtriggeratref{7}   % break before ref 7; adjust N to balance columns
\begin{thebibliography}{15}
...
\end{thebibliography}
```

A typical starting point for N is `ceil(total_refs / 2)`. If reference lengths are uneven, shift N by ±1 until the columns look balanced.

## 7. Initial Submission Cleanup
Remove before initial submission unless the journal explicitly asks for final-package material:

```latex
\begin{IEEEbiography}
...
\end{IEEEbiography}

\begin{IEEEbiographynophoto}
...
\end{IEEEbiographynophoto}
```

Final ending should look like:

```latex
\end{thebibliography}

\end{document}
```

or, for BibTeX:

```latex
\bibliographystyle{IEEEtran}
\bibliography{refs}

\end{document}
```

## 8. QA Checklist

Run after every conversion:

- `\documentclass` contains `journal,twocolumn`.
- `\maketitle` exists after `\title` and `\author`.
- No `\IEEEauthorblockN` or `\IEEEauthorblockA` remains in journal mode.
- No `IEEEbiography`, author photos, or photo placeholders remain for initial submission.
- No `\includegraphics[width=\textwidth]` remains inside a single-column `figure`.
- No `\includegraphics[width=1.2\textwidth]` or similar overwide draft hack remains.
- References close cleanly before `\end{document}`.
- `\FloatBarrier` (from `placeins`, loaded without `[section]`) placed immediately before `\begin{thebibliography}` or `\bibliography`.
- `\IEEEtriggeratref{N}` placed before `\begin{thebibliography}` to balance the two reference columns; N ≈ half the total reference count.
- Compile log has no fatal errors, undefined refs/cites, `Float too large`, or `Overfull \vbox`.
- PDF title page, wide floats, table legibility, and final references page are visually inspected.
- Final references page has no figures or tables interrupting the reference list.

## 9. Common Log Interpretation

- `Underfull \vbox`: often harmless in figure-heavy two-column papers; inspect the rendered page.
- `Underfull \hbox` in references: usually acceptable unless the reference line is visibly ugly.
- `Font shape ... scit undefined`: common with Times small-caps italic substitutions; usually not a blocking issue.
- `Float too large for page`: fix immediately by reducing figure/table height, shortening caption, changing placement, or regenerating the figure.
- `Overfull \vbox`: treat as a layout defect; something is running past the page.
