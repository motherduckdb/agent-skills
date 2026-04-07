from __future__ import annotations

from pathlib import Path

from _lib.repo import ROOT


CLAUDE_PACKAGED_PLUGIN = ROOT / "plugins" / "motherduck-skills-claude"
CLAUDE_PACKAGED_PLUGIN_MANIFEST = CLAUDE_PACKAGED_PLUGIN / ".claude-plugin" / "plugin.json"
CLAUDE_PACKAGED_PLUGIN_SKILLS = CLAUDE_PACKAGED_PLUGIN / "skills"

# All current catalog skills are intended to be directly invokable in Claude.
CLAUDE_SKILL_ARGUMENT_HINTS: dict[str, str] = {
    "build-cfa-app": "[app-or-tenant-scenario]",
    "build-dashboard": "[dashboard-goal]",
    "build-data-pipeline": "[pipeline-goal]",
    "connect": "[app-or-runtime]",
    "create-dive": "[dive-goal]",
    "duckdb-sql": "[syntax-or-error]",
    "ducklake": "[storage-scenario]",
    "enable-self-serve-analytics": "[team-or-rollout-scenario]",
    "explore": "[database-or-workspace]",
    "load-data": "[source-and-target]",
    "migrate-to-motherduck": "[source-system-or-migration-goal]",
    "model-data": "[table-or-model-goal]",
    "partner-delivery": "[client-delivery-scenario]",
    "pricing-roi": "[workload-or-pricing-question]",
    "query": "[query-or-task]",
    "security-governance": "[security-question]",
    "share-data": "[database-and-audience]",
}


def inject_argument_hint(skill_name: str, text: str) -> str:
    hint = CLAUDE_SKILL_ARGUMENT_HINTS.get(skill_name)
    if hint is None:
        return text

    if not text.startswith("---\n"):
        return text

    end = text.find("\n---\n", 4)
    if end == -1:
        return text

    frontmatter = text[4:end].splitlines()
    rewritten: list[str] = []
    inserted = False
    for line in frontmatter:
        if line.startswith("argument-hint:"):
            rewritten.append(f"argument-hint: {hint}")
            inserted = True
            continue
        rewritten.append(line)
        if line.startswith("description:") and not inserted:
            rewritten.append(f"argument-hint: {hint}")
            inserted = True

    if not inserted:
        rewritten.append(f"argument-hint: {hint}")

    return "---\n" + "\n".join(rewritten) + "\n---\n" + text[end + 5 :]
