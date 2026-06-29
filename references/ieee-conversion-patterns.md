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
\usepackage{float}
\usepackage{stfloats}
\usepackage{tabularx}

\renewcommand{\topfraction}{0.8}
\renewcommand{\bottomfraction}{0.6}
\renewcommand{\textfraction}{0.15}
\renewcommand{\floatpagefraction}{0.7}
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{5}
\emergencystretch=1em
```

Use the relaxed float settings only when the manuscript is figure/table heavy. They are conservative enough for most IEEE review drafts, but journal instructions override them.

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

## 6. Initial Submission Cleanup

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

## 7. QA Checklist

Run after every conversion:

- `\documentclass` contains `journal,twocolumn`.
- `\maketitle` exists after `\title` and `\author`.
- No `\IEEEauthorblockN` or `\IEEEauthorblockA` remains in journal mode.
- No `IEEEbiography`, author photos, or photo placeholders remain for initial submission.
- No `\includegraphics[width=\textwidth]` remains inside a single-column `figure`.
- No `\includegraphics[width=1.2\textwidth]` or similar overwide draft hack remains.
- References close cleanly before `\end{document}`.
- Compile log has no fatal errors, undefined refs/cites, `Float too large`, or `Overfull \vbox`.
- PDF title page, wide floats, table legibility, and final references page are visually inspected.

## 8. Common Log Interpretation

- `Underfull \vbox`: often harmless in figure-heavy two-column papers; inspect the rendered page.
- `Underfull \hbox` in references: usually acceptable unless the reference line is visibly ugly.
- `Font shape ... scit undefined`: common with Times small-caps italic substitutions; usually not a blocking issue.
- `Float too large for page`: fix immediately by reducing figure/table height, shortening caption, changing placement, or regenerating the figure.
- `Overfull \vbox`: treat as a layout defect; something is running past the page.
