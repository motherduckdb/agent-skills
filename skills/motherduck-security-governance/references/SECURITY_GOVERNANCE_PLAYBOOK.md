# Security and Governance Playbook

Reference for discussing MotherDuck security posture, access-control boundaries, residency framing, and governance-safe architecture defaults.

## Contents

| Section | Covers |
|---|---|
| SQL Review Checks | Queries that verify the claimed governance boundary |
| Secure Defaults | Service accounts, credentials, isolation posture |
| Publicly Documented Security Anchors | SOC 2, GDPR, service accounts, shares, SSO, recovery |
| Governance Checklist | Questions every design must answer |
| Region and Residency Guidance | Region availability vs residency vs contracts |
| Roles and Grants | Preset/custom roles, inheritance, assignments, and Share grants |
| Product-Specific Patterns To Prefer | Hypertenancy, per-boundary service accounts, read tokens |
| Dives and Sharing Guidance | Share vs Dive vs application boundaries |
| SSO Guidance | Plan gating, verified domains, IdP rollout |
| Recovery and Retention Guidance | Snapshots, restore windows, UNDROP DATABASE |
| What Not To Overstate | Compliance claims requiring commercial confirmation |

## When To Use

- The user asks about residency, isolation, access control, auditing, sharing, or governance.
- The user is reviewing a proposed architecture for tenant isolation or token handling.
- The user needs a secure default pattern for an app, pipeline, or analytics rollout.

## SQL Review Checks

Use SQL to validate the governance boundary that the architecture claims to have.

Check what databases and aliases are actually in scope:

```sql
SELECT alias AS database_name, type
FROM MD_ALL_DATABASES();
```

Check what shares are owned:

```sql
FROM MD_INFORMATION_SCHEMA.OWNED_SHARES;
```

Check what shares are attached from others:

```sql
FROM MD_INFORMATION_SCHEMA.SHARED_WITH_ME;
```

Check whether a proposed consumer path is reading from a curated shared database instead of a raw internal database:

```sql
SELECT *
FROM "shared_partner_data"."main"."approved_metrics"
LIMIT 10;
```

## Secure Defaults

- Prefer service accounts for production systems, not personal tokens.
- Prefer backend-held credentials over browser-exposed credentials.
- Prefer structural isolation over query-time tenant filtering for serious B2B or CFA workloads.
- Prefer region-specific guidance when residency matters.
- Use shares as read-only publication boundaries. Use `INCLUDE_PATTERN` for whole-table/view filtering, never as row-level or column-level security.

## Publicly Documented Security Anchors

These are safe public anchors to use:

- MotherDuck publicly states that it undergoes independent third-party audits and has a SOC 2 Type II attestation.
- MotherDuck publicly states that it is GDPR verified and that signed DPAs can be requested via `security@motherduck.com`.
- Public pricing and trust pages state that compliance reports are available through the commercial process, and that some commercial or security features vary by plan.
- MotherDuck publicly documents service accounts as organization-owned non-human identities for applications and automation.
- MotherDuck publicly documents shares as read-only and zero-copy, with optional table/view filtering through `INCLUDE_PATTERN`; this is not row-level or column-level entitlement enforcement.
- MotherDuck publicly documents preset and custom roles, role inheritance, user assignments, and role-based Share grants. Custom roles are plan-gated, so verify current entitlements before promising availability.
- MotherDuck publicly documents SSO support with identity providers such as Okta, Microsoft Entra ID, and SAML/OIDC options. Verify current plan requirements and limitations before promising a rollout path.
- MotherDuck publicly documents data recovery through automatic snapshots, named snapshots, point-in-time restore, and `UNDROP DATABASE`, with retention and availability varying by plan.

Do not overstate beyond those anchors. If the user needs a compliance report, a signed DPA, a HIPAA BAA, or plan-specific contractual commitments, say that these require confirmation through current Trust/Security or commercial channels.

## Governance Checklist

