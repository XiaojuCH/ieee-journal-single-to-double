# Official Source Basis

Use these sources when explaining why the conversion rules exist. Keep direct quotations short; paraphrase in normal answers.

## IEEE Editorial Style Manual for Authors

URL: https://journals.ieeeauthorcenter.ieee.org/wp-content/uploads/sites/7/IEEE-Editorial-Style-Manual-for-Authors.pdf

Practical implications:

- IEEE Transactions/Journals articles follow a title page sequence: title/byline/first footnote, abstract, index terms, body, conclusion, references, then photographs and biographies.
- The first footnote/author affiliation paragraph is unnumbered and contains manuscript/support/corresponding-author and affiliation information.
- The manual explicitly says not to use asterisks or daggers for the first footnote.
- Corresponding author information belongs in the first footnote wording.
- Photographs and biographies are commonly late/final article material. Verify the target journal and submission stage instead of deleting them unconditionally.

## IEEE Author Tools

URL: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/authoring-tools-and-templates/tools-for-ieee-authors/

Practical implications:

- Prefer the publication-specific template selected through IEEE's Template Selector.
- After local checks, use the IEEE LaTeX Analyzer and PDF Checker when available.
- Treat this skill as a conversion and preflight aid, not as a replacement for the target journal's current instructions.

## IEEEtran on CTAN

URL: https://ctan.org/pkg/ieeetran

Practical implications:

- `IEEEtran` is the standard LaTeX class for IEEE Transactions, journals, and conferences.
- Use the class options to choose journal/two-column behavior instead of manually forcing geometry.
- In journal mode, use the normal `\author{... \thanks{...}}` pattern for byline and first-footnote material.
- Conference-oriented commands such as `\IEEEauthorblockN` and `\IEEEauthorblockA` should not be used as the journal author layout.

## sttools / stfloats on CTAN

URL: https://ctan.org/pkg/sttools

Practical implications:

- `stfloats` is part of the `sttools` bundle and provides float-control support useful in two-column layouts.
- Use it only when the manuscript needs better handling of wide/bottom two-column floats.
- It complements, but does not replace, choosing correct `figure` versus `figure*` and `table` versus `table*` environments.

## Local IEEEtran Template Evidence

When TeX Live is installed, `bare_jrnl.tex` under the local IEEEtran documentation is a useful implementation reference. It demonstrates:

- `\author{...}` with nonbreaking spaces in names.
- Multiple `\thanks{...}` entries for affiliations and manuscript metadata.
- `%` after author/thanks lines to suppress unwanted spacing.

Do not cite a local file in public-facing documentation unless the repository includes it. Use it as an implementation check, not as the primary public source.
