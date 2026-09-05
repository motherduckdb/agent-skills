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

- `artifacts/client_delivery_example.py` -- MotherDuck-backed Python example showing one database namespace per client and a simple validation pass across client environments
- `artifacts/client_delivery_example.ts` -- TypeScript companion artifact with the same delivery output contract

From the repository root, run it with (for an installed skill, substitute its absolute artifact path):

```bash
uv run --with duckdb python skills/motherduck-partner-delivery/artifacts/client_delivery_example.py
```

Run the same artifact against temporary MotherDuck databases:

```bash
MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK=1 \
uv run --with duckdb python skills/motherduck-partner-delivery/artifacts/client_delivery_example.py
```

From a checkout of this repository, validate the TypeScript companion artifacts:

```bash
uv run scripts/test_typescript_artifacts.py
```
