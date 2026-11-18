---
name: compliance-tracking
description: Track compliance controls and evidence for a tenant: status, gaps, owners and due dates. Use when the user says "compliance status", "audit prep", "track controls", "evidence for the auditor", "SOC 2", "ISO 27001", or "what's overdue". Reads the active tenant's settings from tenants/<name>/tenant.env.
argument-hint: "<framework or control set>"
---

# /1xops:compliance-tracking

Resolve the tenant first (see `../tenant-setup/references/tenant-config.md`).

## Steps

1. Ask for the framework and the audit date. Read the tenant's control register from `KNOWLEDGE_BASE` or `DOC_STORE`; if none exists, offer to draft one for the owner `COMPLIANCE_OWNER`.
2. For each control, record: owner, status (met, partial, gap, not tested), evidence link, last checked, next due.
3. Gather technical evidence read-only: audit trail and access settings through the read-only sign-ins in the Rules of `../tenant-setup/references/tenant-config.md`, for the clouds in `CLOUDS`. Run `1xops doctor` first. Keep evidence for `RETENTION_DAYS`.
4. Report: counts by status, overdue items, controls with no evidence, and the three actions that close the most gaps before the audit date.
5. After a yes, update the register and post the summary to `CHAT`.

## Rules

- Evidence is a link to a record, never a pasted secret or customer data.
- Mark a control met only when the evidence exists and is dated.
