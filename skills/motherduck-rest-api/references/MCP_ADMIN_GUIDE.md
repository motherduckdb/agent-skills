# MotherDuck MCP Admin Tools

Use this guide when the **MotherDuck MCP server** is connected and user-admin tools are
enabled. Admin tools call the **regional** control-plane REST API
(`api.<region>.motherduck.com/v1/...`) via a short-lived token (SLT), not SQL or the global
routing host.

Optional: call `get_user_admin_guide` to load the server-side copy of this guide in an MCP
session.

## Prerequisites

- Authenticate with MotherDuck (OAuth or PAT). Admin tools exchange that credential for an
  **SLT** and call the regional API.
- The MCP user's underlying account must have the **Admin** role in the organization.
- Most endpoints require Admin. A member may read or change their **own** Duckling config;
  token create/delete for another user requires that target to be a **service account**.

**Docs**

- OpenAPI: https://api.motherduck.com/docs/specs
- REST index: https://motherduck.com/docs/sql-reference/rest-api/

The MCP server resolves the caller's regional host and SLT at connection time (same path as
the dive viewer). Tool names below map 1:1 to REST operations on that regional host.

For direct HTTP/curl administration (global host, admin bearer token), use
`references/REST_API_GUIDE.md` instead.

## Tool picker

| User goal | MCP tool |
|---|---|
| Load full admin instructions | `get_user_admin_guide` |
| Read Duckling sizes / flock | `get_duckling_config` |
| Change Duckling sizes / flock | `set_duckling_config` |
| Create programmatic user | `create_service_account` |
| Remove user or service account | `delete_user` |
| Mint a token (secret shown once) | `create_access_token` |
| List token metadata | `list_access_tokens` |
| Revoke a token | `invalidate_access_token` |
| Embed a Dive for a service account | `create_dive_embed_session` |

## Before you act

1. Confirm the user wants an **admin** operation (not a query or Dive edit).
2. Verify they have **Admin** role (most tools). Members may only manage their **own**
   Duckling config.
3. For destructive steps (`delete_user`, `invalidate_access_token`), **confirm intent**
   before calling the tool.

## Duckling (instance) configuration

Path: `/v1/users/{username}/instances` (legacy name `instances`; configures Ducklings).

| Goal | MCP tool | REST |
|---|---|---|
| Read config | `get_duckling_config` | `GET /v1/users/{username}/instances` |
| Update config | `set_duckling_config` | `PUT /v1/users/{username}/instances` |

**Instance sizes** (both `read_write` and `read_scaling`): `pulse`, `standard`, `jumbo`,
`mega`, `giga`.

**Read-scaling** also has `flock_size` (0–64). Optional `cooldown_seconds` (60–86400) on
each side.

Example `set_duckling_config`:

```json
{
  "username": "my_service_account",
  "read_write": { "instance_size": "standard" },
  "read_scaling": { "instance_size": "pulse", "flock_size": 4 }
}
```

Omitting `cooldown_seconds` on update fills the default for the chosen instance size.

## Account administration

`POST /v1/users` creates a **service account** (programmatic user with Member role). There
is no separate REST endpoint for interactive human users.

| Goal | MCP tool | REST |
|---|---|---|
| Create service account | `create_service_account` | `POST /v1/users` |
| Delete user or service account | `delete_user` | `DELETE /v1/users/{username}` |

**Username rules:** 1–255 characters; must start with a letter; only letters, digits, and
underscores afterward.

**Delete is permanent** — removes the user and their data.

## Token administration

| Goal | MCP tool | REST |
|---|---|---|
| Create token | `create_access_token` | `POST /v1/users/{username}/tokens` |
| List tokens | `list_access_tokens` | `GET /v1/users/{username}/tokens` |
| Invalidate token | `invalidate_access_token` | `DELETE /v1/users/{username}/tokens/{token_id}` |

**Create token** fields:

- `name` (required): token label
- `token_type` (optional): `read_write` (default) or `read_scaling`
- `ttl` (optional): expiration in seconds (300–31536000)

Response includes the secret `token` **once**.

**Invalidate** accepts token UUID `id` from create/list, or URL-encoded token label
(`name`).

Creating tokens for **another** user is only allowed when that user is a service account.

## Dive embed sessions

Business plan required. Backend creates the session; frontend renders a sandboxed iframe with
the returned session string.

- REST API: https://motherduck.com/docs/sql-reference/rest-api/dashboards-create-embed-session/
- Embedding guide: https://motherduck.com/docs/key-tasks/ai-and-motherduck/dives/embedding-dives/

| Goal | MCP tool | REST |
|---|---|---|
| Create embed session | `create_dive_embed_session` | `POST /v1/dives/{dive_id}/embed-session` |

Request body: `username` (required service account), optional `session_hint`.

Response: `{ "session": "<opaque string>" }` — pass only the session to the browser, never
the admin token.

## Typical service-account workflow

1. `create_service_account` with a unique username
2. `set_duckling_config` — size read/write and read-scaling Ducklings
3. Share Dive data to the service account
4. `create_dive_embed_session` with `dive_id`, `username`, optional `session_hint`
5. Frontend: load session in iframe per embedding guide

## Error handling

| Code | Meaning |
|---|---|
| 401 | Re-authenticate |
| 403 | Not Admin, wrong plan, or target user not allowed |
| 404 | Username, dive, or token not found |
| 400 | Validation (username, flock_size, ttl, etc.) |

When a tool returns `success: false`, read `error`, fix input, retry once.

## Related MCP tools (not admin)

- SQL: `query`, `list_databases`, `list_tables`, …
- Dives: `save_dive`, `read_dive`, `get_dive_guide`
- Docs: `ask_docs_question`
