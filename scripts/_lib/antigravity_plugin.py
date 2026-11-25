"""Shared paths and helpers for the packaged Google Antigravity plugin.

The package under plugins/motherduck-skills-antigravity is a native Antigravity
plugin: plugin.json, mcp_config.json, rules/AGENTS.md, and assets/logo.svg sit
at the plugin root and are edited in place, and skills/ is a generated copy of
the repo-level skills directory.
"""

from __future__ import annotations

from pathlib import Path

from _lib.repo import ROOT, file_digest, iter_files

PLUGIN_SCHEMA = "https://antigravity.google/schemas/v1/plugin.json"
MCP_SERVER_URL = "https://api.motherduck.com/mcp"
# The plugin shares its name with the MCP server it carries.
PLUGIN_NAME = "motherduck"

ALLOWED_PLUGIN_FIELDS = {
    "$schema",
    "name",
    "displayName",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "logo",
    "category",
    "keywords",
    "suggestedPrompts",
    "disabled",
}

SOURCE_SKILLS = ROOT / "skills"
PACKAGED_ROOT = ROOT / "plugins" / "motherduck-skills-antigravity"
PACKAGED_PLUGIN = PACKAGED_ROOT / "plugin.json"
PACKAGED_MCP = PACKAGED_ROOT / "mcp_config.json"
PACKAGED_RULES = PACKAGED_ROOT / "rules" / "AGENTS.md"
PACKAGED_SKILLS = PACKAGED_ROOT / "skills"


def iter_skill_files(skills_root: Path) -> dict[Path, Path]:
    """Files that belong to a skill directory, keyed by path relative to skills_root.

    Antigravity loads skills from skills/<name>/SKILL.md, so top-level files
    such as the repo-only catalog.json are left out of the package.
    """
    files: dict[Path, Path] = {}
    for path in iter_files(skills_root):
        relative_path = path.relative_to(skills_root)
        if len(relative_path.parts) > 1:
            files[relative_path] = path
    return files


def collect_skill_digests(skills_root: Path) -> dict[Path, str]:
    if not skills_root.exists():
        raise FileNotFoundError(f"Missing required directory: {skills_root}")
    return {relative: file_digest(path) for relative, path in iter_skill_files(skills_root).items()}
