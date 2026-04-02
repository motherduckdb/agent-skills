#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

from _lib.gemini import (
    GEMINI_COMMANDS,
    GEMINI_CONTEXT,
    GEMINI_CONTEXT_FILE_NAME,
    GEMINI_EXTENSION,
    GEMINI_PLAN_DIRECTORY,
    GEMINI_REQUIRED_COMMANDS,
)
from _lib.repo import ROOT, read_json_file

SKILLS_DIR = ROOT / "skills"
SKILL_CATALOG = SKILLS_DIR / "catalog.json"
README = ROOT / "README.md"
CLAUDE_CONTEXT = ROOT / "CLAUDE.md"
CLAUDE_PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
CODEX_PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
CODEX_PACKAGED_PLUGIN = ROOT / "plugins" / "motherduck-skills"

LAYERS = {"utility": 0, "workflow": 1, "use-case": 2}
GEMINI_CATALOG_HEADINGS = {
    "utility": "### Utility",
    "workflow": "### Workflow",
    "use-case": "### Use-case",
}


class ValidationError(Exception):
    pass


def parse_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValidationError(f"{path}: missing opening frontmatter delimiter")

    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValidationError(f"{path}: missing closing frontmatter delimiter")

    frontmatter = text[4:end].splitlines()

    data: dict[str, object] = {}
    allowed_keys = {"name", "description", "license"}

    for raw_line in frontmatter:
        if not raw_line.strip():
            continue

        if raw_line.startswith("  "):
            raise ValidationError(f"{path}: nested frontmatter is not supported; move repo-only metadata elsewhere")

        key, _, value = raw_line.partition(":")
        key = key.strip()
        value = value.strip()
        if key not in allowed_keys:
            raise ValidationError(
                f"{path}: unsupported frontmatter key {key!r}; keep SKILL.md frontmatter portable"
            )
        data[key] = value

    if "name" not in data:
        raise ValidationError(f"{path}: missing name")
    if "description" not in data:
        raise ValidationError(f"{path}: missing description")
    return data


def read_skill_catalog() -> dict[str, dict[str, object]]:
    if not SKILL_CATALOG.exists():
        raise ValidationError(f"Missing required skill catalog: {SKILL_CATALOG}")

    payload = json.loads(SKILL_CATALOG.read_text())
    if not isinstance(payload, dict) or not payload:
        raise ValidationError(f"{SKILL_CATALOG}: expected a non-empty object")

    catalog: dict[str, dict[str, object]] = {}
    for skill_name, entry in payload.items():
        if not isinstance(entry, dict):
            raise ValidationError(f"{SKILL_CATALOG}: entry for {skill_name!r} must be an object")
        name = entry.get("name")
        description = entry.get("description")
        layer = entry.get("layer")
        depends_on = entry.get("depends_on")
        references = entry.get("references")
        artifacts = entry.get("artifacts")
        source_docs = entry.get("source_docs")
        needs_live_discovery = entry.get("needs_live_discovery")
        if name != skill_name:
            raise ValidationError(
                f"{SKILL_CATALOG}: entry name mismatch for {skill_name!r}: {name!r}"
            )
        if not isinstance(description, str) or not description.strip():
            raise ValidationError(f"{SKILL_CATALOG}: description for {skill_name!r} must be a non-empty string")
        if layer not in LAYERS:
            raise ValidationError(f"{SKILL_CATALOG}: invalid layer for {skill_name!r}: {layer!r}")
        if not isinstance(depends_on, list) or not all(isinstance(dep, str) for dep in depends_on):
            raise ValidationError(f"{SKILL_CATALOG}: depends_on for {skill_name!r} must be a list of strings")
        if not isinstance(references, list) or not all(isinstance(path, str) for path in references):
            raise ValidationError(f"{SKILL_CATALOG}: references for {skill_name!r} must be a list of strings")
        if not isinstance(artifacts, list) or not all(isinstance(path, str) for path in artifacts):
            raise ValidationError(f"{SKILL_CATALOG}: artifacts for {skill_name!r} must be a list of strings")
        if not isinstance(source_docs, list) or not all(isinstance(url, str) for url in source_docs):
            raise ValidationError(f"{SKILL_CATALOG}: source_docs for {skill_name!r} must be a list of strings")
        if not isinstance(needs_live_discovery, bool):
            raise ValidationError(
                f"{SKILL_CATALOG}: needs_live_discovery for {skill_name!r} must be a boolean"
            )
        catalog[skill_name] = {
            "description": description,
            "layer": layer,
            "depends_on": depends_on,
            "references": references,
            "artifacts": artifacts,
            "source_docs": source_docs,
            "needs_live_discovery": needs_live_discovery,
        }

    return catalog


