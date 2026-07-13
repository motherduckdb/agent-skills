# MotherDuck REST API Guide

Use this guide for control-plane workflows against `https://api.motherduck.com`.

The REST API is not the SQL query path. Use it for organization administration, service-account provisioning, supported token lifecycle work, Duckling configuration, active-account inspection, and Dive embed sessions.

## MotherDuck MCP

When the MotherDuck MCP server is connected and user-admin tools are enabled, prefer MCP
admin tools over curl. The server exchanges the caller's credential for a regional SLT and
calls `api.<region>.motherduck.com`, not the global routing host. Call `get_user_admin_guide`
for the in-session copy of this guide.

Confirm destructive MCP calls (`delete_user`, `invalidate_access_token`) before invoking.
Store newly minted token secrets immediately — they are shown once.

## Contents

- [Authentication](#authentication)
- [Endpoint Summary](#endpoint-summary)
- [Service Account Provisioning](#service-account-provisioning)
- [Token Lifecycle](#token-lifecycle)
- [Duckling Configuration](#duckling-configuration)
- [Active Accounts](#active-accounts)
- [Dive Embed Sessions](#dive-embed-sessions)
- [Error Responses](#error-responses)

## Authentication

All endpoints use bearer authentication:

```bash
export MD_API="https://api.motherduck.com"
export MOTHERDUCK_ADMIN_TOKEN="<admin-token-from-secret-manager>"

curl -fsS \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  "${MD_API}/v1/active_accounts"
```

Operational rules:

- Use a read-write access token for an organization Admin for admin/control-plane calls.
- Keep `MOTHERDUCK_ADMIN_TOKEN` in a backend secret manager or local environment variable, never source code.
- Do not send admin bearer tokens to browsers.
- Do not use read-scaling tokens for REST API administration.
- Log status codes and error `code` or `message`, but do not log bearer tokens or newly minted access tokens.

## Endpoint Summary

| Operation | MCP tool | Method and path | Notes |
|---|---|---|---|
| Load admin guide | `get_user_admin_guide` | — | In-session copy of this guide. |
| Create service account | `create_service_account` | `POST /v1/users` | Username unique in org; creates a service account only. |
| Delete user | `delete_user` | `DELETE /v1/users/{username}` | Destructive; confirm first. |
| Create token | `create_access_token` | `POST /v1/users/{username}/tokens` | Secret returned once. |
| List tokens | `list_access_tokens` | `GET /v1/users/{username}/tokens` | Metadata only. |
| Delete token | `invalidate_access_token` | `DELETE /v1/users/{username}/tokens/{token_id}` | Use token `id`, not the secret. |
| Get Duckling config | `get_duckling_config` | `GET /v1/users/{username}/instances` | Requires admin role. |
| Set Duckling config | `set_duckling_config` | `PUT /v1/users/{username}/instances` | Requires both `read_write` and `read_scaling`. |
| Get active accounts | — | `GET /v1/active_accounts` | Verify lifecycle status and response shape in the current OpenAPI spec. |
| Create Dive embed session | `create_dive_embed_session` | `POST /v1/dives/{dive_id}/embed-session` | Requires service-account `username`; optional `session_hint`. |

## Service Account Provisioning

Create a service account:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"username":"analytics_app"}' \
  "${MD_API}/v1/users"
```

Username constraints from the runtime validator:

- `3..255` characters
- starts with a Unicode letter
- contains only Unicode letters, digits, and underscores
- unique within the organization
- case-insensitive for identity

The endpoint path says `/v1/users`, but it creates service accounts, not arbitrary human users or arbitrary-role users. Do not document role updates, service-account impersonation, share attachment routes, or attachment management as public REST API capabilities unless the current public spec exposes them.

Delete a user only after explicit confirmation:

```bash
curl -fsS -X DELETE \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  "${MD_API}/v1/users/analytics_app"
```

The delete operation permanently deletes the user and all of their data.

## Token Lifecycle

Create a read-write token:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"backend-api","ttl":2592000,"token_type":"read_write"}' \
  "${MD_API}/v1/users/analytics_app/tokens"
```

Create a read-scaling token:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"embed-read-scaling","ttl":86400,"token_type":"read_scaling"}' \
  "${MD_API}/v1/users/analytics_app/tokens"
```

Request fields:

- `name`: required, `1..255` characters
- `ttl`: optional token lifetime in integer seconds, `300..31536000`; omit it for a token that remains valid until revoked
- `token_type`: optional, `read_write` or `read_scaling`; defaults to `read_write`

Response fields include:

- `token`: the access token secret, only returned on creation
- `id`: token UUID used for invalidation
- `name`, `expire_at`, `created_ts`
- `read_only`
- `token_type`: `read_write` or `read_scaling`

List token metadata:

```bash
curl -fsS \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  "${MD_API}/v1/users/analytics_app/tokens"
```

Invalidate a token:

```bash
curl -fsS -X DELETE \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  "${MD_API}/v1/users/analytics_app/tokens/00000000-0000-0000-0000-000000000000"
```

Token handling gotchas:

- Through the API, users can create tokens for themselves and admins can create tokens for service accounts.
- Admins cannot create tokens for other non-service-account members through the API.
- If a service account is newly created through the API, connect once with that service account's read-write token before relying on read-scaling tokens.
- The token secret is not returned by the list endpoint.
- Store the `id` separately from the token secret so rotation and invalidation can target the correct token.
- Delete tokens by `id`; do not rely on labels or names as stable deletion identifiers.
- Prefer short TTLs for automation that can rotate tokens cleanly.
- Use read-scaling tokens for read-heavy serving paths that should not use the read-write Duckling.

## Duckling Configuration

The endpoint path uses the legacy word `instances`, but it configures Ducklings.

Read a user's current Duckling configuration:

```bash
curl -fsS \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  "${MD_API}/v1/users/analytics_app/instances"
```

Set read-write and read-scaling configuration:

```bash
curl -fsS -X PUT \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "read_write": {
        "instance_size": "standard",
        "cooldown_seconds": 600
      },
      "read_scaling": {
        "instance_size": "standard",
        "flock_size": 2,
        "cooldown_seconds": 600
      }
    }
  }' \
  "${MD_API}/v1/users/analytics_app/instances"
```

Allowed `instance_size` values:

- `pulse`
- `standard`
- `jumbo`
- `mega`
- `giga`

Validation limits:

- `read_write.instance_size` is required.
- `read_scaling.instance_size` and `read_scaling.flock_size` are required.
- The schema allows `read_scaling.flock_size` values between `0` and `64`, but effective limits are plan and organization specific.
- `cooldown_seconds`, when supplied, must be an integer between `60` and `86400`.
- `cooldown_seconds` cannot be set for `pulse` Ducklings.

Default cooldown behavior:

- `standard`: `60`
- `jumbo`: `60`
- `mega`: `300`
- `giga`: `600`
- `pulse`: no cooldown

Use a read-before-write posture because `PUT /v1/users/{username}/instances` requires the full `config` object with both `read_write` and `read_scaling`. When switching an existing non-Pulse config to `pulse`, remove copied `cooldown_seconds` fields before sending the `PUT`.

A `400` response such as `Invalid config for tier ...` can mean the payload exceeded plan or organization limits even when it satisfies the OpenAPI schema.

## Active Accounts

Inspect active accounts and active Ducklings:

```bash
curl -fsS \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  "${MD_API}/v1/active_accounts"
```

The response has an `accounts` array. Each account includes:

- `username`
- `ducklings[]` with `id`, `type`, and `status`

Duckling fields:

- `id`: `rw` or `rs.N`
- `type`: `read_write` or `read_scaling`
- `status`: `active` or `cooldown`

Check the current OpenAPI spec for this endpoint's lifecycle status and response shape before building operational automation around it.

## Dive Embed Sessions

Create an embed session for a Dive:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer ${MOTHERDUCK_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"username":"analytics_app","session_hint":"customer-123"}' \
  "${MD_API}/v1/dives/00000000-0000-0000-0000-000000000000/embed-session"
```

Request fields:

- `username`: required service account username within the organization
- `session_hint`: optional non-empty hint used to reuse the same read-scaling session across embed requests

Verify embedded-Dive entitlements against current docs. An organization without embed access may receive `403`; preserve the actual status and response body rather than assuming the cause.

The response contains an opaque `session` string backed by a short-lived read-scaling token that runs as the service account. Treat it as a runtime credential:

- do not persist it longer than needed
- do not log it
- do not confuse it with a user access token
- expect it to expire after 24 hours

Frontend iframe shape:

```html
<iframe
  src="https://embed-motherduck.com/sandbox/#session=<session_from_backend>"
  sandbox="allow-scripts allow-same-origin"
></iframe>
```

If the host site has a restrictive Content Security Policy, add `https://embed-motherduck.com` to `frame-src`.

## Error Responses

Standard error responses use this shape:

```json
{
  "code": "BAD_REQUEST",
  "message": "Bad Request",
  "issues": [
    {
      "message": "field-specific validation message"
    }
  ]
}
```

Expected status codes:

- `400`: malformed request or validation failure
- `401`: invalid credentials
- `403`: authenticated but unauthorized
- `404`: target user, token, Dive, or resource not found
- `500`: internal service error

Do not convert these into silent success. Preserve the status code and response body for the caller or operator.
