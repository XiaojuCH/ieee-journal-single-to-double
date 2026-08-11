---
name: ieee-paper-doctor
description: Convert, audit, and verify single-file or multi-file IEEEtran LaTeX projects for safe two-column journal submission. Use for IEEE single-column to double-column conversion, 单栏转双栏, IEEE 双栏排版, multi-file papers using input/include/subfile, draftclsnofoot cleanup, figure or table overflow, figure*/table* placement, journal author blocks, bibliography float problems, camera-ready formatting, CI annotations, audit reports, and final PDF layout checks. Do not use for Word, ACM, Springer, or non-IEEEtran templates.
---

# IEEE Paper Doctor

Convert an IEEEtran project without rewriting scientific content. Produce a reviewable source diff, compile evidence, and a concise list of remaining risks.

## Workflow

1. Establish the target before editing.
   - Identify the target journal and whether this is an initial, revision, or final submission.
   - Read journal-specific instructions when provided. Do not assume every IEEE journal wants the same author, biography, anonymity, or float treatment.

2. Inspect the project.
   - Pass a project directory when possible; the CLI locates the unique IEEEtran main file and follows `\input`, `\include`, and `\subfile` recursively.
   - If multiple main files exist, identify the intended one explicitly instead of guessing.
   - Find bibliography mode, figures, tables, algorithms, wide equations, author metadata, and biography blocks across included files.
   - Preserve user changes. Never rewrite claims, equations, captions, citations, or results unless requested.

3. Run the bundled checker from the directory containing this `SKILL.md`:

   ```bash
   python scripts/ieee_paper_doctor.py check path/to/project --format json
   ```

   Use `--strict` when warnings must fail CI. Read the JSON diagnostics before editing. Use `--format github` in GitHub Actions and `--report audit.md` when the author needs a shareable review artifact.

4. Generate conservative fixes as a diff:

   ```bash
   python scripts/ieee_paper_doctor.py fix path/to/main.tex
   ```

   With no output flag, `fix` prints a unified diff and changes nothing. Use `--output converted.tex` for a new file or `--write` only after reviewing the diff. The deterministic fixer only normalizes safe class options and obvious single-column width expressions.
   After the transformation preview, read the full project diagnostics; a clean main-file diff does not clear unresolved findings in included sources.

5. Apply judgment-based fixes manually.
   - Choose `figure` versus `figure*` and `table` versus `table*` from content readability, not width alone.
   - Convert conference-style author blocks only after mapping every author to the correct affiliation and corresponding-author note.
   - Remove biographies only when the target submission stage or journal instructions require it.
   - Add `stfloats`, `placeins`, `\FloatBarrier`, float-fraction tuning, or `\IEEEtriggeratref` only when compilation or the rendered PDF demonstrates that need.
   - Read [references/ieee-conversion-patterns.md](references/ieee-conversion-patterns.md) for detailed patterns.

6. Verify:

   ```bash
   python scripts/ieee_paper_doctor.py verify path/to/project --compile --strict --report ieee-audit.md
   ```

   Inspect the rendered PDF when a renderer is available. Check the title block, float readability, column overflow, equations, bibliography start, and final page. When standards or rationale are requested, read [references/official-sources.md](references/official-sources.md).

## Safety Rules

- Default to a diff or a new output file; do not overwrite the only manuscript copy.
- Preserve journal-specific class options unless they conflict with the requested conversion.
- Treat `[H]`, wide floats, author blocks, and biographies as review items rather than blind replacements.
- Treat missing or dynamic include targets as unresolved project risks; do not silently skip them.
- Do not add packages speculatively. Compile after each structural group of edits.
- Stop and report when the source is not IEEEtran or when the target format is ambiguous.

## Completion Report

Return:

- files changed;
- deterministic fixes applied;
- judgment-based fixes applied;
- compile command and result;
- number of TeX files scanned and the audit report path, when generated;
- unresolved warnings and any journal-specific decision still required.