def validate_skill_paths(skill_name: str, path_strings: list[str], field_name: str) -> None:
    skill_root = SKILLS_DIR / skill_name
    for relative_path in path_strings:
        candidate = skill_root / relative_path
        if not candidate.exists():
            raise ValidationError(
                f"{SKILL_CATALOG}: {field_name} entry for {skill_name!r} does not exist: {relative_path}"
            )


def validate_live_discovery_language(skill_name: str, text: str) -> None:
    required_heading = "## Start Here: Is a MotherDuck Server Active?"
    required_phrases = [
        "remote MotherDuck MCP server",
        "local MotherDuck server",
    ]
    if required_heading not in text:
        raise ValidationError(
            f"{skill_name}: skills with needs_live_discovery=true must include the '{required_heading}' section"
        )
    for phrase in required_phrases:
        if phrase not in text:
            raise ValidationError(
                f"{skill_name}: live-discovery skill is missing required phrase {phrase!r}"
            )


def read_readme_catalog_skills() -> list[str]:
    text = README.read_text()
    found = re.findall(r"^\| `([a-z0-9-]+)` \| (?:Utility|Workflow|Use-case) \|", text, re.MULTILINE)
    if not found:
        raise ValidationError("README.md: could not parse skill catalog table")
    return found


def read_claude_context_skills() -> list[str]:
    text = CLAUDE_CONTEXT.read_text()
    found = re.findall(r"^\| ([a-z0-9-]+) \| `\/[a-z0-9-]+` \|", text, re.MULTILINE)
    if not found:
        raise ValidationError("CLAUDE.md: could not parse skill catalog table")
    return found


def read_gemini_context_skills() -> dict[str, list[str]]:
    text = GEMINI_CONTEXT.read_text()
    found_by_layer: dict[str, list[str]] = {}
    ordered_layers = list(GEMINI_CATALOG_HEADINGS.items())

    for index, (layer, heading) in enumerate(ordered_layers):
        start = text.find(heading)
        if start == -1:
            raise ValidationError(f"{GEMINI_CONTEXT}: missing catalog heading {heading!r}")

        section_start = text.find("\n", start)
        if section_start == -1:
            raise ValidationError(f"{GEMINI_CONTEXT}: malformed section for {heading!r}")
        section_start += 1

        section_end = len(text)
        for _, next_heading in ordered_layers[index + 1 :]:
            next_start = text.find(next_heading, section_start)
            if next_start != -1:
                section_end = next_start
                break

        section = text[section_start:section_end]
        found = re.findall(r"^- `([a-z0-9-]+)`: ", section, re.MULTILINE)
        if not found:
            raise ValidationError(f"{GEMINI_CONTEXT}: could not parse skills under {heading!r}")
        found_by_layer[layer] = found

    return found_by_layer


def validate_claude_plugin() -> str:
    payload = read_json_file(CLAUDE_PLUGIN)
    plugin_name = payload.get("name")
    if not plugin_name:
        raise ValidationError(f"{CLAUDE_PLUGIN}: missing name")

    skills_path = payload.get("skills")
    if skills_path != "./skills/":
        raise ValidationError(f"{CLAUDE_PLUGIN}: expected skills to be './skills/', found {skills_path!r}")

    resolved_skills_dir = (ROOT / skills_path).resolve()
    if resolved_skills_dir != SKILLS_DIR.resolve():
        raise ValidationError(
            f"{CLAUDE_PLUGIN}: skills path does not resolve to repo skills directory: {resolved_skills_dir}"
        )

    return plugin_name


