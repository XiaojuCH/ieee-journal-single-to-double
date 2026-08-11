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


VERSION = "1.2.0"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    line: int | None = None
    file: str | None = None


@dataclass(frozen=True)
class Project:
    main: Path
    files: tuple[Path, ...]
    discovery_diagnostics: tuple[Diagnostic, ...] = ()


DOCUMENT_CLASS_RE = re.compile(
    r"\\documentclass\s*(?:\[([^\]]*)\]\s*)?\{\s*IEEEtran\s*\}", re.IGNORECASE
)
UNSTARRED_FLOAT_RE = re.compile(
    r"(?s)\\begin\{(?P<kind>figure|table)\}(?:\[[^\]]*\])?.*?"
    r"\\end\{(?P=kind)\}"
)
INCLUDE_RE = re.compile(
    r"\\(?P<command>input|include|subfile)\s*\{(?P<target>[^{}]+)\}",
    re.IGNORECASE,
)
IGNORED_PROJECT_DIRS = {".git", ".ieee-paper-doctor", "build", "dist", "out"}


def read_source(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig"), has_bom


def write_source(path: Path, text: str, has_bom: bool) -> None:
    payload = text.encode("utf-8")
    if has_bom:
        payload = b"\xef\xbb\xbf" + payload
    path.write_bytes(payload)


def iter_tex_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.tex")):
        relative_parts = path.relative_to(root).parts[:-1]
        if any(part.lower() in IGNORED_PROJECT_DIRS for part in relative_parts):
            continue
        yield path.resolve()


def discover_main_file(root: Path) -> Path:
    candidates: list[Path] = []
    for path in iter_tex_files(root):
        text, _ = read_source(path)
        if DOCUMENT_CLASS_RE.search(strip_tex_comments(text)):
            candidates.append(path)
    if not candidates:
        raise FileNotFoundError(f"No IEEEtran main TeX file was found under: {root}")
    if len(candidates) > 1:
        listed = ", ".join(str(path.relative_to(root)) for path in candidates[:5])
        suffix = " ..." if len(candidates) > 5 else ""
        raise ValueError(
            f"Multiple IEEEtran main files were found under {root}: {listed}{suffix}. "
            "Pass the intended main .tex file explicitly."
        )
    return candidates[0]


def resolve_project(value: str) -> Project:
    target = Path(value).expanduser().resolve()
    if target.is_dir():
        main = discover_main_file(target)
    elif target.is_file():
        main = target
    else:
        raise FileNotFoundError(f"TeX file or project directory not found: {target}")

    files: list[Path] = []
    diagnostics: list[Diagnostic] = []
    queued = [main]
    seen: set[Path] = set()
    while queued:
        current = queued.pop(0).resolve()
        if current in seen:
            continue
        seen.add(current)
        files.append(current)
        text, _ = read_source(current)
        clean = strip_tex_comments(text)
        for match in INCLUDE_RE.finditer(clean):
            raw_target = match.group("target").strip()
            if any(marker in raw_target for marker in ("\\", "#", "$")):
                diagnostics.append(
                    Diagnostic(
                        "IPD109",
                        "warning",
                        f"Could not resolve dynamic \\{match.group('command')} target: {raw_target}",
                        line_number(clean, match.start()),
                        str(current),
                    )
                )
                continue
            requested_path = Path(raw_target)
            if not requested_path.suffix:
                requested_path = requested_path.with_suffix(".tex")
            candidate_paths = [
                (main.parent / requested_path).resolve(),
                (current.parent / requested_path).resolve(),
            ]
            include_path = next(
                (candidate for candidate in candidate_paths if candidate.is_file()),
                None,
            )
            if include_path is None:
                diagnostics.append(
                    Diagnostic(
                        "IPD108",
                        "warning",
                        f"Included TeX file was not found: {raw_target}",
                        line_number(clean, match.start()),
                        str(current),
                    )
                )
                continue
            if include_path not in seen:
                queued.append(include_path)
    return Project(main, tuple(files), tuple(diagnostics))


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
    source_path: Path | None = None,
) -> None:
    items.append(
        Diagnostic(
            code=code,
            severity=severity,
            message=message,
            line=line_number(text, match.start()) if match else None,
            file=str(source_path) if source_path else None,
        )
    )


