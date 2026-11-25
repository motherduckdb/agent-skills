# Execution Reference

Read this for example execution or an explicit structured-output request. These fixtures illustrate the pattern; they are not the user’s dataset or a prerequisite for ordinary work.

## Structured Output

If the caller explicitly asks for structured JSON, return raw JSON only with no Markdown fences or prose before/after it.
This is mainly for automated tests, regression checks, or downstream tooling that needs a stable machine-readable shape. Normal human-facing use of the skill can stay in prose unless JSON is explicitly requested.

Use this exact top-level shape when JSON is requested:

```json
{
  "summary": {},
  "assumptions": [],
  "implementation_plan": [],
  "validation_plan": [],
  "risks": []
}
```

## Runnable Artifact

- `artifacts/migration_validation_example.py` -- MotherDuck-backed Python example for source-vs-target validation and variance reporting
- `artifacts/migration_validation_example.ts` -- TypeScript companion artifact with the same validation output contract

From the repository root, run it with (for an installed skill, substitute its absolute artifact path):

```bash
uv run --with duckdb python skills/motherduck-migrate-to-motherduck/artifacts/migration_validation_example.py
```

Run the same validation flow against temporary MotherDuck databases:

```bash
MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK=1 \
uv run --with duckdb python skills/motherduck-migrate-to-motherduck/artifacts/migration_validation_example.py
```

From a checkout of this repository, validate the TypeScript companion artifacts:

```bash
uv run scripts/test_typescript_artifacts.py
```
