# Release Process

The canonical version is the top-level `version` in `package.json`. Every release keeps these surfaces aligned:

- `version` fields in the package, marketplace, plugin, and Gemini extension manifests
- `INTEGRATION_VERSION` in `scripts/_lib/motherduck_user_agent.py`
- `agent-skills/<version>` watermark strings across skills, plugins, commands, and docs

## Cutting a Release

1. Trigger the **Release** workflow (`workflow_dispatch`) with the new `X.Y.Z` version, or run the bump locally:

   ```bash
   uv run scripts/bump_version.py 2.3.0
   ```

   The workflow validates the bump and opens a `Release vX.Y.Z` PR. CI checks do not re-run on that PR (it is opened by `GITHUB_TOKEN`); the bump is validated inside the workflow before the PR is opened.

2. Add a `## X.Y.Z` section to `CHANGELOG.md` in that PR (or before it): customer-facing Highlights, Added, Changed, Fixed, and Upgrade notes. Write what an agent user notices, not repo internals. Check it with `uv run scripts/release_notes.py show X.Y.Z`.

3. Review and merge the release PR.

4. Tag the merge commit:

   ```bash
   git tag v2.3.0 && git push origin v2.3.0
   ```

   The tag triggers the publish job, which verifies every version surface matches the tag (`scripts/bump_version.py --check`), revalidates the catalog, and creates the GitHub release with the Gemini extension archive attached. The release body is the version's `CHANGELOG.md` section; without one, the job falls back to generated notes and logs a warning.

## Editing Published Notes

Edit the version's section in `CHANGELOG.md` and merge it. The **Release notes** workflow rewrites every published release that has a section. Run it by hand (`workflow_dispatch`) or locally with `uv run scripts/release_notes.py sync` (needs an authenticated `gh`).

## Verifying the Latest Version

Agents and tooling can resolve the latest published version without cloning:

```bash
curl -s https://api.github.com/repos/motherduckdb/agent-skills/releases/latest | jq -r .tag_name
```

Inside a checkout, `package.json` is the source of truth, and `uv run scripts/bump_version.py --check <version>` verifies repo-wide consistency.
