# Security and Governance Playbook

Reference for discussing MotherDuck security posture, access-control boundaries, residency framing, and governance-safe architecture defaults.

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
- Use shares as database-level read-only publication boundaries, not as row-level security.

## Publicly Documented Security Anchors

These are safe public anchors to use:

- MotherDuck publicly states that it undergoes independent third-party audits and has a SOC 2 Type II attestation.
- MotherDuck publicly states that it is GDPR verified and that signed DPAs can be requested via `security@motherduck.com`.
- Public pricing and trust pages state that compliance reports are available through the commercial process, and that some commercial or security features vary by plan.
- MotherDuck publicly documents service accounts as organization-owned non-human identities for applications and automation.
- MotherDuck publicly documents shares as read-only, zero-copy, database-level distribution rather than row-level or table-level entitlement enforcement.
- MotherDuck publicly documents SSO support with identity providers such as Okta, Microsoft Entra ID, and SAML/OIDC options. Verify current plan requirements and limitations before promising a rollout path.

Do not overstate beyond those anchors. If the user needs a compliance report, a signed DPA, a HIPAA BAA, or plan-specific contractual commitments, say that these require confirmation through current Trust/Security or commercial channels.

## Governance Checklist

Answer these questions:

1. Where do credentials live?
2. What is the isolation boundary: account, database, schema, or query filter?
3. Who can read, write, share, or administer data?
4. Does the design require region or residency constraints?
5. What proof or documentation still needs to come from current public trust or compliance material?

If the design claims governed distribution, also ask:

6. Which database is actually being shared?
7. Is the shared database curated or just a raw internal workspace?
8. Does the plan rely on query-time tenant filtering where a stronger database or service-account boundary is warranted?

## Region and Residency Guidance

- Treat region and residency as first-class architectural constraints.
- Verify current public region availability before answering. MotherDuck's public pricing page currently lists AWS `us-east-1` and AWS `eu-central-1`.
- Distinguish clearly between:
  - region availability
  - data residency expectations
  - network connectivity requirements
  - contractual or compliance requirements

If the user is really asking for a residency guarantee or legal assurance, direct them to current Trust & Security materials and the account/security channel rather than improvising.

## Topics This Skill Should Cover

- service accounts and token handling
- SSO and organization login controls
- database-level isolation vs shared-database tradeoffs
- regional endpoint selection
- share and Dive sharing boundaries
- governance implications of app architecture choices

## Product-Specific Patterns To Prefer

- Hypertenancy for strong per-customer or per-user compute isolation
- one service account per customer or workload boundary when the blast radius matters
- read-only tokens or read-scaling tokens for high-concurrency read paths
- backend-only token handling for applications
- careful sharing boundaries when using shares or Dives

## Dives and Sharing Guidance

- Dives are shareable live visualizations that persist in the MotherDuck workspace.
- Shares are zero-copy, database-level, and read-only. Use them for governed distribution, not as a substitute for row-level entitlement logic.
- Do not assume Dives replace all BI tooling; MotherDuck positions them for the long tail of questions that do not justify a full dashboard.
- For broad external or client-facing access, be explicit about whether the right pattern is a share, a Dive, or a full customer-facing application.

## SSO Guidance

- Treat SSO as an organization-level authentication control, not a data-access boundary.
- Verify that the organization is on a plan that supports SSO before proposing implementation work.
- Confirm verified domains, IdP ownership, and domain conflicts before activation.
- Once SSO is active for matching domains, users should expect to authenticate through the identity provider rather than unmanaged login paths.
- If the user needs multi-org SSO behavior, verify current docs before committing; do not infer it from ordinary SAML or OIDC support.

## What Not To Overstate

- Do not imply certifications, contractual terms, or legal guarantees that are not explicitly documented in current MotherDuck materials.