Answer these questions:

1. Where do credentials live?
2. What is the isolation boundary: account, database, schema, or query filter?
3. Who can read, write, share, or administer data?
4. Does the design require region or residency constraints?
5. What proof or documentation still needs to come from current public trust or compliance material?

If the design claims governed distribution, also ask:

6. Which database is the share source and does it use an include pattern?
7. Which users or roles receive the Share grant?
8. Is the exposed catalog curated or just a raw internal workspace?
9. Does the plan rely on query-time tenant filtering where a stronger database or service-account boundary is warranted?

## Region and Residency Guidance

- Treat region and residency as first-class architectural constraints.
- Verify current public region availability before answering; do not preserve a region list in durable guidance.
- Distinguish clearly between:
  - region availability
  - data residency expectations
  - network connectivity requirements
  - contractual or compliance requirements

If the user is really asking for a residency guarantee or legal assurance, direct them to current Trust & Security materials and the account/security channel rather than improvising.

## Product-Specific Patterns To Prefer

- Hypertenancy for strong per-customer or per-user compute isolation
- one service account per customer or workload boundary when the blast radius matters
- read-only tokens or read-scaling tokens for high-concurrency read paths
- backend-only token handling for applications
- careful sharing boundaries when using shares or Dives

## Roles and Grants

- Preset roles are concentric: `explorer` capabilities are included by `builder`, which is included by `admin`.
- A custom role inherits platform permissions from one or more roles and can receive Share grants directly. Platform permissions are inherited as a unit; do not claim they can be individually assembled unless current docs say so.
- A user's effective permissions are the union of all assigned roles. Revoking one role does not remove access supplied by another.
- Grant restricted Shares to the lowest role that should receive them. Inheriting roles receive the same grant.
- A roleless user can sign in but has no data access until a role is assigned.
- Public share links sit outside role grants; treat them as a separate exposure path.

Audit the live state before making a governance claim:

```sql
SHOW ALL ROLES;
SHOW USERS OF ROLE finance;
SHOW ROLES TO USER alice;
SHOW GRANTS ON SHARE finance_share;
```

Use `GRANT ROLE ... TO USER ...`, `GRANT ROLE ... TO ROLE ...`, and `GRANT READ ON SHARE ... TO ROLE ...` only after confirming the caller has the required permissions. A grant determines who receives a Share; its include pattern determines which tables and views all its grantees see.

## Dives and Sharing Guidance

- Dives are shareable live visualizations that persist in the MotherDuck workspace.
- Shares are zero-copy and read-only. They may expose the whole source database or a table/view subset. Use them for governed distribution, not as a substitute for row-level or column-level entitlement logic.
- Do not assume Dives replace all BI tooling; MotherDuck positions them for the long tail of questions that do not justify a full dashboard.
- For broad external or client-facing access, be explicit about whether the right pattern is a share, a Dive, or a full customer-facing application.

## SSO Guidance

- Treat SSO as an organization-level authentication control, not a data-access boundary.
- Verify the current SSO entitlement and organization requirements before proposing implementation work.
- Confirm verified domains, IdP ownership, and domain conflicts before activation.
- Once SSO is active for matching domains, users should expect to authenticate through the identity provider rather than unmanaged login paths.
- If the user needs multi-org SSO behavior, verify current docs before committing; do not infer it from ordinary SAML or OIDC support.

## Recovery and Retention Guidance

- Treat recovery posture as a governance requirement when the user asks about rollback, deletion recovery, audit readiness, or operational resilience.
- Verify the plan-specific retention window before promising a recovery target; do not carry a plan name or day count forward from this reference.
- Use named snapshots for explicit restore points that should survive automatic snapshot garbage collection.
- `UNDROP DATABASE` can recover dropped databases only within the documented recovery window.

## What Not To Overstate

- Do not imply certifications, contractual terms, or legal guarantees that are not explicitly documented in current MotherDuck materials.
