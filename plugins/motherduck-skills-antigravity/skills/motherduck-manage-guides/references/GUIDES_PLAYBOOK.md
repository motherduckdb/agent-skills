# MotherDuck Guides Playbook

Reference for designing, discovering, creating, editing, and governing Guides through MotherDuck MCP or SQL.

## Contents

| Section | Covers |
| --- | --- |
| What Guides Solve | Durable semantic and workflow context |
| Discovery Before Querying | `get_query_guide`, topics, related Guides |
| Topic Design | Root, domains, nesting, reserved topics |
| Guide Content | Rules, SQL, pitfalls, descriptions |
| Access and Governance | User vs organization visibility |
| References | Catalog, Share, Dive, Flight, and Guide links |
| MCP and SQL Operations | Create, list, read, edit, version, delete |
| Versioning and Concurrency | Read-before-write and change comments |
| Quality Checklist | Validation before trusting or publishing |
| Common Mistakes | Misrouting, duplication, and stale context |

## What Guides Solve

A schema shows columns and types, but not why a metric uses one table, which join duplicates rows, what “customer” means, or which conventions a team expects in Dives and Flights. Guides store that missing context as versioned Markdown in MotherDuck.

Use Guides for:

- metric and dimension definitions
- canonical join paths and grains
- columns or tables agents must avoid
- known data-quality caveats
- organization vocabulary
- reusable query patterns
- Dive styles under `dives`
- Flight naming, scheduling, and ingestion conventions under `flights`

Do not use a Guide as a substitute for table comments, constraints, access control, source-controlled transformation logic, or query validation.

## Discovery Before Querying

When MotherDuck MCP is available and the task asks a business question:

1. Call `get_query_guide`.
2. Read root Guides that apply globally.
3. Inspect only topic names relevant to the question.
4. Call `list_guides(topic)` to traverse that subtree.
5. Read the smallest set of Guides needed for the query.
6. Inspect the live referenced tables and validate the SQL.

`search_catalog` can return `relatedGuides`, and `list_tables` can surface Guides referencing objects in that database. Treat those as discovery hints, not proof that every returned Guide applies.

## Topic Design

Topics are slash-delimited discovery paths, not unique objects. Keep them shallow and descriptive.

```text
(root)                         organization and data-platform orientation
definitions/                  shared vocabulary
revenue-billing/              revenue metrics and billing model
revenue-billing/forecasting/  one useful nested specialization
dbt/marts/                    context mirroring an existing project structure
dives/                        reserved Dive conventions
flights/                      reserved Flight conventions
```

Use the root only for context an agent should consider in almost every analytical session. A root Guide should be a short map with pointers, not a warehouse manual. Avoid topics such as `misc`, deep one-item paths, dates, or individual author names.

## Guide Content

A useful Guide has:

- a title that names the governed concept
- a one-line description that lets an agent decide whether to read it
- explicit catalog object names
- the source grain and safe join keys
- rules stated before background explanation
- working DuckDB SQL where SQL clarifies the contract
- named failure modes such as duplicate joins or incomplete history
- references to the governed objects

Prefer:

```markdown
Use `billing.main.subscriptions` for MRR. Filter `status = 'active'` and
`trial_end IS NULL`. Do not join invoices into the MRR calculation because one
subscription can have several invoice rows.
```

Avoid vague prose such as “use the billing tables carefully.”

## Access and Governance

Guide access is independent from its topic:

| Access | Visibility |
| --- | --- |
| `user` | Private to the owner; default for new Guides |
| `organization` | Visible to the organization; requires the appropriate admin permission |

Personal and organization Guides appear in the same visible topic tree. Check each Guide's access field instead of inferring visibility from its topic.

Before organization publication:

- confirm the user asked for shared context
- validate definitions with the appropriate owner
- verify SQL and references against the live workspace
- remove credentials, personal data, temporary incident details, and unsupported claims
- use a change comment that records the reason for publication

