"""Shared implementation for repo-wide version bumps and release checks.

The canonical version is the top-level "version" in package.json. A release
must keep every surface aligned:

- "version" fields in the package/plugin/extension manifests
- INTEGRATION_VERSION in scripts/_lib/motherduck_user_agent.py
- "agent-skills/<version>" watermark strings across skills, plugins, and docs
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Manifests where every "version" key holding the current version is bumped.
MANIFEST_PATHS = [
    "package.json",
    "package-lock.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    "gemini-extension.json",
    "plugins/motherduck-skills-claude/.claude-plugin/plugin.json",
    "plugins/motherduck-skills/.codex-plugin/plugin.json",
]

USER_AGENT_MODULE = "scripts/_lib/motherduck_user_agent.py"
INTEGRATION_VERSION_RE = re.compile(r'(INTEGRATION_VERSION = ")(\d+\.\d+\.\d+)(")')

WATERMARK_TEMPLATE = "agent-skills/{version}"


class ReleaseError(Exception):
    pass


def current_version() -> str:
    payload = json.loads((REPO_ROOT / "package.json").read_text())
    version = payload.get("version")
    if not version or not VERSION_RE.match(version):
        raise ReleaseError(f"package.json has no valid semver version: {version!r}")
    return version


def _tracked_text_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    files = []
    for line in output.splitlines():
        path = REPO_ROOT / line
        if not path.is_file():
            continue
        try:
            path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        files.append(path)
    return files


def _replace_versions(node, old: str, new: str) -> int:
    """Replace "version": <old> with <new> anywhere in a parsed JSON tree."""
    replaced = 0
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "version" and value == old:
                node[key] = new
                replaced += 1
            else:
                replaced += _replace_versions(value, old, new)
    elif isinstance(node, list):
        for item in node:
            replaced += _replace_versions(item, old, new)
    return replaced


def bump(new_version: str) -> list[str]:
    """Bump every version surface from the current version. Returns a change log."""
    if not VERSION_RE.match(new_version):
        raise ReleaseError(f"not a valid X.Y.Z version: {new_version!r}")
    old_version = current_version()
    if new_version == old_version:
        raise ReleaseError(f"repo is already at version {old_version}")

    changes: list[str] = []

    for rel_path in MANIFEST_PATHS:
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        payload = json.loads(path.read_text())
        replaced = _replace_versions(payload, old_version, new_version)
        if replaced:
            path.write_text(json.dumps(payload, indent=2) + "\n")
            changes.append(f"{rel_path}: {replaced} version field(s)")

    module_path = REPO_ROOT / USER_AGENT_MODULE
    module_text = module_path.read_text()
    new_text, replaced = INTEGRATION_VERSION_RE.subn(
        rf"\g<1>{new_version}\g<3>", module_text
    )
    if replaced:
        module_path.write_text(new_text)
        changes.append(f"{USER_AGENT_MODULE}: INTEGRATION_VERSION")

    old_watermark = WATERMARK_TEMPLATE.format(version=old_version)
    new_watermark = WATERMARK_TEMPLATE.format(version=new_version)
    watermark_files = 0
    for path in _tracked_text_files():
        text = path.read_text()
        if old_watermark in text:
            path.write_text(text.replace(old_watermark, new_watermark))
            watermark_files += 1
    if watermark_files:
        changes.append(f"watermark {old_watermark} -> {new_watermark}: {watermark_files} file(s)")

    return changes


def check(expected_version: str) -> list[str]:
    """Return a list of mismatches between the repo and the expected version."""
    if not VERSION_RE.match(expected_version):
        raise ReleaseError(f"not a valid X.Y.Z version: {expected_version!r}")
    problems: list[str] = []

    repo_version = current_version()
    if repo_version != expected_version:
        problems.append(
            f"package.json version is {repo_version}, expected {expected_version}"
        )

    for rel_path in MANIFEST_PATHS:
        path = REPO_ROOT / rel_path
        if not path.exists() or rel_path == "package-lock.json":
            continue
        text = path.read_text()
        for match in re.finditer(r'"version":\s*"(\d+\.\d+\.\d+)"', text):
            if match.group(1) != expected_version:
                problems.append(
                    f"{rel_path}: version {match.group(1)}, expected {expected_version}"
                )

    module_text = (REPO_ROOT / USER_AGENT_MODULE).read_text()
    match = INTEGRATION_VERSION_RE.search(module_text)
    if not match:
        problems.append(f"{USER_AGENT_MODULE}: INTEGRATION_VERSION not found")
    elif match.group(2) != expected_version:
        problems.append(
            f"{USER_AGENT_MODULE}: INTEGRATION_VERSION is {match.group(2)}, "
            f"expected {expected_version}"
        )

    expected_watermark = WATERMARK_TEMPLATE.format(version=expected_version)
    stale_re = re.compile(r"agent-skills/\d+\.\d+\.\d+")
    for path in _tracked_text_files():
        for found in set(stale_re.findall(path.read_text())):
            if found != expected_watermark:
                problems.append(
                    f"{path.relative_to(REPO_ROOT)}: watermark {found}, "
                    f"expected {expected_watermark}"
                )

    return problems
