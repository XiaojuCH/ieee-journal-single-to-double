import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "ieee-paper-doctor" / "scripts" / "ieee_paper_doctor.py"
SPEC = importlib.util.spec_from_file_location("ieee_paper_doctor", SCRIPT)
assert SPEC and SPEC.loader
DOCTOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DOCTOR
SPEC.loader.exec_module(DOCTOR)


MINIMAL_BODY = r"""
\title{Example}
\author{A. Author}
\begin{document}
\maketitle
Scientific content must remain unchanged.
\end{document}
"""


class AnalyzeTests(unittest.TestCase):
    def test_release_versions_match(self):
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(DOCTOR.VERSION, manifest["version"])
        self.assertEqual(DOCTOR.VERSION, project["project"]["version"])

    def test_document_class_option_order_is_irrelevant(self):
        source = r"\documentclass[twocolumn,journal]{IEEEtran}" + MINIMAL_BODY
        codes = {item.code for item in DOCTOR.analyze(source)}
        self.assertNotIn("IPD001", codes)
        self.assertNotIn("IPD002", codes)
        self.assertNotIn("IPD003", codes)

    def test_document_class_allows_common_whitespace(self):
        source = (
            "\\documentclass  [journal,\n twocolumn] { IEEEtran }" + MINIMAL_BODY
        )
        codes = {item.code for item in DOCTOR.analyze(source)}
        self.assertFalse({"IPD001", "IPD002", "IPD003"} & codes)

    def test_inline_comments_do_not_trigger_false_positives(self):
        source = (
            r"\documentclass[journal,twocolumn]{IEEEtran}"
            + "\n"
            + r"\author{A. Author} % \IEEEauthorblockN{comment only}"
            + MINIMAL_BODY
        )
        codes = {item.code for item in DOCTOR.analyze(source)}
        self.assertNotIn("IPD101", codes)

    def test_before_example_exercises_expected_diagnostics(self):
        source, _ = DOCTOR.read_source(ROOT / "examples" / "before" / "minimal.tex")
        codes = {item.code for item in DOCTOR.analyze(source)}
        self.assertTrue({"IPD003", "IPD101", "IPD102", "IPD103", "IPD104"} <= codes)

    def test_after_example_is_clean(self):
        source, _ = DOCTOR.read_source(ROOT / "examples" / "after" / "minimal.tex")
        self.assertEqual([], DOCTOR.analyze(source))

    def test_project_discovery_follows_nested_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "sections" / "nested").mkdir(parents=True)
            (root / "main.tex").write_text(
                r"\documentclass[journal,twocolumn]{IEEEtran}"
                "\n"
                r"\title{Project}\author{A. Author}"
                "\n"
                r"\begin{document}\maketitle"
                "\n"
                r"\input{sections/results}"
                "\n"
                r"\end{document}",
                encoding="utf-8",
            )
            child = root / "sections" / "results.tex"
            child.write_text(
                r"\input{sections/nested/overflow}"
                "\n"
                r"% \input{commented-missing}",
                encoding="utf-8",
            )
            nested = root / "sections" / "nested" / "overflow.tex"
            nested.write_text(
                r"\begin{figure}\includegraphics[width=\textwidth]{result.pdf}\end{figure}"
                "\n"
                r"\input{../../main}",
                encoding="utf-8",
            )

            project = DOCTOR.resolve_project(str(root))
            diagnostics = DOCTOR.analyze_project(project)
            issue = next(item for item in diagnostics if item.code == "IPD104")

            self.assertEqual((root / "main.tex").resolve(), project.main)
            self.assertEqual(3, len(project.files))
            self.assertEqual(str(nested.resolve()), issue.file)
            self.assertNotIn("IPD001", {item.code for item in diagnostics})
            self.assertNotIn("IPD108", {item.code for item in diagnostics})

    def test_missing_input_is_reported_with_source_location(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main = Path(temp_dir) / "main.tex"
            main.write_text(
                r"\documentclass[journal,twocolumn]{IEEEtran}"
                + MINIMAL_BODY.replace(
                    r"Scientific content must remain unchanged.",
                    r"\input{sections/missing}",
                ),
                encoding="utf-8",
            )
            project = DOCTOR.resolve_project(str(main))
            issue = next(
                item
                for item in DOCTOR.analyze_project(project)
                if item.code == "IPD108"
            )
            self.assertEqual(str(main.resolve()), issue.file)
            self.assertIsNotNone(issue.line)

    def test_ambiguous_directory_requires_explicit_main_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in ("a.tex", "b.tex"):
                (root / name).write_text(
                    r"\documentclass[journal,twocolumn]{IEEEtran}" + MINIMAL_BODY,
                    encoding="utf-8",
                )
            with self.assertRaisesRegex(ValueError, "Multiple IEEEtran main files"):
                DOCTOR.resolve_project(str(root))

    def test_latex_log_detects_horizontal_overflow(self):
        diagnostics = DOCTOR.analyze_latex_log(
            "Overfull \\hbox (12.0pt too wide) in paragraph at lines 10--11"
        )
        self.assertEqual(["IPD907"], [item.code for item in diagnostics])

    def test_latex_log_names_undefined_reference(self):
        diagnostics = DOCTOR.analyze_latex_log(
            "LaTeX Warning: Reference `fig:missing-target' on page 2 undefined on input line 17."
        )
        issue = next(item for item in diagnostics if item.code == "IPD906")
        self.assertIn("fig:missing-target", issue.message)

    def test_compiler_failure_extracts_first_actionable_error(self):
        output = """latexmk output
! LaTeX Error: File `figures/missing.pdf' not found.
Type X to quit.
"""
        self.assertEqual(
            "! LaTeX Error: File `figures/missing.pdf' not found.",
            DOCTOR.first_compiler_error(output),
        )

    def test_project_static_check_finds_undefined_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main = Path(temp_dir) / "main.tex"
            main.write_text(
                r"\documentclass[journal,twocolumn]{IEEEtran}"
                + MINIMAL_BODY.replace(
                    "Scientific content must remain unchanged.",
                    r"See Fig.~\ref{fig:missing-target}.",
                ),
                encoding="utf-8",
            )
            diagnostics = DOCTOR.analyze_project(DOCTOR.resolve_project(str(main)))
            issue = next(item for item in diagnostics if item.code == "IPD110")
            self.assertIn("fig:missing-target", issue.message)
            self.assertEqual(str(main.resolve()), issue.file)

    def test_github_annotations_include_file_and_line(self):
        diagnostic = DOCTOR.Diagnostic(
            "IPD104", "warning", "Too wide", line=7, file="sections/results.tex"
        )
        output = io.StringIO()
        with redirect_stdout(output):
            DOCTOR.print_github_annotations(Path("main.tex"), [diagnostic])
        self.assertIn(
            "::warning file=sections/results.tex,line=7::IPD104: Too wide",
            output.getvalue(),
        )

    def test_markdown_report_lists_all_scanned_files(self):
        project = DOCTOR.Project(
            Path("main.tex"), (Path("main.tex"), Path("sections/results.tex"))
        )
        report = DOCTOR.markdown_report(project, [])
        self.assertIn("TeX files scanned: 2", report)
        self.assertIn("`sections/results.tex`", report)

    def test_report_does_not_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "audit.md"
            output.write_text("keep me", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                DOCTOR.write_report(str(output), "replacement", force=False)
            self.assertEqual("keep me", output.read_text(encoding="utf-8"))

    def test_project_json_preserves_legacy_file_field(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "check",
                str(ROOT / "examples" / "project"),
                "--format",
                "json",
            ],
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(0, result.returncode)
        self.assertEqual(payload["file"], payload["main_file"])
        self.assertEqual("1.2.0", payload["version"])
        self.assertEqual(2, len(payload["files"]))


class TransformTests(unittest.TestCase):
    def test_safe_transform_ignores_commented_document_class(self):
        source = (
            r"% \documentclass[journal,onecolumn]{IEEEtran}"
            + "\n"
            + r"\documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran}"
            + MINIMAL_BODY
        )
        transformed, _ = DOCTOR.safe_transform(source)
        self.assertIn(r"% \documentclass[journal,onecolumn]{IEEEtran}", transformed)
        self.assertIn(r"\documentclass[journal,twocolumn]{IEEEtran}", transformed)

    def test_safe_transform_is_conservative_and_idempotent(self):
        source = (
            r"\documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran}"
            + "\n"
            + r"\begin{figure}[H]"
            + "\n"
            + r"\includegraphics[width=\textwidth]{result.pdf}"
            + "\n"
            + r"\end{figure}"
            + MINIMAL_BODY
        )
        transformed, actions = DOCTOR.safe_transform(source)
        self.assertIn(r"\documentclass[journal,twocolumn]{IEEEtran}", transformed)
        self.assertIn(r"width=\columnwidth", transformed)
        self.assertIn(r"\begin{figure}[H]", transformed)
        self.assertIn("Scientific content must remain unchanged.", transformed)
        self.assertTrue(actions)

        second_pass, second_actions = DOCTOR.safe_transform(transformed)
        self.assertEqual(transformed, second_pass)
        self.assertEqual([], second_actions)

    def test_fix_defaults_to_diff_without_writing(self):
        source = r"\documentclass[journal,onecolumn]{IEEEtran}" + MINIMAL_BODY
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_path = Path(temp_dir) / "paper.tex"
            tex_path.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "fix", str(tex_path)],
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertIn("@@", result.stdout)
            self.assertEqual(source, tex_path.read_text(encoding="utf-8"))

    def test_fix_rechecks_included_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            main = root / "main.tex"
            child = root / "results.tex"
            main.write_text(
                r"\documentclass[journal,onecolumn]{IEEEtran}"
                + MINIMAL_BODY.replace(
                    "Scientific content must remain unchanged.", r"\input{results}"
                ),
                encoding="utf-8",
            )
            child.write_text(
                r"\begin{figure}\includegraphics[width=\textwidth]{result.pdf}\end{figure}",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "fix", str(main)],
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertIn("(2 TeX file(s))", result.stdout)
            self.assertIn("IPD104", result.stdout)


if __name__ == "__main__":
    unittest.main()
