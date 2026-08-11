---
name: ieee-paper-doctor
description: Convert, audit, and verify IEEEtran LaTeX manuscripts for safe two-column journal submission. Use for IEEE single-column to double-column conversion, 单栏转双栏, IEEE 双栏排版, draftclsnofoot cleanup, figure or table overflow, figure*/table* placement, journal author blocks, bibliography float problems, camera-ready formatting, and final PDF layout checks. Do not use for Word, ACM, Springer, or non-IEEEtran templates.
---

# IEEE Paper Doctor

Convert an IEEEtran project without rewriting scientific content. Produce a reviewable source diff, compile evidence, and a concise list of remaining risks.

## Workflow

1. Establish the target before editing.
   - Identify the target journal and whether this is an initial, revision, or final submission.
   - Read journal-specific instructions when provided. Do not assume every IEEE journal wants the same author, biography, anonymity, or float treatment.

2. Inspect the project.
   - Locate the main file through `\documentclass`, not by filename alone.
   - Find included files, bibliography mode, figures, tables, algorithms, wide equations, author metadata, and biography blocks.
   - Preserve user changes. Never rewrite claims, equations, captions, citations, or results unless requested.

3. Run the bundled checker from the directory containing this `SKILL.md`:

   ```bash
   python scripts/ieee_paper_doctor.py check path/to/main.tex --json
   ```

   Use `--strict` when warnings must fail CI. Read the JSON diagnostics before editing.

4. Generate conservative fixes as a diff:

   ```bash
   python scripts/ieee_paper_doctor.py fix path/to/main.tex
   ```

   With no output flag, `fix` prints a unified diff and changes nothing. Use `--output converted.tex` for a new file or `--write` only after reviewing the diff. The deterministic fixer only normalizes safe class options and obvious single-column width expressions.

5. Apply judgment-based fixes manually.
   - Choose `figure` versus `figure*` and `table` versus `table*` from content readability, not width alone.
   - Convert conference-style author blocks only after mapping every author to the correct affiliation and corresponding-author note.
   - Remove biographies only when the target submission stage or journal instructions require it.
   - Add `stfloats`, `placeins`, `\FloatBarrier`, float-fraction tuning, or `\IEEEtriggeratref` only when compilation or the rendered PDF demonstrates that need.
   - Read [references/ieee-conversion-patterns.md](references/ieee-conversion-patterns.md) for detailed patterns.

6. Verify:

   ```bash
   python scripts/ieee_paper_doctor.py verify path/to/main.tex --compile --strict
   ```

   Inspect the rendered PDF when a renderer is available. Check the title block, float readability, column overflow, equations, bibliography start, and final page. When standards or rationale are requested, read [references/official-sources.md](references/official-sources.md).

## Safety Rules

- Default to a diff or a new output file; do not overwrite the only manuscript copy.
- Preserve journal-specific class options unless they conflict with the requested conversion.
- Treat `[H]`, wide floats, author blocks, and biographies as review items rather than blind replacements.
- Do not add packages speculatively. Compile after each structural group of edits.
- Stop and report when the source is not IEEEtran or when the target format is ambiguous.

## Completion Report

Return:

- files changed;
- deterministic fixes applied;
- judgment-based fixes applied;
- compile command and result;
- unresolved warnings and any journal-specific decision still required.
