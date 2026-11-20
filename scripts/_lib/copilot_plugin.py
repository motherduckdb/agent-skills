"""Shared paths and helpers for the packaged GitHub Copilot plugin.

The package under plugins/motherduck-skills-copilot is an Agent Plugins 1.0
plugin: plugin.json and mcp.json sit at the plugin root and are edited in
place, and skills/ is a generated copy of the repo-level skills directory.
"""

from __future__ import annotations

from pathlib import Path

from _lib.repo import ROOT, file_digest, iter_files

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
MCP_SERVER_URL = "https://api.motherduck.com/mcp"
# The plugin shares its name with the MCP server it carries.
PLUGIN_NAME = "motherduck"

# Agent Plugins 1.0 uses a closed plugin.json schema; other fields are ignored.
ALLOWED_PLUGIN_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}

SOURCE_SKILLS = ROOT / "skills"
PACKAGED_ROOT = ROOT / "plugins" / "motherduck-skills-copilot"
PACKAGED_PLUGIN = PACKAGED_ROOT / "plugin.json"
PACKAGED_MCP = PACKAGED_ROOT / "mcp.json"
PACKAGED_SKILLS = PACKAGED_ROOT / "skills"
MARKETPLACE = ROOT / ".github" / "plugin" / "marketplace.json"


def iter_skill_files(skills_root: Path) -> dict[Path, Path]:
    """Files that belong to a skill directory, keyed by path relative to skills_root.

    Agent Plugins 1.0 defines skills as immediate subdirectories, so top-level
    files such as the repo-only catalog.json are left out of the package.
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
