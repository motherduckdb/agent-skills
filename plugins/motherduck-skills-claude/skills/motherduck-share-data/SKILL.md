---
name: motherduck-share-data
description: Create, consume, or manage MotherDuck data shares, including audience grants, table filters, and refresh policy.
argument-hint: [database-and-audience]
license: MIT
---

# Share Data with MotherDuck

## Source Of Truth

- Prefer the current MotherDuck sharing docs and SQL reference first.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it before falling back to public docs.
- Keep the sharing model aligned with the documented behavior:
  - zero-copy and metadata-only
  - a database is the share source, with optional table/view filtering through `INCLUDE_PATTERN`
  - read-only recipients
  - owner-controlled update and include-pattern policy

## Prerequisites

A working connection, the source database, and the intended audience. Reuse these from context; related skills are available for missing setup or SQL details.

## Default Posture

- Prefer `ACCESS RESTRICTED` plus `GRANT READ ON SHARE ... TO ROLE ...` for governed internal distribution. Use `ACCESS ORGANIZATION` only when the caller deliberately wants its legacy organization-wide behavior.
- Use `INCLUDE_PATTERN` when every recipient of one share should see the same table/view subset. Create separate shares when audiences need different subsets.
- Use `UPDATE MANUAL` when the recipient needs a stable snapshot or versioned delivery.
- Use `ACCESS RESTRICTED` or `VISIBILITY HIDDEN` when distribution should stay tightly controlled.
- Confirm whether the recipient is an internal user, another organization, or public before choosing access and visibility.
- For write-heavy publishers, verify the DuckDB client version is one MotherDuck supports before relying on checkpoint or concurrent-write behavior during share-update workflows.
- Never describe `INCLUDE_PATTERN` as row-level or column-level security. It selects whole tables and views and requires native MotherDuck storage.

## Workflow

1. Identify the exact database to publish and who should consume it.
2. Decide the audience, visible table/view subset, discoverability, and freshness requirements before writing SQL.
3. Preview and validate any include pattern against the live source catalog, then create the share with explicit access, visibility, update mode, and optional `INCLUDE_PATTERN`.
4. If access is restricted, grant users or roles explicitly. If the share is hidden or link-based, distribute the share URL directly.
5. Read the share back with `LIST SHARES` or `MD_INFORMATION_SCHEMA.OWNED_SHARES`; for filtered shares, verify the stored pattern and consumer-visible catalog.
6. Have recipients `ATTACH` the shared database and query it read-only.
7. Use `ALTER SHARE ... SET|RESET INCLUDE_PATTERN` for table/view scope changes. If the share uses `UPDATE MANUAL`, the owner runs `UPDATE SHARE` and consumers run `REFRESH DATABASE` when a new snapshot is ready.

For answer, review, or planning requests, return the sharing design and SQL without provisioning. For create, update, grant, or revoke requests, perform the requested in-scope operation and validate the resulting access; ask before public exposure, destructive revocation, or unrelated grants.

## References

Read only the reference sections needed for the current task.

- Read `references/SHARE_PLAYBOOK.md` for the full SQL playbook, role grants, include-pattern rules, access/update decisions, consumer workflow, and common failure modes.

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` for MotherDuck authentication and connection setup
- `motherduck-explore` for discovering databases, tables, columns, and existing shares
- `motherduck-query` for validating share SQL and downstream queries
- `motherduck-duckdb-sql` for DuckDB SQL syntax and lookup support
- `motherduck-security-governance` for role design and access-boundary review