def analyze(
    text: str,
    *,
    source_path: Path | None = None,
    require_document_structure: bool = True,
) -> list[Diagnostic]:
    clean = strip_tex_comments(text)
    diagnostics: list[Diagnostic] = []

    class_match = DOCUMENT_CLASS_RE.search(clean)
    if require_document_structure and not class_match:
        add_diagnostic(
            diagnostics,
            "IPD001",
            "error",
            "No IEEEtran document class was found; this tool only handles IEEEtran projects.",
            clean,
            source_path=source_path,
        )
    elif class_match:
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
                source_path,
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
                source_path,
            )

    match = re.search(r"\\maketitle\b", clean)
    if require_document_structure and not match:
        add_diagnostic(
            diagnostics,
            "IPD004",
            "error",
            "Missing \\maketitle.",
            clean,
            source_path=source_path,
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
            source_path,
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
            source_path,
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
            source_path,
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
                    file=str(source_path) if source_path else None,
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
            source_path,
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
            source_path,
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
                source_path,
            )

    return diagnostics


def analyze_project(
    project: Project,
    source_overrides: dict[Path, str] | None = None,
) -> list[Diagnostic]:
    overrides = {path.resolve(): text for path, text in (source_overrides or {}).items()}
    diagnostics = list(project.discovery_diagnostics)
    project_sources: list[tuple[Path, str]] = []
    for path in project.files:
        text = overrides.get(path.resolve())
        if text is None:
            text, _ = read_source(path)
        project_sources.append((path, text))
        diagnostics.extend(
            analyze(
                text,
                source_path=path,
                require_document_structure=path == project.main,
            )
        )
    clean_sources = [(path, strip_tex_comments(text)) for path, text in project_sources]
    if not any(re.search(r"\\externaldocument\b", text) for _, text in clean_sources):
        labels = {
            match.group(1).strip()
            for _, text in clean_sources
            for match in re.finditer(r"\\label\s*\{([^{}]+)\}", text)
        }
        reported: set[str] = set()
        reference_re = re.compile(
            r"\\(?:ref|eqref|pageref|autoref|cref|Cref)\*?\s*\{([^{}]+)\}"
        )
        for path, text in clean_sources:
            for match in reference_re.finditer(text):
                for key in (item.strip() for item in match.group(1).split(",")):
                    if not key or key in labels or key in reported:
                        continue
                    if any(marker in key for marker in ("\\", "#", "$")):
                        continue
                    reported.add(key)
                    diagnostics.append(
                        Diagnostic(
                            "IPD110",
                            "warning",
                            f"Reference target is not defined in the scanned project: {key}",
                            line_number(text, match.start()),
                            str(path),
                        )
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
        item_path = Path(item.file) if item.file else path
        location = f":{item.line}" if item.line else ""
        print(f"{item_path}{location}: {item.severity}: {item.code}: {item.message}")
    summary = diagnostic_summary(diagnostics)
    print(f"Summary: {summary['errors']} error(s), {summary['warnings']} warning(s)")


def github_escape(value: str, *, property_value: bool = False) -> str:
    escaped = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if property_value:
        escaped = escaped.replace(":", "%3A").replace(",", "%2C")
    return escaped


def portable_path(path: Path, *, base: Path | None = None) -> str:
    resolved = path.resolve()
    for candidate_base in (base, Path.cwd()):
        if candidate_base is None:
            continue
        try:
            return resolved.relative_to(candidate_base.resolve()).as_posix()
        except ValueError:
            continue
    return resolved.as_posix()


def print_github_annotations(path: Path, diagnostics: Sequence[Diagnostic]) -> None:
    for item in diagnostics:
        item_path = portable_path(Path(item.file) if item.file else path)
        properties = f"file={github_escape(item_path, property_value=True)}"
        if item.line:
            properties += f",line={item.line}"
        message = github_escape(f"{item.code}: {item.message}")
        print(f"::{item.severity} {properties}::{message}")
    summary = diagnostic_summary(diagnostics)
    print(
        "::notice::IEEE Paper Doctor scanned "
        f"{path}: {summary['errors']} error(s), {summary['warnings']} warning(s)"
    )


def markdown_report(
    project: Project,
    diagnostics: Sequence[Diagnostic],
    *,
    compiled: bool = False,
    compiler_returncode: int | None = None,
) -> str:
    summary = diagnostic_summary(diagnostics)
    status = "PASS" if not should_fail(diagnostics, strict=True) else "REVIEW REQUIRED"
    lines = [
        "# IEEE Paper Doctor Audit",
        "",
        f"- Version: `{VERSION}`",
        f"- Status: **{status}**",
        f"- Main file: `{portable_path(project.main, base=project.main.parent)}`",
        f"- TeX files scanned: {len(project.files)}",
        f"- Diagnostics: {summary['errors']} error(s), {summary['warnings']} warning(s)",
    ]
    if compiled:
        compile_status = "passed" if compiler_returncode == 0 else "failed"
        lines.append(f"- Compilation: **{compile_status}**")
    lines.extend(["", "## Files scanned", ""])
    lines.extend(
        f"- `{portable_path(path, base=project.main.parent)}`" for path in project.files
    )
    lines.extend(["", "## Diagnostics", ""])
    if not diagnostics:
        lines.append("No issues found.")
    else:
        lines.extend(
            [
                "| Severity | Code | Location | Finding |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in diagnostics:
            item_path = portable_path(
                Path(item.file) if item.file else project.main,
                base=project.main.parent,
            )
            location = item_path + (f":{item.line}" if item.line else "")
            message = item.message.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {item.severity} | `{item.code}` | `{location}` | {message} |"
            )
    lines.extend(["", "_Generated by IEEE Paper Doctor._", ""])
    return "\n".join(lines)


def write_report(
    output: str,
    report: str,
    *,
    force: bool,
) -> Path:
    path = Path(output).expanduser().resolve()
    if path.exists() and not force:
        raise FileExistsError(f"Report exists: {path}. Use --force to replace it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return path


def requested_format(args: argparse.Namespace) -> str:
    return "json" if getattr(args, "json", False) else getattr(args, "format", "text")


def emit_project_diagnostics(
    args: argparse.Namespace,
    project: Project,
    diagnostics: Sequence[Diagnostic],
    *,
    extra_json: dict[str, object] | None = None,
) -> None:
    output_format = requested_format(args)
    if output_format == "json":
        payload: dict[str, object] = {
            "version": VERSION,
            "file": str(project.main),
            "main_file": str(project.main),
            "files": [str(path) for path in project.files],
            "summary": diagnostic_summary(diagnostics),
            "diagnostics": [asdict(item) for item in diagnostics],
        }
        if extra_json:
            payload.update(extra_json)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif output_format == "github":
        print_github_annotations(project.main, diagnostics)
    else:
        print(f"Project main file: {project.main} ({len(project.files)} TeX file(s))")
        print_diagnostics(project.main, diagnostics)


def make_diff(path: Path, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path) + ".converted",
        )
    )


def analyze_latex_log(log_text: str, log_path: Path | None = None) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    log_checks = (
        (r"LaTeX Error", "error", "IPD903", "The LaTeX log contains an error."),
        (r"Float too large", "warning", "IPD904", "The LaTeX log reports an oversized float."),
        (r"Overfull \\vbox", "warning", "IPD905", "The LaTeX log reports an overfull vertical box."),
        (r"Overfull \\hbox", "warning", "IPD907", "The LaTeX log reports horizontal overflow that can cross a column or page margin."),
    )
    for pattern, severity, code, message in log_checks:
        match = re.search(pattern, log_text, re.IGNORECASE)
        if match:
            diagnostics.append(
                Diagnostic(
                    code,
                    severity,
                    message,
                    line=line_number(log_text, match.start()),
                    file=str(log_path) if log_path else None,
                )
            )
    undefined_match = re.search(
        r"(?:Reference|Citation)\s+[`']([^`']+)'[^\r\n]*undefined|There were undefined references",
        log_text,
        re.IGNORECASE,
    )
    if undefined_match:
        missing_keys = list(
            dict.fromkeys(
                re.findall(
                    r"(?:Reference|Citation)\s+[`']([^`']+)'[^\r\n]*undefined",
                    log_text,
                    re.IGNORECASE,
                )
            )
        )
        detail = ""
        if missing_keys:
            visible = ", ".join(missing_keys[:5])
            suffix = ", ..." if len(missing_keys) > 5 else ""
            detail = f" Missing key(s): {visible}{suffix}."
        diagnostics.append(
            Diagnostic(
                "IPD906",
                "warning",
                "The LaTeX log reports undefined references or citations." + detail,
                line=line_number(log_text, undefined_match.start()),
                file=str(log_path) if log_path else None,
            )
        )
    return diagnostics


def first_compiler_error(output: str) -> str | None:
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("! ") or re.search(r"\.tex:\d+:\s", stripped):
            return stripped[:300]
    return None


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
        "-file-line-error",
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
        detail = first_compiler_error(result.stdout)
        message = "latexmk failed; inspect the compiler output."
        if detail:
            message += f" First compiler error: {detail}"
        diagnostics.append(
            Diagnostic("IPD902", "error", message, file=str(path))
        )
    log_path = path.with_suffix(".log")
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        diagnostics.extend(analyze_latex_log(log_text, log_path))
    return result.returncode, result.stdout, diagnostics


def require_tex_file(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"TeX file not found: {path}")
    return path


def run_check(args: argparse.Namespace) -> int:
    project = resolve_project(args.target)
    diagnostics = analyze_project(project)
    emit_project_diagnostics(args, project, diagnostics)
    if args.report:
        report_path = write_report(
            args.report,
            markdown_report(project, diagnostics),
            force=args.force,
        )
        if requested_format(args) == "text":
            print(f"Report: {report_path}")
    return 1 if should_fail(diagnostics, args.strict) else 0


def run_fix(args: argparse.Namespace) -> int:
    path = require_tex_file(args.tex_file)
    before, has_bom = read_source(path)
    after, actions = safe_transform(before)
    project = resolve_project(str(path))
    diagnostics = analyze_project(project, {path: after})
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
                    "version": VERSION,
                    "file": str(path),
                    "main_file": str(project.main),
                    "files": [str(item) for item in project.files],
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
        print(f"Project main file: {project.main} ({len(project.files)} TeX file(s))")
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
    project = resolve_project(args.target)
    diagnostics = analyze_project(project)
    compiler_returncode: int | None = None
    compiler_output = ""
    if args.compile:
        compiler_returncode, compiler_output, compile_diagnostics = compile_document(project.main)
        diagnostics.extend(compile_diagnostics)

    emit_project_diagnostics(
        args,
        project,
        diagnostics,
        extra_json={
            "compiled": args.compile,
            "compiler_returncode": compiler_returncode,
        },
    )
    if args.report:
        report_path = write_report(
            args.report,
            markdown_report(
                project,
                diagnostics,
                compiled=args.compile,
                compiler_returncode=compiler_returncode,
            ),
            force=args.force,
        )
        if requested_format(args) == "text":
            print(f"Report: {report_path}")
    if requested_format(args) == "text":
        if compiler_returncode:
            print("\nCompiler output (last 40 lines):")
            print("\n".join(compiler_output.splitlines()[-40:]))
        elif args.compile:
            print("Compilation succeeded.")
    return 1 if should_fail(diagnostics, args.strict) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ieee-paper-doctor",
        description="Audit, conservatively fix, and verify IEEEtran two-column projects.",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Audit a TeX file or project directory.")
    check.add_argument("target", help="Main .tex file or project directory.")
    check.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    check_format = check.add_mutually_exclusive_group()
    check_format.add_argument("--json", action="store_true", help="Emit machine-readable JSON (legacy alias).")
    check_format.add_argument(
        "--format",
        choices=("text", "json", "github"),
        default="text",
        help="Choose human text, JSON, or GitHub Actions annotations.",
    )
    check.add_argument("--report", help="Write a shareable Markdown audit report.")
    check.add_argument("--force", action="store_true", help="Replace an existing report.")
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

    verify = subparsers.add_parser("verify", help="Audit and optionally compile a TeX project.")
    verify.add_argument("target", help="Main .tex file or project directory.")
    verify.add_argument("--compile", action="store_true", help="Compile with latexmk.")
    verify.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    verify_format = verify.add_mutually_exclusive_group()
    verify_format.add_argument("--json", action="store_true", help="Emit machine-readable JSON (legacy alias).")
    verify_format.add_argument(
        "--format",
        choices=("text", "json", "github"),
        default="text",
        help="Choose human text, JSON, or GitHub Actions annotations.",
    )
    verify.add_argument("--report", help="Write a shareable Markdown audit report.")
    verify.add_argument("--force", action="store_true", help="Replace an existing report.")
    verify.set_defaults(handler=run_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (FileNotFoundError, FileExistsError, PermissionError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
