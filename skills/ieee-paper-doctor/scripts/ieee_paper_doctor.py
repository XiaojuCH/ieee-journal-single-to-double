#!/usr/bin/env python3
"""Conservative IEEEtran two-column audit, fix, and verification CLI."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


VERSION = "1.1.0"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    line: int | None = None


DOCUMENT_CLASS_RE = re.compile(
    r"\\documentclass(?:\[([^\]]*)\])?\{IEEEtran\}", re.IGNORECASE
)
UNSTARRED_FLOAT_RE = re.compile(
    r"(?s)\\begin\{(?P<kind>figure|table)\}(?:\[[^\]]*\])?.*?"
    r"\\end\{(?P=kind)\}"
)


def read_source(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig"), has_bom


def write_source(path: Path, text: str, has_bom: bool) -> None:
    payload = text.encode("utf-8")
    if has_bom:
        payload = b"\xef\xbb\xbf" + payload
    path.write_bytes(payload)


def strip_tex_comments(text: str) -> str:
    """Replace unescaped TeX comments with spaces while preserving offsets."""
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        comment_at: int | None = None
        for index, char in enumerate(line):
            if char != "%":
                continue
            slash_count = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                slash_count += 1
                cursor -= 1
            if slash_count % 2 == 0:
                comment_at = index
                break
        if comment_at is None:
            output.append(line)
            continue
        ending = ""
        if line.endswith("\r\n"):
            ending = "\r\n"
        elif line.endswith("\n") or line.endswith("\r"):
            ending = line[-1]
        visible_length = len(line) - len(ending)
        output.append(line[:comment_at] + " " * (visible_length - comment_at) + ending)
    return "".join(output)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def add_diagnostic(
    items: list[Diagnostic],
    code: str,
    severity: str,
    message: str,
    text: str,
    match: re.Match[str] | None = None,
) -> None:
    items.append(
        Diagnostic(
            code=code,
            severity=severity,
            message=message,
            line=line_number(text, match.start()) if match else None,
        )
    )


def analyze(text: str) -> list[Diagnostic]:
    clean = strip_tex_comments(text)
    diagnostics: list[Diagnostic] = []

    class_match = DOCUMENT_CLASS_RE.search(clean)
    if not class_match:
        add_diagnostic(
            diagnostics,
            "IPD001",
            "error",
            "No IEEEtran document class was found; this tool only handles IEEEtran projects.",
            clean,
        )
    else:
        options = {
            item.strip().lower()
            for item in (class_match.group(1) or "").split(",")
            if item.strip()
        }
        if "journal" not in options:
            add_diagnostic(
                diagnostics,
                "IPD002",
                "error",
                "IEEEtran is not in journal mode; confirm the target before converting.",
                clean,
                class_match,
            )
        incompatible = sorted(
            options.intersection({"onecolumn", "draft", "draftcls", "draftclsnofoot"})
        )
        if incompatible:
            add_diagnostic(
                diagnostics,
                "IPD003",
                "error",
                "Draft or one-column class options remain: " + ", ".join(incompatible) + ".",
                clean,
                class_match,
            )

    match = re.search(r"\\maketitle\b", clean)
    if not match:
        add_diagnostic(
            diagnostics, "IPD004", "error", "Missing \\maketitle.", clean
        )

    match = re.search(r"\\IEEEauthorblock[NA]\b", clean)
    if match:
        add_diagnostic(
            diagnostics,
            "IPD101",
            "warning",
            "Conference-style IEEEauthorblock commands remain in journal mode.",
            clean,
            match,
        )

    match = re.search(
        r"\\begin\{IEEEbiography(?:nophoto)?\}|PLACE\s+PHOTO\s+HERE",
        clean,
        re.IGNORECASE,
    )
    if match:
        add_diagnostic(
            diagnostics,
            "IPD102",
            "warning",
            "Biography or photo material remains; verify whether the submission stage requires it.",
            clean,
            match,
        )

    for match in re.finditer(
        r"\\begin\{(?:figure|table|algorithm)\}\s*\[\s*H\s*\]", clean
    ):
        add_diagnostic(
            diagnostics,
            "IPD103",
            "warning",
            "A pinned [H] float remains; review its placement in two-column output.",
            clean,
            match,
        )

    width_patterns = (
        re.compile(r"\\includegraphics\[[^\]]*\bwidth\s*=\s*\\textwidth"),
        re.compile(r"\\makebox\[\s*\\textwidth\s*\]"),
        re.compile(r"\\rule\{\s*(?:0?\.\d+|1(?:\.0+)?)\\textwidth\s*\}"),
    )
    for float_match in UNSTARRED_FLOAT_RE.finditer(clean):
        block = float_match.group(0)
        local_match = next(
            (pattern.search(block) for pattern in width_patterns if pattern.search(block)),
            None,
        )
        if local_match:
            diagnostics.append(
                Diagnostic(
                    code="IPD104",
                    severity="warning",
                    message="An unstarred float uses text width; use column width or deliberately promote it to a starred float.",
                    line=line_number(
                        clean, float_match.start() + local_match.start()
                    ),
                )
            )

    match = re.search(r"(?:width\s*=\s*|\{)1\.[0-9]+\\textwidth", clean)
    if match:
        add_diagnostic(
            diagnostics,
            "IPD105",
            "warning",
            "An overwide 1.x\\textwidth sizing expression remains.",
            clean,
            match,
        )

    match = re.search(r"\\usepackage\s*\[\s*section\s*\]\s*\{placeins\}", clean)
    if match:
        add_diagnostic(
            diagnostics,
            "IPD106",
            "warning",
            "placeins with the section option can create large whitespace gaps.",
            clean,
            match,
        )

    bibliography_end = re.search(r"\\end\{thebibliography\}", clean)
    document_end = re.search(r"\\end\{document\}", clean)
    if bibliography_end and document_end and bibliography_end.end() < document_end.start():
        tail = clean[bibliography_end.end() : document_end.start()].strip()
        if tail:
            add_diagnostic(
                diagnostics,
                "IPD107",
                "warning",
                "Content remains between the bibliography and \\end{document}.",
                clean,
                bibliography_end,
            )

    return diagnostics


def normalize_document_class(match: re.Match[str], actions: list[str]) -> str:
    raw_options = [item.strip() for item in (match.group(1) or "").split(",") if item.strip()]
    lowered = {item.lower() for item in raw_options}
    if "journal" not in lowered:
        return match.group(0)

    remove = {"onecolumn", "draft", "draftcls", "draftclsnofoot", "11pt", "12pt"}
    normalized = [item for item in raw_options if item.lower() not in remove]
    if "twocolumn" not in {item.lower() for item in normalized}:
        journal_index = next(
            (index for index, item in enumerate(normalized) if item.lower() == "journal"),
            len(normalized) - 1,
        )
        normalized.insert(journal_index + 1, "twocolumn")

    replacement = "\\documentclass[" + ",".join(normalized) + "]{IEEEtran}"
    if replacement != match.group(0):
        actions.append("Normalized IEEEtran journal class options for explicit two-column output.")
    return replacement


def transform_unstarred_float_block(block: str, actions: list[str]) -> str:
    updated = re.sub(
        r"\bwidth(\s*)=(\s*)\\textwidth",
        r"width\1=\2\\columnwidth",
        block,
    )
    updated = re.sub(
        r"(\\makebox\[\s*)\\textwidth(\s*\])",
        r"\1\\columnwidth\2",
        updated,
    )
    updated = re.sub(
        r"(\\rule\{\s*(?:0?\.\d+|1(?:\.0+)?))\\textwidth(\s*\})",
        r"\1\\columnwidth\2",
        updated,
    )
    if updated != block:
        actions.append(
            "Changed an obvious text-width expression inside an unstarred float to column width."
        )
    return updated


def safe_transform(text: str) -> tuple[str, list[str]]:
    actions: list[str] = []
    transformed = text

    clean = strip_tex_comments(transformed)
    clean_class_match = DOCUMENT_CLASS_RE.search(clean)
    if clean_class_match:
        raw_class_match = DOCUMENT_CLASS_RE.match(transformed, clean_class_match.start())
        if raw_class_match:
            replacement = normalize_document_class(raw_class_match, actions)
            transformed = (
                transformed[: raw_class_match.start()]
                + replacement
                + transformed[raw_class_match.end() :]
            )

    clean = strip_tex_comments(transformed)
    float_matches = list(UNSTARRED_FLOAT_RE.finditer(clean))
    for float_match in reversed(float_matches):
        start, end = float_match.span()
        replacement = transform_unstarred_float_block(
            transformed[start:end], actions
        )
        transformed = transformed[:start] + replacement + transformed[end:]
    return transformed, list(dict.fromkeys(actions))


def diagnostic_summary(diagnostics: Iterable[Diagnostic]) -> dict[str, int]:
    summary = {"errors": 0, "warnings": 0}
    for item in diagnostics:
        if item.severity == "error":
            summary["errors"] += 1
        elif item.severity == "warning":
            summary["warnings"] += 1
    return summary


def should_fail(diagnostics: Sequence[Diagnostic], strict: bool) -> bool:
    summary = diagnostic_summary(diagnostics)
    return bool(summary["errors"] or (strict and summary["warnings"]))


def print_diagnostics(path: Path, diagnostics: Sequence[Diagnostic]) -> None:
    if not diagnostics:
        print(f"IEEE Paper Doctor: {path}: no issues found")
        return
    for item in diagnostics:
        location = f":{item.line}" if item.line else ""
        print(f"{path}{location}: {item.severity}: {item.code}: {item.message}")
    summary = diagnostic_summary(diagnostics)
    print(f"Summary: {summary['errors']} error(s), {summary['warnings']} warning(s)")


def make_diff(path: Path, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path) + ".converted",
        )
    )


def compile_document(path: Path) -> tuple[int, str, list[Diagnostic]]:
    latexmk = shutil.which("latexmk")
    if not latexmk:
        return (
            2,
            "latexmk was not found on PATH.",
            [Diagnostic("IPD901", "error", "latexmk was not found on PATH.")],
        )
    command = [
        latexmk,
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        path.name,
    ]
    result = subprocess.run(
        command,
        cwd=path.parent,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    diagnostics: list[Diagnostic] = []
    if result.returncode != 0:
        diagnostics.append(
            Diagnostic("IPD902", "error", "latexmk failed; inspect the compiler output.")
        )
    log_path = path.with_suffix(".log")
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        log_checks = (
            (r"LaTeX Error", "error", "IPD903", "The LaTeX log contains an error."),
            (r"Float too large", "warning", "IPD904", "The LaTeX log reports an oversized float."),
            (r"Overfull \\vbox", "warning", "IPD905", "The LaTeX log reports an overfull vertical box."),
            (r"There were undefined references|Citation .* undefined", "warning", "IPD906", "The LaTeX log reports undefined references or citations."),
        )
        for pattern, severity, code, message in log_checks:
            if re.search(pattern, log_text, re.IGNORECASE):
                diagnostics.append(Diagnostic(code, severity, message))
    return result.returncode, result.stdout, diagnostics


def require_tex_file(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"TeX file not found: {path}")
    return path


def run_check(args: argparse.Namespace) -> int:
    path = require_tex_file(args.tex_file)
    text, _ = read_source(path)
    diagnostics = analyze(text)
    if args.json:
        print(
            json.dumps(
                {
                    "file": str(path),
                    "summary": diagnostic_summary(diagnostics),
                    "diagnostics": [asdict(item) for item in diagnostics],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print_diagnostics(path, diagnostics)
    return 1 if should_fail(diagnostics, args.strict) else 0


def run_fix(args: argparse.Namespace) -> int:
    path = require_tex_file(args.tex_file)
    before, has_bom = read_source(path)
    after, actions = safe_transform(before)
    diagnostics = analyze(after)
    diff = make_diff(path, before, after)

    destination: Path | None = None
    if args.write:
        destination = path
    elif args.output:
        destination = Path(args.output).expanduser().resolve()

    if destination:
        if destination.exists() and destination != path and not args.force:
            raise FileExistsError(
                f"Output exists: {destination}. Use --force to replace it."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_source(destination, after, has_bom)

    if args.json:
        print(
            json.dumps(
                {
                    "file": str(path),
                    "output": str(destination) if destination else None,
                    "changed": before != after,
                    "actions": actions,
                    "diff": diff,
                    "summary": diagnostic_summary(diagnostics),
                    "diagnostics": [asdict(item) for item in diagnostics],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if actions:
            for action in actions:
                print(f"- {action}")
        else:
            print("No deterministic fixes were available.")
        if destination:
            print(f"Wrote: {destination}")
        elif diff:
            print(diff, end="" if diff.endswith("\n") else "\n")
        print_diagnostics(destination or path, diagnostics)
    return 1 if should_fail(diagnostics, args.strict) else 0


def run_verify(args: argparse.Namespace) -> int:
    path = require_tex_file(args.tex_file)
    text, _ = read_source(path)
    diagnostics = analyze(text)
    compiler_returncode: int | None = None
    compiler_output = ""
    if args.compile:
        compiler_returncode, compiler_output, compile_diagnostics = compile_document(path)
        diagnostics.extend(compile_diagnostics)

    if args.json:
        print(
            json.dumps(
                {
                    "file": str(path),
                    "compiled": args.compile,
                    "compiler_returncode": compiler_returncode,
                    "summary": diagnostic_summary(diagnostics),
                    "diagnostics": [asdict(item) for item in diagnostics],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print_diagnostics(path, diagnostics)
        if compiler_returncode:
            print("\nCompiler output (last 40 lines):")
            print("\n".join(compiler_output.splitlines()[-40:]))
        elif args.compile:
            print("Compilation succeeded.")
    return 1 if should_fail(diagnostics, args.strict) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ieee-paper-doctor",
        description="Audit, conservatively fix, and verify IEEEtran two-column manuscripts.",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Audit a TeX file without changing it.")
    check.add_argument("tex_file")
    check.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    check.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    check.set_defaults(handler=run_check)

    fix = subparsers.add_parser("fix", help="Generate conservative, reviewable fixes.")
    fix.add_argument("tex_file")
    output_group = fix.add_mutually_exclusive_group()
    output_group.add_argument("--write", action="store_true", help="Overwrite the input file.")
    output_group.add_argument("--output", help="Write the converted source to a new file.")
    fix.add_argument("--force", action="store_true", help="Replace an existing --output file.")
    fix.add_argument("--strict", action="store_true", help="Treat remaining warnings as failures.")
    fix.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    fix.set_defaults(handler=run_fix)

    verify = subparsers.add_parser("verify", help="Audit and optionally compile a TeX file.")
    verify.add_argument("tex_file")
    verify.add_argument("--compile", action="store_true", help="Compile with latexmk.")
    verify.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    verify.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    verify.set_defaults(handler=run_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (FileNotFoundError, FileExistsError, PermissionError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
