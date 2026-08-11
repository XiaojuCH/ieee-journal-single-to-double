# Contributing

Contributions are welcome, especially minimal IEEEtran failures, anonymized real-world conversion cases, and conservative diagnostics that prevent a bad submission PDF.

## Before opening a pull request

1. Keep the scope to IEEEtran LaTeX journal formatting.
2. Add or update a focused test in `tests/` for every CLI behavior change.
3. Put reusable skill guidance in `skills/ieee-paper-doctor/SKILL.md` or its `references/` files; keep user-facing documentation at the repository root.
4. Do not add an automatic rewrite unless it is deterministic, reviewable, and idempotent.
5. Preserve scientific prose, equations, captions, citations, labels, and results in fixtures.

Run:

```bash
python -m unittest discover -s tests -v
python skills/ieee-paper-doctor/scripts/ieee_paper_doctor.py check examples/after/minimal.tex --strict
python skills/ieee-paper-doctor/scripts/ieee_paper_doctor.py check examples/before/minimal.tex --strict
```

The final command is expected to fail and list the intentionally planted problems.

If a change affects layout, compile both examples and include a focused before/after screenshot or a concise description of the rendered difference in the pull request.