## References

References make Guides appear beside relevant catalog and product objects. A catalog reference can target a database, schema, table, or column. For an attached share, use its canonical share URL rather than the local alias.

Example SQL shape:

```sql
FROM MD_UPDATE_GUIDE(
  id = '<guide-uuid>',
  "references" = [
    {
      'type': 'catalog',
      'url': 'md:billing',
      'schema': 'main',
      'table': 'subscriptions',
      'column': 'amount',
      'description': 'Monthly subscription amount in cents'
    }
  ],
  change_comment = 'Link the canonical MRR amount column'
);
```

Discover the canonical database/share URL with MCP `list_databases` or `MD_ATTACHED_DATABASES`. Validate every referenced object before updating the Guide.

## MCP and SQL Operations

Prefer MCP when it is available because its tool descriptions carry the current contract. The corresponding SQL functions support non-MCP clients.

| Operation | MCP shape | SQL shape |
| --- | --- | --- |
| Overview | `get_query_guide` | `MD_LIST_GUIDES()` plus reads |
| Browse | `list_guides` | `MD_LIST_GUIDES(topic := ...)` |
| Read | `get_guide` | `MD_GET_GUIDE(id := ..., version := ...)` |
| Create | `create_guide` | `MD_CREATE_GUIDE(...)` |
| Replace content | `update_guide` | `MD_UPDATE_GUIDE(...)` |
| Surgical edit | `edit_guide_content` | read, edit client-side, then update |
| Change title/topic | `update_guide_metadata` | `MD_UPDATE_GUIDE_METADATA(...)` |
| Versions | version listing tool | `MD_LIST_GUIDE_VERSIONS(id := ...)` |
| Delete | delete tool | documented delete function |

Check the live tools/docs for exact arguments. Do not invent a mutation tool because a similarly named Dive or Flight tool exists.

Create SQL example:

```sql
SELECT id, topic, current_version
FROM MD_CREATE_GUIDE(
  topic = 'revenue-billing',
  title = 'MRR definition',
  description = 'Canonical source and filters for monthly recurring revenue',
  content = '# MRR\n\nUse `billing.main.subscriptions` ...',
  access = 'user'
);
```

## Versioning and Concurrency

Every content update creates a version. Before editing:

1. read the current Guide and version
2. compare the requested change with existing content
3. use a surgical edit for a small exact change or replace full content for a coherent rewrite
4. provide a reason-focused `change_comment`
5. read the new version back

If the current version changed after the initial read, stop and reconcile instead of overwriting someone else's update blindly.

## Quality Checklist

Before considering a Guide trustworthy:

- title and description discriminate it from neighboring Guides
- topic is shallow and meaningful
- rules name exact, fully qualified objects
- table grain and join cardinality are explicit
- example SQL is DuckDB SQL and runs against the intended workspace
- references resolve to the intended live objects
- access matches the requested audience
- no credentials, tokens, or private personal information appear
- claims have an owner or authoritative source
- change comment explains why the version changed

## Common Mistakes

| Mistake | Better pattern |
| --- | --- |
| Loading every Guide before every query | Traverse relevant topics progressively |
| Putting domain definitions at the root | Keep one short root map and use domain topics |
| Storing vague background prose | Lead with exact rules, objects, SQL, and pitfalls |
| Omitting descriptions | Write a one-line discriminator used in discovery |
| Referencing a share by local alias | Store its canonical share URL |
| Publishing organization-wide by default | Default to `user`; share only when explicitly requested and validated |
| Trusting a Guide without checking the schema | Validate live objects and SQL; Guides can become stale |
| Duplicating Dive/Flight instructions | Put local conventions under the reserved topic and let the product guide surface them |
| Python fetch raises `Required module 'pytz' failed to import` | Add `pytz` to that client environment or avoid converting temporal result fields; the Guide mutation itself may already have succeeded, so read state before retrying |
