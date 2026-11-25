# Access Control Setups

How MotherDuck access works layer by layer, and the setups customers build from it. The setup shapes follow the runnable examples and blueprints in the official Terraform provider repository (`motherduckdb/terraform-provider-motherduck`, `examples/` and `docs/guides/`); read those for complete roots. Verify plan availability (custom roles, read scaling, include patterns, secure views) against current docs before promising a setup.

## Contents

| Section | Covers |
| --- | --- |
| The Access Model | Identities, roles, ownership, shares, tokens, and what each controls |
| Pick the Mechanism | Requirement to mechanism table (RBAC, table-, row-, column-level, masking) |
| Setup Archetypes | Seven customer setups with identities, objects, and pitfalls |
| Terraform | Provider, auth, resources, state, and what a plan proves |
| Verify Access | Audits and live checks with real reader credentials |

## The Access Model

- **Ownership decides writes.** A database is writable only by the identity that owns it (the account whose token created it). There is no write grant and no database-level grant. Plan writers as identities, usually one service account per writer.
- **Shares decide reads.** A share publishes a database read-only. `ACCESS RESTRICTED` needs explicit grants; `ACCESS ORGANIZATION` reaches everyone in the org; `ACCESS UNRESTRICTED` reaches anyone with the URL. `VISIBILITY HIDDEN` only stops discovery. Only the share owner can grant it.
- **Grants pick the audience.** `GRANT READ ON SHARE <share> TO ROLE <role>` (or `TO USER <user>`, which covers service accounts). A grant does not attach the share: each reader attaches it once (`ATTACH '<share_url>' AS <alias>`) with a read-write token; a read-scaling token cannot do the first attach.
- **Roles carry platform permissions.** Preset roles nest: `admin` includes `builder`, which includes `explorer`. A custom role has no platform permissions until it inherits a preset role (`GRANT ROLE explorer TO ROLE finance_readers`), and it can receive share grants directly. Effective access is the union of a user's roles. A user with no role has no data access.
- **Include patterns pick tables (table-level security).** `INCLUDE_PATTERN 'reporting.*, main.orders'` limits a share to matching tables and views for every grantee. Audiences that need different tables need different shares.
- **Secure views pick rows, columns, and values (row-level, column-level security, masking).** Secure views on a share filter rows, drop columns, or mask values per consumer, keyed on `current_email()`, `current_user`, or `is_role_in_session()`. See `motherduck-share-data` for syntax and limits. A table a share exposes without a replacing secure view stays fully readable.
- **Tokens carry an identity, not a policy.** A `read_write` token can do whatever its account can. A `read_scaling` token reads through replicas and sees everything its account sees, so a writer's read-scaling token is not a curated reader. For a curated reader, use a separate account that only holds share grants.
- **Other grants.** `GRANT RUN ON FLIGHT` lets others start a Flight that runs with the owner's credentials. Dives are visible to the org but read data only through shares the viewer can read. Guides are `user` or `organization` access. These are separate from data grants; review them in the same access review.
- **Transport.** All client connections use TLS; for PostgreSQL-protocol clients set `sslmode=verify-full` (see `motherduck-connect`).

## Pick the Mechanism

| Requirement | Mechanism |
| --- | --- |
| A team may build Dives and run queries but not administer the org | Custom role inheriting `builder` or `explorer` |
| A team reads a curated database | Restricted share + `GRANT READ ON SHARE ... TO ROLE <team_role>` |
| A team sees only some schemas or tables | Share with `INCLUDE_PATTERN` (one share per distinct table set) |
| Users see only their region's or account's rows | Secure view with a `WHERE` on `is_role_in_session()`, `current_email()`, or a mapping table |
| Some users must not see a column (PII) | Secure view that omits it, or exposes it only `WHEN is_role_in_session('pii_readers')` |
| Show a partial value (last 4 digits, hashed email) | Secure view with a masking expression |
| Each customer of a SaaS app sees only its data | Database per customer, per-customer reader service account, read-scaling token in the backend |
| BI tool reads curated marts only | Separate reader account granted a marts-only share; BI holds only its read-scaling token |
| Others trigger a write without write access | Flight owned by a service account + `GRANT RUN ON FLIGHT` |
| Prove the live grants match policy | Share and role audits (below) plus live reader checks |

## Setup Archetypes

### 1. Simple warehouse

One writer identity owns `raw` and `analytics` schemas in one database; BI uses the writer's read-scaling token. Fine for a first warehouse, but it is not a security boundary: the BI token reads everything the writer can. Move to archetype 3 before exposing it to more people.

### 2. Dev and prod environments

An admin bootstrap creates one writer service account per environment (`<prefix>_dev_writer`, `<prefix>_prod_writer`), a Duckling configuration for each, and tokens per environment (a `read_write` writer token, a `read_scaling` BI token). Each environment's warehouse is then managed with that environment's writer token, in separate state. An environment name is only a naming convention; the token decides which account owns the objects. Promote code, not data. Destroy warehouses before the bootstrap: deleting a service account deletes the data it owns.

### 3. Curated BI reader