def validate_claude_marketplace(expected_plugin_name: str) -> None:
    marketplace_path = ROOT / ".claude-plugin" / "marketplace.json"
    if not marketplace_path.exists():
        raise ValidationError(f"Missing required Claude marketplace manifest: {marketplace_path}")

    payload = read_json_file(marketplace_path)
    if not payload.get("name"):
        raise ValidationError(f"{marketplace_path}: missing name")

    owner = payload.get("owner")
    if not isinstance(owner, dict) or not owner.get("name"):
        raise ValidationError(f"{marketplace_path}: owner.name is required")

    plugins = payload.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        raise ValidationError(f"{marketplace_path}: plugins must be a non-empty list")

    entry = next((plugin for plugin in plugins if plugin.get("name") == expected_plugin_name), None)
    if entry is None:
        raise ValidationError(f"{marketplace_path}: missing plugin entry for {expected_plugin_name!r}")

    source = entry.get("source")
    if not isinstance(source, str) or not source.startswith("./"):
        raise ValidationError(f"{marketplace_path}: plugin source must be a relative path starting with './'")

    marketplace_root = marketplace_path.parents[1]
    resolved_plugin_root = (marketplace_root / source).resolve()
    if resolved_plugin_root != ROOT.resolve():
        raise ValidationError(
            f"{marketplace_path}: plugin source must resolve to repo root, found {resolved_plugin_root}"
        )
    if not (resolved_plugin_root / ".claude-plugin" / "plugin.json").exists():
        raise ValidationError(
            f"{marketplace_path}: plugin source does not point at a valid Claude plugin root"
        )


def validate_codex_plugin(skills: list[str]) -> str:
    if not CODEX_PLUGIN.exists():
        raise ValidationError(f"Missing required Codex plugin manifest: {CODEX_PLUGIN}")

    payload = read_json_file(CODEX_PLUGIN)
    plugin_name = payload.get("name")
    if not plugin_name:
        raise ValidationError(f"{CODEX_PLUGIN}: missing name")
    if not payload.get("version"):
        raise ValidationError(f"{CODEX_PLUGIN}: missing version")
    if not payload.get("description"):
        raise ValidationError(f"{CODEX_PLUGIN}: missing description")

    skills_path = payload.get("skills")
    if skills_path != "./skills/":
        raise ValidationError(f"{CODEX_PLUGIN}: expected skills to be './skills/', found {skills_path!r}")

    resolved_skills_dir = (ROOT / skills_path).resolve()
    if resolved_skills_dir != SKILLS_DIR.resolve():
        raise ValidationError(
            f"{CODEX_PLUGIN}: skills path does not resolve to repo skills directory: {resolved_skills_dir}"
        )

    interface = payload.get("interface")
    if not isinstance(interface, dict) or not interface.get("displayName"):
        raise ValidationError(f"{CODEX_PLUGIN}: missing interface.displayName")

    codex_skills = sorted(p.parent.name for p in resolved_skills_dir.glob("*/SKILL.md"))
    if codex_skills != skills:
        raise ValidationError(
            f"{CODEX_PLUGIN}: skills directory mismatch\nexpected: {skills}\nfound:    {codex_skills}"
        )

    return plugin_name


