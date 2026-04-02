#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import sys

from _lib.codex import (
    CodexAppServer,
    CodexSupportError,
    IsolatedCodexHome,
    MARKETPLACE,
    plugin_name,
    require,
    require_codex_cli,
    source_skill_names,
)
from _lib.repo import ROOT


def main() -> int:
    require_codex_cli()

    current_plugin_name = plugin_name()
    namespaced_skill_names = sorted(
        f"{current_plugin_name}:{skill_name}" for skill_name in source_skill_names()
    )

    with IsolatedCodexHome(prefix="codex-plugin-home-") as (tmp_home, env):
        tmp_project = tmp_home / "scratch"
        tmp_project.mkdir()

        with CodexAppServer(env=env) as server:
            listed = server.call("plugin/list", {"cwds": [str(ROOT)], "forceRemoteSync": False})
            marketplaces = listed.get("marketplaces", [])
            require(marketplaces, "plugin/list returned no marketplaces")
            require(
                any(
                    item.get("name") == current_plugin_name
                    for marketplace in marketplaces
                    for item in marketplace.get("plugins", [])
                ),
                "plugin/list did not expose the MotherDuck plugin",
            )

            plugin = server.call(
                "plugin/read",
                {"marketplacePath": str(MARKETPLACE), "pluginName": current_plugin_name},
            ).get("plugin", {})
            plugin_skills = sorted(skill.get("name") for skill in plugin.get("skills", []))
            require(
                plugin_skills == namespaced_skill_names,
                f"plugin/read skill mismatch: expected {namespaced_skill_names}, found {plugin_skills}",
            )

            server.call(
                "plugin/install",
                {"marketplacePath": str(MARKETPLACE), "pluginName": current_plugin_name},
            )

            installed = server.call("plugin/list", {"cwds": [str(ROOT)], "forceRemoteSync": False})
            installed_plugin = next(
                item
                for marketplace in installed.get("marketplaces", [])
                for item in marketplace.get("plugins", [])
                if item.get("name") == current_plugin_name
            )
            require(installed_plugin.get("installed") is True, "plugin was not marked installed after plugin/install")
            require(installed_plugin.get("enabled") is True, "plugin was not marked enabled after plugin/install")

            skills_result = server.call("skills/list", {"cwds": [str(tmp_project)], "forceReload": True})
            cwd_skill_sets = skills_result.get("data", [])
            require(cwd_skill_sets, "skills/list returned no cwd entries")
            resolved_skill_names = sorted(
                skill.get("name")
                for entry in cwd_skill_sets
                for skill in entry.get("skills", [])
                if skill.get("name") in set(namespaced_skill_names)
            )
            require(
                resolved_skill_names == namespaced_skill_names,
                f"skills/list did not surface installed plugin skills: expected {namespaced_skill_names}, found {resolved_skill_names}",
            )

    print(f"Codex plugin smoke test passed for {current_plugin_name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CodexSupportError as exc:
        print(f"Codex plugin smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
