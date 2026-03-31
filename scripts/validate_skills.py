#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
README = ROOT / "README.md"
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
CODEX_PLUGIN = ROOT / ".codex-plugin" / "plugin.json"

LAYERS = {"utility": 0, "workflow": 1, "use-case": 2}


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

    name = None
    description = None
    metadata: dict[str, object] = {}
    in_metadata = False
    in_depends_on = False
    depends_on: list[str] = []

    for raw_line in frontmatter:
        if not raw_line.strip():
            continue

        if raw_line.startswith("metadata:"):
            in_metadata = True
            in_depends_on = False
            continue

        if not raw_line.startswith("  "):
            in_metadata = False
            in_depends_on = False
            key, _, value = raw_line.partition(":")
            value = value.strip()
            if key == "name":
                name = value
            elif key == "description":
                description = value
            continue

        if not in_metadata:
            continue

        if raw_line.startswith("  depends_on:"):
            in_depends_on = True
            inline = raw_line.split(":", 1)[1].strip()
            if inline == "[]":
                depends_on = []
                in_depends_on = False
            metadata["depends_on"] = depends_on
            continue

        if in_depends_on:
            match = re.match(r"^\s*-\s+([a-z0-9-]+)\s*$", raw_line)
            if not match:
                raise ValidationError(f"{path}: invalid depends_on entry: {raw_line!r}")
            depends_on.append(match.group(1))
            continue

        key, _, value = raw_line.strip().partition(":")
        metadata[key] = value.strip().strip('"')

    if not name:
        raise ValidationError(f"{path}: missing name")
    if not description:
        raise ValidationError(f"{path}: missing description")
    if "layer" not in metadata:
        raise ValidationError(f"{path}: missing metadata.layer")
    if "depends_on" not in metadata:
        raise ValidationError(f"{path}: missing metadata.depends_on")

    return {
        "name": name,
        "description": description,
        "metadata": metadata,
    }


def read_catalog_skills() -> list[str]:
    text = README.read_text()
    found = re.findall(r"^\| `([a-z0-9-]+)` \| (?:Utility|Workflow|Use-case) \|", text, re.MULTILINE)
    if not found:
        raise ValidationError("README.md: could not parse skill catalog table")
    return found


def read_plugin_skills() -> list[str]:
    payload = json.loads(PLUGIN.read_text())
    return [entry.removeprefix("skills/") for entry in payload["skills"]]


def main() -> int:
    skills = sorted(p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md"))
    if not skills:
        raise ValidationError("No skills found")

    parsed: dict[str, dict[str, object]] = {}
    for skill_name in skills:
        path = SKILLS_DIR / skill_name / "SKILL.md"
        data = parse_frontmatter(path)
        if data["name"] != skill_name:
            raise ValidationError(f"{path}: name {data['name']!r} does not match directory {skill_name!r}")
        layer = data["metadata"]["layer"]
        if layer not in LAYERS:
            raise ValidationError(f"{path}: invalid layer {layer!r}")
        parsed[skill_name] = data

    for skill_name, data in parsed.items():
        layer = data["metadata"]["layer"]
        depends_on = data["metadata"]["depends_on"]
        if not isinstance(depends_on, list):
            raise ValidationError(f"{skill_name}: depends_on must be a list")

        if layer == "utility" and depends_on:
            raise ValidationError(f"{skill_name}: utility skills may not depend on other skills")

        for dep in depends_on:
            if dep not in parsed:
                raise ValidationError(f"{skill_name}: unknown dependency {dep!r}")
            dep_layer = parsed[dep]["metadata"]["layer"]
            if layer == "workflow" and dep_layer != "utility":
                raise ValidationError(
                    f"{skill_name}: workflow skills may depend only on utility skills, found {dep} ({dep_layer})"
                )
            if layer == "use-case" and dep_layer == "use-case":
                raise ValidationError(
                    f"{skill_name}: use-case skills may not depend on other use-case skills"
                )

    catalog_skills = read_catalog_skills()
    if sorted(catalog_skills) != skills:
        raise ValidationError(
            f"README.md: skill catalog mismatch\nexpected: {skills}\nfound:    {catalog_skills}"
        )

    if PLUGIN.exists():
        plugin_skills = read_plugin_skills()
        if sorted(plugin_skills) != skills:
            raise ValidationError(
                f".claude-plugin/plugin.json: skill list mismatch\nexpected: {skills}\nfound:    {plugin_skills}"
            )
    else:
        print(f"Skipping plugin validation: {PLUGIN} not found")

    if CODEX_PLUGIN.exists():
        codex = json.loads(CODEX_PLUGIN.read_text())
        for field in ("name", "version", "description", "skills"):
            if field not in codex:
                raise ValidationError(f".codex-plugin/plugin.json: missing required field {field!r}")
        skills_path = codex["skills"]
        resolved = (CODEX_PLUGIN.parent.parent / skills_path.lstrip("./")).resolve()
        if resolved != SKILLS_DIR.resolve():
            raise ValidationError(
                f".codex-plugin/plugin.json: skills path {skills_path!r} does not resolve to {SKILLS_DIR}"
            )
        print("Codex plugin manifest validated.")
    else:
        print(f"Skipping Codex plugin validation: {CODEX_PLUGIN} not found")

    print(f"Validated {len(skills)} skills successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
