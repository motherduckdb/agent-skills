from __future__ import annotations

from pathlib import Path

from _lib.repo import ROOT


CLAUDE_PACKAGED_PLUGIN = ROOT / "plugins" / "motherduck-skills-claude"
CLAUDE_PACKAGED_PLUGIN_MANIFEST = CLAUDE_PACKAGED_PLUGIN / ".claude-plugin" / "plugin.json"
CLAUDE_PACKAGED_PLUGIN_SKILLS = CLAUDE_PACKAGED_PLUGIN / "skills"

# All current catalog skills are intended to be directly invokable in Claude.
CLAUDE_SKILL_ARGUMENT_HINTS: dict[str, str] = {
    "motherduck-build-cfa-app": "[app-or-tenant-scenario]",
    "motherduck-build-dashboard": "[dashboard-goal]",
    "motherduck-build-data-pipeline": "[pipeline-goal]",
    "motherduck-connect": "[app-or-runtime]",
    "motherduck-create-dive": "[dive-goal]",
    "motherduck-duckdb-sql": "[syntax-or-error]",
    "motherduck-ducklake": "[storage-scenario]",
    "motherduck-enable-self-serve-analytics": "[team-or-rollout-scenario]",
    "motherduck-explore": "[database-or-workspace]",
    "motherduck-load-data": "[source-and-target]",
    "motherduck-migrate-to-motherduck": "[source-system-or-migration-goal]",
    "motherduck-model-data": "[table-or-model-goal]",
    "motherduck-partner-delivery": "[client-delivery-scenario]",
    "motherduck-pricing-roi": "[workload-or-pricing-question]",
    "motherduck-query": "[query-or-task]",
    "motherduck-security-governance": "[security-question]",
    "motherduck-share-data": "[database-and-audience]",
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
