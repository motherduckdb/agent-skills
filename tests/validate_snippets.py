#!/usr/bin/env python3
"""Validate code snippets embedded in markdown files.

Extracts fenced code blocks from all .md files in the repo,
validates them per language, and reports errors.

Usage:
    python tests/validate_snippets.py
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
TS_CHECK_SCRIPT = Path(__file__).resolve().parent / "ts_syntax_check.js"

SKIP_PATTERN = re.compile(r"^\s*<!--\s*snippet-skip-next\s*-->\s*$")
FENCE_OPEN = re.compile(r"^```(\w*)(.*)$")
FENCE_CLOSE = re.compile(r"^```\s*$")
SKIP_LANGUAGES = {"", "text", "markdown", "md"}


@dataclass
class Snippet:
    file: Path
    line: int  # 1-based line number of the opening ```
    language: str
    code: str
    skip: bool = False


@dataclass
class SnippetError:
    file: str
    line: int
    language: str
    message: str


@dataclass
class ValidationResult:
    total: int = 0
    validated: int = 0
    skipped: int = 0
    errors: list[SnippetError] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------


def extract_snippets(path: Path) -> list[Snippet]:
    """Extract fenced code blocks from a markdown file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    snippets: list[Snippet] = []

    # Skip YAML frontmatter
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break

    i = start
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i])
        if m and not _inside_code_block(lines, i):
            language = m.group(1).lower()
            fence_line = i + 1  # 1-based

            # Check for skip annotation on previous non-blank line
            skip = False
            for j in range(i - 1, max(start - 1, -1), -1):
                if lines[j].strip() == "":
                    continue
                if SKIP_PATTERN.match(lines[j]):
                    skip = True
                break

            # Collect code until closing fence
            code_lines: list[str] = []
            i += 1
            while i < len(lines):
                if FENCE_CLOSE.match(lines[i]):
                    break
                code_lines.append(lines[i])
                i += 1

            snippets.append(
                Snippet(
                    file=path,
                    line=fence_line,
                    language=language,
                    code="\n".join(code_lines),
                    skip=skip,
                )
            )
        i += 1

    return snippets


def _inside_code_block(lines: list[str], idx: int) -> bool:
    """Check if line idx is already inside an open code block (shouldn't happen in valid MD)."""
    return False  # Simplified — we parse sequentially


# ---------------------------------------------------------------------------
# SQL validation
# ---------------------------------------------------------------------------


def split_sql_statements(code: str) -> list[str]:
    """Split SQL on semicolons, respecting string literals."""
    stmts: list[str] = []
    current: list[str] = []
    in_string = False
    prev_char = ""

    for char in code:
        if char == "'" and prev_char != "\\":
            in_string = not in_string
        if char == ";" and not in_string:
            stmts.append("".join(current))
            current = []
        else:
            current.append(char)
        prev_char = char

    remaining = "".join(current).strip()
    if remaining:
        stmts.append(remaining)

    return stmts


def strip_line_comment(line: str) -> str:
    """Remove trailing -- comment from a SQL line, respecting string literals."""
    in_string = False
    for i, char in enumerate(line):
        if char == "'":
            in_string = not in_string
        if not in_string and line[i:i + 2] == "--":
            return line[:i].rstrip()
    return line.rstrip()


def is_comment_only(stmt: str) -> bool:
    """Check if a statement is only comments and whitespace."""
    for line in stmt.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("--"):
            return False
    return True


def is_expression_block(code: str) -> bool:
    """Detect expression-style SQL blocks (one expression per line with -- comments)."""
    lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith("--")]
    if len(lines) < 2:
        return False
    # Heuristic: most lines have trailing comments
    comment_lines = sum(1 for l in code.splitlines() if l.strip() and "--" in l)
    return comment_lines > len(lines) * 0.5


