# AI Functions in MotherDuck SQL

MotherDuck runs model calls from SQL. Each function call is a billable request per row (or per batch), measured in AI Units and capped by the organization's AI session cap. Verify current models, regions, and rates against the MotherDuck AI function docs before quoting them.

## Contents

| Section | Covers |
| --- | --- |
| Pick the Function | `prompt_jev` vs `prompt` vs `embedding` |
| `prompt_jev` | Question types, return shapes, multi-question calls, images, batching |
| `prompt` | Models, `reasoning_effort`, typed and structured output |
| `embedding` | Vector output and similarity search |
| Cost and Reliability Rules | Sampling, materializing, `NULL` reruns, session cap |
| Data Handling | Where each function sends data and how Admins turn it off |

## Pick the Function

| Need | Use |
| --- | --- |
| Yes/no probability, one label from a fixed set, several independent labels, an ordinal score, or an object's location in an image | `prompt_jev()` |
| Free text, summaries, open-ended extraction, or a model-filled schema | `prompt()` |
| Vectors for semantic search or clustering | `embedding()` |

`prompt_jev()` never returns free text. It returns typed, calibrated answers, bills input tokens only, and batches text rows, so it is usually much cheaper than `prompt()` for classification at scale.

## `prompt_jev`

```sql
-- yes/no: DOUBLE probability between 0 and 1
SELECT ticket_id,
       prompt_jev(body, 'The customer asks to cancel their subscription') AS p_cancel
FROM "support"."main"."tickets"
LIMIT 20;

-- one label: STRUCT(choice, probabilities, confidence)
SELECT ticket_id,
       prompt_jev(body, 'Primary product area', choice := ['billing', 'auth', 'dives', 'other']).choice AS area
FROM "support"."main"."tickets";

-- several questions, input sent once: STRUCT with one field per question
SELECT ticket_id,
       prompt_jev(body, questions := {
         urgent: {type: 'noul', instructions: 'The customer reports a production outage'},
         area:   {type: 'choice', instructions: 'Primary product area', criteria: ['billing', 'auth', 'dives', 'other']}
       }) AS triage
FROM "support"."main"."tickets";
```

- Question types are mutually exclusive named arguments: `noul` (the default when none is given), `choice` (2 to 255 labels), `multiple_choice` (labels judged independently; returns `choices` above 0.5, which can be empty), `score` (2 to 10 ordered levels; `score` runs from 0 to levels minus 1), and `box` (image only).
- Labels can be `VARCHAR[]` or `STRUCT(label, description)[]`; descriptions guide the model without changing the returned value.
- `choice` probabilities are sorted by label. Read them by `value`, not position.
- `multiple_choice` is MotherDuck shorthand that expands into one yes/no question per label, so it costs more and cannot be used inside `questions`.
- Only `input` varies per row. `instructions`, labels, and `questions` must be constants.
- Images: pass PNG or JPEG bytes as a `BLOB` (a bare BLOB is treated as JPEG) or a `{name, content, format}` struct or list of structs; load files or URLs with `read_blob`. Each side must be 280 to 1,568 px and upright (EXIF rotation is ignored); out-of-limit images return `NULL`. `box` always returns coordinates, so pair it with a `noul` presence check.
- Batching: text rows go 32 per request by default and shrink automatically under the token limit. Setting `batch_size` (1 to 64) turns that adjustment off, and an oversized batch returns `NULL` for every row in it. `batch_size := 1` gives strict per-row isolation at higher cost. Images are never batched.
- There is no model parameter. Confidence is not correctness: evaluate on labelled examples before automating a decision.

## `prompt`

```sql
SELECT review_id,
       prompt('Extract the product and the main complaint: ' || review_text,
              model := 'gpt-6-luna',
              struct := {product: 'VARCHAR', complaint: 'VARCHAR'}) AS parsed
FROM "shop"."main"."reviews"
LIMIT 20;
```

- Structured output: `return_type` (an exact DuckDB type or enum), `struct` (+ `struct_descr`), or `json_schema`. Pick one.
- Reasoning models (`gpt-6-luna`, GPT-5 series) accept `reasoning_effort`, which defaults to `'none'`. Raise it to `'low'` or higher only for tasks that need reasoning; it adds cost and latency. `temperature` applies to non-reasoning models only.
- Results are not cached between queries. Pass untrusted user text through prepared statements.

## `embedding`

`embedding(text_input [, model := ...])` returns `FLOAT[512]` with the default `text-embedding-3-small` and `FLOAT[1024]` with `text-embedding-3-large`. Store vectors in a table and rank with `array_cosine_similarity`. Keep the model fixed for a column, since vectors from different models are not comparable.

## Cost and Reliability Rules

- Run on a `LIMIT` sample first and inspect results before scanning a full table.
- Materialize results (`CREATE TABLE ... AS SELECT` or an enrichment column) instead of recomputing them in dashboards or views.
- Failures and a reached session cap return `NULL` for affected rows rather than failing the query. Fill gaps with `UPDATE ... WHERE result IS NULL`. A validation error from `prompt_jev` fails the whole query.
- In scheduled pipelines, enrich only new or changed rows.
- Admins set the AI session cap on the AI Features settings page; it limits spend, not throughput.

## Data Handling

- `prompt_jev()` sends input, instructions, and labels to TypeSafe servers in the US from every MotherDuck region. It is off by default in EU regions until an Admin enables it.
- `prompt()` is served from US processing for US regions and from Europe for Dublin (`eu-west-1`); Asia Pacific regions use a US endpoint, so text leaves the region. Check current docs for other regions and for `embedding()`.
- Admins can disable AI functions or `prompt_jev()` alone on the AI Features settings page; queries then fail with an "AI functions are not available" error.