The writer owns `raw`, `transform`, and `marts`. A separate reader account receives a restricted, hidden share of `marts` only (with `INCLUDE_PATTERN` if marts mixes audiences), attaches it once with a short-lived read-write setup token, and gives BI only its read-scaling token. Raw data never reaches the BI tool.

### 4. Team access control

Per team: a custom role `<prefix>_<team>` that inherits `explorer` or `builder`, membership grants for its users, and share grants to the role (restricted shares only). Add or remove access by editing the team map, not by granting users one by one. Share grants run as the share owner, so keep one Terraform root per share owner. When an identity provider owns role membership (SCIM), MotherDuck refuses role grants for people; grant to roles and service accounts instead.

### 5. Row- and column-level access for internal audiences

One restricted share per subject area, granted to the roles that need it, with secure views that filter rows by role or email, drop sensitive columns, and mask partial values. Keep mapping tables and policy macros in a schema the share does not expose. This replaces a fan-out of near-identical shares when audiences differ only by rows or columns. Test as a member of each role; identity functions evaluate as whoever runs the query.

### 6. Customer-facing analytics (read hypertenancy)

A writer service account owns one database per tenant. Per tenant: a reader service account, its Duckling configuration, a one-hour read-write setup token (used once to attach the tenant share), a read-scaling token for the backend, a restricted hidden share of that tenant's database, and a grant to the tenant reader. The backend derives the tenant from trusted session data, keeps one connection pool per tenant identity, and never picks a credential from a request parameter. Browsers get Dive embed sessions, not tokens. Suspending a tenant revokes its grant and tokens and keeps the data; removing the tenant from configuration destroys its database. A database per tenant isolates data, not the shared writer's compute.

### 7. Partners and agencies

Repeat archetype 6 or 3 per client, with per-client writer and reader identities, service-account descriptions that name the client, and separate state per client. Use secure views only for audiences inside one client; different clients always get separate databases and shares.

## Terraform

- Provider `motherduckdb/motherduck`, Terraform 1.5 or later (OpenTofu works). Pin a version range in roots and commit `.terraform.lock.hcl`; pin reusable modules from the repo to a reviewed release tag.
- `MOTHERDUCK_TOKEN` is the SQL identity: it owns databases, shares, roles, grants, and secrets it creates. `MOTHERDUCK_ADMIN_TOKEN` is required for service accounts, access tokens, Duckling configuration, and user listing. A service-account resource does not switch the provider's SQL identity; assert the identity with `data "motherduck_current_user"` and a precondition, and never configure a provider from a token created in the same apply.
- Core resources: `motherduck_role`, `motherduck_role_grant` (`role_name`, `grantee_name`, `grantee_type` `user` or `role`), `motherduck_share` (`access`, `visibility`, `update_mode`, `include_pattern`), `motherduck_share_grant` (`share`, `username`, `grantee_type`), `motherduck_service_account`, `motherduck_access_token` (`token_type`, `ttl`), `motherduck_duckling_config`, `motherduck_database`, `motherduck_secret`.

```hcl
resource "motherduck_role" "finance" {
  name = "finance_readers"
}

resource "motherduck_role_grant" "finance_inherits_explorer" {
  role_name    = "explorer"
  grantee_name = motherduck_role.finance.name
  grantee_type = "role"
}

resource "motherduck_share" "finance" {
  name            = "finance_share"
  source_database = motherduck_database.warehouse.name
  access          = "restricted"
  visibility      = "hidden"
  update_mode     = "automatic"
  include_pattern = ["finance.*", "main.calendar"]
}

resource "motherduck_share_grant" "finance" {
  share        = motherduck_share.finance.name
  username     = motherduck_role.finance.name
  grantee_type = "role"
}
```

- Changing a share's name, source, access, visibility, or update mode replaces it: a new URL, readers must reattach, and secure views added with SQL are lost. Secure views, Flight run grants, the reader's first `ATTACH`, SSO, and SCIM are outside the provider; manage them with SQL in a step that runs after `apply`, and re-apply secure views after any share replacement.
- Token secrets are returned once and stored in state. Use an encrypted, locking remote backend, hand tokens to runtimes through a secret manager, and never give an application the state. A TTL is not a rotation plan: create the next token, switch consumers, then revoke the old one.
- Provider support can trail the platform; if a resource rejects a newer capability (for example include patterns on a managed DuckLake), use SQL for that part.

## Verify Access

- A clean plan proves only that the managed grants exist. It does not prove that no other grants exist, and `apply` does not revoke grants Terraform does not own.
- Audit drift against an explicit allowlist: the provider's `share-access-audit` example compares `motherduck_share_grants` with expected grants, and `role-access-audit` compares role members and inheritance. Both are read-only; run them in CI with failure on drift.
- In SQL: `SHOW ALL ROLES`, `SHOW ROLES TO USER <user>`, `SHOW USERS OF ROLE <role>`, `SHOW GRANTS ON SHARE <share>`, `SHOW SECURE VIEWS ON SHARE <share>`, `SHOW GRANTS ON FLIGHT '<id>'`.
- Prove it live with real reader credentials: expected reads succeed, writes fail, hidden tables and columns are absent, other tenants' shares cannot be attached, and each role sees only its rows.