def validate_codex_marketplace(expected_plugin_name: str) -> None:
    if not CODEX_MARKETPLACE.exists():
        raise ValidationError(f"Missing required Codex marketplace: {CODEX_MARKETPLACE}")

    payload = read_json_file(CODEX_MARKETPLACE)
    if not payload.get("name"):
        raise ValidationError(f"{CODEX_MARKETPLACE}: missing top-level name")

    interface = payload.get("interface")
    if not isinstance(interface, dict) or not interface.get("displayName"):
        raise ValidationError(f"{CODEX_MARKETPLACE}: missing interface.displayName")

    plugins = payload.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        raise ValidationError(f"{CODEX_MARKETPLACE}: plugins must be a non-empty list")

    entry = next((plugin for plugin in plugins if plugin.get("name") == expected_plugin_name), None)
    if entry is None:
        raise ValidationError(f"{CODEX_MARKETPLACE}: missing plugin entry for {expected_plugin_name!r}")

    source = entry.get("source")
    if not isinstance(source, dict) or source.get("source") != "local":
        raise ValidationError(f"{CODEX_MARKETPLACE}: plugin source must be local")

    source_path = source.get("path")
    if not isinstance(source_path, str) or not source_path.startswith("./"):
        raise ValidationError(f"{CODEX_MARKETPLACE}: source.path must start with './'")

    marketplace_root = CODEX_MARKETPLACE.parents[2]
    resolved_plugin_root = (marketplace_root / source_path).resolve()
    if resolved_plugin_root != CODEX_PACKAGED_PLUGIN.resolve():
        raise ValidationError(
            f"{CODEX_MARKETPLACE}: source.path must resolve to {CODEX_PACKAGED_PLUGIN}, found {resolved_plugin_root}"
        )
    if not (resolved_plugin_root / ".codex-plugin" / "plugin.json").exists():
        raise ValidationError(f"{CODEX_MARKETPLACE}: source.path does not point at a valid Codex plugin root")

    policy = entry.get("policy")
    if not isinstance(policy, dict):
        raise ValidationError(f"{CODEX_MARKETPLACE}: plugin policy is required")
    if "installation" not in policy or "authentication" not in policy:
        raise ValidationError(f"{CODEX_MARKETPLACE}: policy.installation and policy.authentication are required")
    if "category" not in entry:
        raise ValidationError(f"{CODEX_MARKETPLACE}: category is required on each plugin entry")


def validate_command_file(path: Path) -> None:
    try:
        payload = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f"{path}: invalid TOML: {exc}") from exc

    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValidationError(f"{path}: command must define a non-empty prompt")

    description = payload.get("description")
    if description is not None and (not isinstance(description, str) or not description.strip()):
        raise ValidationError(f"{path}: description must be a non-empty string when provided")


def validate_gemini_extension() -> str:
    if not GEMINI_EXTENSION.exists():
        raise ValidationError(f"Missing required Gemini extension manifest: {GEMINI_EXTENSION}")

    payload = read_json_file(GEMINI_EXTENSION)
    extension_name = payload.get("name")
    if not extension_name:
        raise ValidationError(f"{GEMINI_EXTENSION}: missing name")
    if not payload.get("version"):
        raise ValidationError(f"{GEMINI_EXTENSION}: missing version")
    if not payload.get("description"):
        raise ValidationError(f"{GEMINI_EXTENSION}: missing description")

    context_file_name = payload.get("contextFileName")
    if context_file_name != GEMINI_CONTEXT_FILE_NAME:
        raise ValidationError(
            f"{GEMINI_EXTENSION}: expected contextFileName to be {GEMINI_CONTEXT_FILE_NAME!r}, found {context_file_name!r}"
        )
    if not GEMINI_CONTEXT.exists():
        raise ValidationError(f"{GEMINI_EXTENSION}: referenced context file is missing: {GEMINI_CONTEXT}")

    plan = payload.get("plan")
    if not isinstance(plan, dict) or plan.get("directory") != GEMINI_PLAN_DIRECTORY:
        raise ValidationError(
            f"{GEMINI_EXTENSION}: expected plan.directory to be {GEMINI_PLAN_DIRECTORY!r}"
        )

    if not GEMINI_COMMANDS.exists():
        raise ValidationError(f"Missing required Gemini commands directory: {GEMINI_COMMANDS}")
    for command_path in GEMINI_REQUIRED_COMMANDS:
        if not command_path.exists():
            raise ValidationError(f"Missing required Gemini discovery command: {command_path}")
    for command_path in sorted(GEMINI_COMMANDS.rglob("*.toml")):
        validate_command_file(command_path)

    return extension_name


