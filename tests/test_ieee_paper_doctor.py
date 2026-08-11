import importlib.util
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
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


if __name__ == "__main__":
    unittest.main()
