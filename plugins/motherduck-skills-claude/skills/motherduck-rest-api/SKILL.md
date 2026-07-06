---
name: motherduck-rest-api
description: MotherDuck REST API control-plane reference. Use when calling api.motherduck.com or MotherDuck MCP admin tools to provision service accounts, create, list, rotate, or revoke access tokens, configure Duckling instance sizes and read scaling, inspect active accounts, or mint Dive embed sessions. Prefer MCP admin tools when the MotherDuck MCP server is connected. Not for SQL or data-plane query work.
argument-hint: [admin-api-task]
license: MIT
---

# REST API Administration

Use this skill when the user needs to manage MotherDuck service accounts, supported token operations, Duckling configuration, active accounts, or Dive embed sessions through the REST API.

## Source Of Truth

- Prefer current MotherDuck REST API documentation, the public OpenAPI spec at `https://api.motherduck.com/docs/specs`, or an explicit OpenAPI spec supplied by the user.
- For token scope and embed behavior, cross-check the REST API docs and the Embedded Dives docs because they include operational constraints not obvious from the raw schema.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it to check whether public REST API guidance has changed.
- Treat endpoint availability, preview status, token fields, and role requirements as current only when backed by the supplied spec or current docs.

## Default Posture

- Treat the REST API as the control plane; SQL and data-plane queries go through a database connection, not the REST API.
- Use `https://api.motherduck.com` as the base URL unless the user provides another environment.
- Authenticate with `Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}` and keep admin read-write tokens in backend-managed secrets.
- Never use read-scaling tokens for REST API administration.
- Prefer read-before-write flows for configuration changes so the current account, service account, Duckling config, or Dive metadata is known before mutation.
- Treat `POST /v1/users` as service-account creation unless current docs explicitly broaden the API.
- Assume active-account, Duckling configuration, service-account creation, service-account token creation, and Dive embed-session endpoints require an organization admin bearer token unless current docs say otherwise.
- Never expose generated access tokens in logs, browser code, client bundles, or committed files.
- Confirm destructive deletes with the user. Deleting a user permanently deletes that user and all of their data.

## Workflow

1. Identify whether the task is service-account provisioning, token management, Duckling sizing, active-account inspection, or Dive embedding.
2. Confirm the admin token location and the target `username` or `dive_id`; never invent production identifiers.
3. Check token scope before calling token endpoints: users can create tokens for themselves, and admins can create tokens for service accounts, but admins cannot create tokens for other non-service-account members through the API.
4. For Duckling config changes, read the current config first, then update both `read_write` and `read_scaling` because the `PUT` payload requires both.
5. Preserve response fields that are only returned once, especially newly created token strings and embed session strings.
6. Surface API errors by status and response body; do not hide `400`, `401`, `403`, `404`, or `500` responses behind success-shaped fallbacks.

## MotherDuck MCP Path

When the MotherDuck MCP server is connected and user-admin tools are enabled, prefer MCP
admin tools over raw HTTP. The server exchanges the caller's credential for a regional SLT
and targets `api.<region>.motherduck.com`, not the global routing host.

| Task | MCP tool |
|---|---|
| Load admin instructions | `get_user_admin_guide` |
| Read / set Duckling config | `get_duckling_config` / `set_duckling_config` |
| Create service account | `create_service_account` |
| Delete user | `delete_user` |
| Create / list / revoke tokens | `create_access_token` / `list_access_tokens` / `invalidate_access_token` |
| Mint Dive embed session | `create_dive_embed_session` |

Common flows:

- Service account + token: `create_service_account` → `set_duckling_config` → `create_access_token`
- Dive embed: create service account → size Ducklings → share Dive data → `create_dive_embed_session`

Confirm destructive MCP calls (`delete_user`, `invalidate_access_token`) before invoking.
Store newly minted token secrets immediately — they are shown once.

## Open Next

- When MotherDuck MCP admin tools are available: read `references/MCP_ADMIN_GUIDE.md` for tool workflows, regional API behavior, and embed-session patterns.
- For direct HTTP/curl administration: read `references/REST_API_GUIDE.md` for endpoint summaries, auth headers, request payloads, curl examples, validation limits, and operational gotchas.

## Related Skills

- `motherduck-query` for SQL and data-plane query work
- `motherduck-connect` for connection tokens and application connection posture
- `motherduck-security-governance` for admin-token handling, service-account posture, and access-boundary questions
- `motherduck-create-dive` for designing Dives before minting embed sessions