def main() -> int:
    skills = sorted(p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md"))
    if not skills:
        raise ValidationError("No skills found")

    catalog = read_skill_catalog()
    if sorted(catalog) != skills:
        raise ValidationError(
            f"{SKILL_CATALOG}: skill catalog mismatch\nexpected: {skills}\nfound:    {sorted(catalog)}"
        )

    parsed: dict[str, dict[str, object]] = {}
    for skill_name in skills:
        path = SKILLS_DIR / skill_name / "SKILL.md"
        data = parse_frontmatter(path)
        if data["name"] != skill_name:
            raise ValidationError(f"{path}: name {data['name']!r} does not match directory {skill_name!r}")
        catalog_entry = catalog[skill_name]
        if data["description"] != catalog_entry["description"]:
            raise ValidationError(
                f"{path}: description does not match skills/catalog.json for {skill_name!r}"
            )
        skill_text = path.read_text()
        validate_skill_paths(skill_name, catalog_entry["references"], "references")
        validate_skill_paths(skill_name, catalog_entry["artifacts"], "artifacts")
        if catalog_entry["needs_live_discovery"]:
            if catalog_entry["layer"] != "use-case":
                raise ValidationError(
                    f"{skill_name}: needs_live_discovery=true is only valid for use-case skills"
                )
            validate_live_discovery_language(skill_name, skill_text)
        parsed[skill_name] = {
            **data,
            "layer": catalog_entry["layer"],
            "depends_on": catalog_entry["depends_on"],
        }

    for skill_name, data in parsed.items():
        layer = data["layer"]
        depends_on = data["depends_on"]
        if not isinstance(depends_on, list):
            raise ValidationError(f"{skill_name}: depends_on must be a list")

        if layer == "utility" and depends_on:
            raise ValidationError(f"{skill_name}: utility skills may not depend on other skills")

        for dep in depends_on:
            if dep not in parsed:
                raise ValidationError(f"{skill_name}: unknown dependency {dep!r}")
            dep_layer = parsed[dep]["layer"]
            if layer == "workflow" and dep_layer != "utility":
                raise ValidationError(
                    f"{skill_name}: workflow skills may depend only on utility skills, found {dep} ({dep_layer})"
                )
            if layer == "use-case" and dep_layer == "use-case":
                raise ValidationError(
                    f"{skill_name}: use-case skills may not depend on other use-case skills"
                )

    readme_skills = read_readme_catalog_skills()
    if sorted(readme_skills) != skills:
        raise ValidationError(
            f"README.md: skill catalog mismatch\nexpected: {skills}\nfound:    {readme_skills}"
        )

    claude_skills = read_claude_context_skills()
    if sorted(claude_skills) != skills:
        raise ValidationError(
            f"CLAUDE.md: skill catalog mismatch\nexpected: {skills}\nfound:    {claude_skills}"
        )

    gemini_skills = read_gemini_context_skills()
    for layer in LAYERS:
        expected = sorted(skill_name for skill_name, entry in catalog.items() if entry["layer"] == layer)
        found = sorted(gemini_skills.get(layer, []))
        if found != expected:
            raise ValidationError(
                f"{GEMINI_CONTEXT}: skill catalog mismatch for {layer}\nexpected: {expected}\nfound:    {found}"
            )

    if not CLAUDE_PLUGIN.exists():
        raise ValidationError(f"Missing required Claude plugin manifest: {CLAUDE_PLUGIN}")
    claude_plugin_name = validate_claude_plugin()
    validate_claude_marketplace(claude_plugin_name)

    codex_plugin_name = validate_codex_plugin(skills)
    validate_codex_marketplace(codex_plugin_name)
    validate_gemini_extension()

    print(f"Validated {len(skills)} skills successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