def validate_sql(snippet: Snippet, conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Validate SQL syntax using DuckDB's json_serialize_sql()."""
    errors: list[str] = []
    code = snippet.code.strip()

    if not code:
        return errors

    # If it looks like an expression block (SYNTAX_REFERENCE.md style), validate per line
    if is_expression_block(code):
        return _validate_sql_expression_block(code, conn)

    # Otherwise, split on semicolons and validate each statement
    stmts = split_sql_statements(code)
    for stmt in stmts:
        stmt = stmt.strip()
        if not stmt or is_comment_only(stmt):
            continue

        err = _try_parse_sql(stmt, conn)
        if err:
            errors.append(err)

    return errors


def _try_parse_sql(stmt: str, conn: duckdb.DuckDBPyConnection) -> str | None:
    """Try to parse a SQL statement. Returns error message or None."""
    # Try direct parse
    try:
        conn.execute("SELECT json_serialize_sql(?)", [stmt])
        return None
    except duckdb.Error:
        pass

    # Try wrapping as SELECT expression
    expr = strip_line_comment(stmt).rstrip(";").strip()
    if expr:
        try:
            conn.execute("SELECT json_serialize_sql(?)", [f"SELECT {expr}"])
            return None
        except duckdb.Error:
            pass

    # Report the original error
    try:
        conn.execute("SELECT json_serialize_sql(?)", [stmt])
    except duckdb.Error as e:
        return f"  {_truncate(stmt, 80)}\n  Error: {e}"

    return None


def _validate_sql_expression_block(code: str, conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Validate expression-style SQL blocks line by line."""
    errors: list[str] = []

    for line in code.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue

        expr = strip_line_comment(stripped).strip()
        if not expr:
            continue

        # Try the whole line as a SELECT expression
        try:
            conn.execute("SELECT json_serialize_sql(?)", [f"SELECT {expr}"])
            continue
        except duckdb.Error:
            pass

        # Try splitting on " / " separator (used in SYNTAX_REFERENCE for alternatives)
        if " / " in expr:
            parts = [p.strip() for p in expr.split(" / ")]
            all_ok = True
            for part in parts:
                if not part:
                    continue
                try:
                    conn.execute("SELECT json_serialize_sql(?)", [f"SELECT {part}"])
                except duckdb.Error:
                    all_ok = False
                    break
            if all_ok:
                continue

        errors.append(f"  {_truncate(stripped, 80)}")

    return errors


# ---------------------------------------------------------------------------
# Python validation
# ---------------------------------------------------------------------------


def validate_python(snippet: Snippet) -> list[str]:
    """Validate Python syntax using ast.parse()."""
    try:
        ast.parse(snippet.code)
        return []
    except SyntaxError as e:
        return [f"  Line {e.lineno}: {e.msg}"]


# ---------------------------------------------------------------------------
# TypeScript/TSX/JS validation (batched)
# ---------------------------------------------------------------------------


def validate_typescript_batch(
    snippets: list[tuple[int, Snippet]],
) -> dict[int, list[str]]:
    """Validate a batch of TS/TSX/JS snippets in a single Node.js invocation.

    Returns a dict mapping snippet index to list of error messages.
    """
    if not snippets:
        return {}

    lang_to_kind = {"ts": "TS", "tsx": "TSX", "javascript": "JS", "js": "JS"}

    batch = []
    index_map: dict[int, int] = {}  # batch_index -> original_index
    for batch_idx, (orig_idx, snippet) in enumerate(snippets):
        kind = lang_to_kind.get(snippet.language, "TS")
        batch.append({"code": snippet.code, "kind": kind})
        index_map[batch_idx] = orig_idx

    try:
        result = subprocess.run(
            ["node", str(TS_CHECK_SCRIPT)],
            input=json.dumps(batch),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        # Node.js or typescript not installed
        return {
            idx: ["  TypeScript/Node.js not available for syntax checking"]
            for idx in [orig_idx for _, (orig_idx, _) in enumerate(snippets)]
        }
    except subprocess.TimeoutExpired:
        return {
            idx: ["  TypeScript syntax check timed out"]
            for idx in [orig_idx for _, (orig_idx, _) in enumerate(snippets)]
        }

    errors_by_index: dict[int, list[str]] = {}

    try:
        results = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        # If we can't parse the output, report error for all snippets
        err_msg = result.stderr.strip() or result.stdout.strip() or "Unknown parse error"
        for _, (orig_idx, _) in enumerate(snippets):
            errors_by_index[orig_idx] = [f"  {err_msg}"]
        return errors_by_index

    for entry in results:
        batch_idx = entry["index"]
        orig_idx = index_map[batch_idx]
        if entry["errors"]:
            errors_by_index[orig_idx] = [
                f"  Line {e['line']}: {e['message']}" for e in entry["errors"]
            ]

    return errors_by_index


# ---------------------------------------------------------------------------
# Bash validation
# ---------------------------------------------------------------------------


def validate_bash(snippet: Snippet) -> list[str]:
    """Validate bash syntax using bash -n."""
    try:
        result = subprocess.run(
            ["bash", "-n"],
            input=snippet.code,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return []
        return [f"  {result.stderr.strip()}"]
    except subprocess.TimeoutExpired:
        return ["  Bash syntax check timed out"]


# ---------------------------------------------------------------------------
# YAML validation
# ---------------------------------------------------------------------------


def validate_yaml(snippet: Snippet) -> list[str]:
    """Validate YAML syntax.

    Handles frontmatter-style blocks (``---`` delimited YAML followed by non-YAML content)
    by extracting and validating only the YAML portion.
    """
    code = snippet.code.strip()

    # Detect frontmatter-style blocks: starts with --- and has a closing ---
    # These are SKILL.md file examples containing YAML frontmatter + markdown body
    if code.startswith("---"):
        lines = code.splitlines()
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is not None:
            # Only validate the YAML between the --- delimiters
            yaml_content = "\n".join(lines[1:end])
            try:
                yaml.safe_load(yaml_content)
                return []
            except yaml.YAMLError as e:
                return [f"  {e}"]

    # Standard YAML validation with multi-document support
    try:
        list(yaml.safe_load_all(code))
        return []
    except yaml.YAMLError as e:
        return [f"  {e}"]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

SIMPLE_VALIDATORS = {
    "sql": None,  # handled specially with shared connection
    "python": validate_python,
    "bash": validate_bash,
    "sh": validate_bash,
    "yaml": validate_yaml,
    "yml": validate_yaml,
}

TS_LANGUAGES = {"ts", "tsx", "typescript", "javascript", "js"}


def validate_all() -> ValidationResult:
    """Walk all markdown files and validate every code snippet."""
    result = ValidationResult()

    md_files = sorted(ROOT.rglob("*.md"))
    # Exclude hidden directories and node_modules
    md_files = [
        f for f in md_files
        if not any(part.startswith(".") for part in f.relative_to(ROOT).parts)
        and "node_modules" not in f.parts
    ]

    all_snippets: list[Snippet] = []
    for md_file in md_files:
        all_snippets.extend(extract_snippets(md_file))

    result.total = len(all_snippets)

    # Separate snippets by validation type
    sql_snippets: list[tuple[int, Snippet]] = []
    ts_snippets: list[tuple[int, Snippet]] = []
    simple_snippets: list[tuple[int, Snippet]] = []

    for idx, snippet in enumerate(all_snippets):
        if snippet.skip or snippet.language in SKIP_LANGUAGES:
            result.skipped += 1
            continue

        if snippet.language == "sql":
            sql_snippets.append((idx, snippet))
        elif snippet.language in TS_LANGUAGES:
            ts_snippets.append((idx, snippet))
        elif snippet.language in SIMPLE_VALIDATORS:
            simple_snippets.append((idx, snippet))
        else:
            result.skipped += 1
            continue

        result.validated += 1

    # Validate SQL with shared connection
    if sql_snippets:
        conn = duckdb.connect(":memory:")
        for _, snippet in sql_snippets:
            errs = validate_sql(snippet, conn)
            for err in errs:
                result.errors.append(
                    SnippetError(
                        file=str(snippet.file.relative_to(ROOT)),
                        line=snippet.line,
                        language=snippet.language,
                        message=err,
                    )
                )
        conn.close()

    # Validate TS/TSX/JS in a single batch
    if ts_snippets:
        ts_errors = validate_typescript_batch(ts_snippets)
        for idx, snippet in ts_snippets:
            if idx in ts_errors:
                for err in ts_errors[idx]:
                    result.errors.append(
                        SnippetError(
                            file=str(snippet.file.relative_to(ROOT)),
                            line=snippet.line,
                            language=snippet.language,
                            message=err,
                        )
                    )

    # Validate simple types
    for _, snippet in simple_snippets:
        validator = SIMPLE_VALIDATORS[snippet.language]
        if validator is None:
            continue
        errs = validator(snippet)
        for err in errs:
            result.errors.append(
                SnippetError(
                    file=str(snippet.file.relative_to(ROOT)),
                    line=snippet.line,
                    language=snippet.language,
                    message=err,
                )
            )

    return result


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _truncate(s: str, max_len: int) -> str:
    s = s.replace("\n", " ")
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def format_console(result: ValidationResult) -> str:
    lines: list[str] = []
    lines.append(
        f"Validated {result.validated} snippets "
        f"({result.total} total, {result.skipped} skipped)"
    )

    if not result.errors:
        lines.append("All snippets passed validation.")
        return "\n".join(lines)

    lines.append(f"\n{len(result.errors)} error(s) found:\n")
    for err in result.errors:
        lines.append(f"--- {err.file}:{err.line} [{err.language}] ---")
        lines.append(err.message)
        lines.append("")

    return "\n".join(lines)


def write_errors_json(result: ValidationResult) -> None:
    """Write errors as JSON for the GitHub Actions PR comment step."""
    errors = [
        {
            "file": err.file,
            "line": err.line,
            "language": err.language,
            "message": err.message,
        }
        for err in result.errors
    ]
    (ROOT / "snippet-errors.json").write_text(json.dumps(errors, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    result = validate_all()
    print(format_console(result))
    write_errors_json(result)

    if result.errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
