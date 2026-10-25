"""Shared implementation for CHANGELOG.md-driven GitHub release notes.

Each `## X.Y.Z` section of CHANGELOG.md is the release body for tag `vX.Y.Z`.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from _lib.repo import ROOT

CHANGELOG = ROOT / "CHANGELOG.md"
SECTION_RE = re.compile(r"^## (\d+\.\d+\.\d+)\s*$", re.MULTILINE)
REPO_URL = "https://github.com/motherduckdb/agent-skills"


def sections(text: str | None = None) -> dict[str, str]:
    """Return {version: body} in file order, without the heading line."""
    text = CHANGELOG.read_text() if text is None else text
    matches = list(SECTION_RE.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1)] = text[match.end():end].strip()
    return result


def notes_for(version: str) -> str | None:
    """Release body for a version, with a link to the diff from the previous version."""
    all_sections = sections()
    body = all_sections.get(version)
    if body is None:
        return None
    versions = list(all_sections)
    position = versions.index(version)
    if position + 1 < len(versions):
        previous = versions[position + 1]
        body += f"\n\n**Full diff:** {REPO_URL}/compare/v{previous}...v{version}"
    return body + "\n"


def published_tags() -> set[str]:
    result = subprocess.run(
        ["gh", "release", "list", "--limit", "200", "--json", "tagName", "--jq", ".[].tagName"],
        check=True, text=True, capture_output=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def sync_published_releases(dry_run: bool = False) -> list[str]:
    """Rewrite the body of every published release that has a CHANGELOG section."""
    updated = []
    tags = published_tags()
    for version in sections():
        tag = f"v{version}"
        if tag not in tags:
            continue
        if not dry_run:
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
                handle.write(notes_for(version) or "")
                notes_path = Path(handle.name)
            try:
                subprocess.run(["gh", "release", "edit", tag, "--notes-file", str(notes_path)], check=True)
            finally:
                notes_path.unlink(missing_ok=True)
        updated.append(tag)
    return updated
