---
name: tenant-setup
description: Create, list, show or switch the active tenant for 1xops operations skills. Use when the user says "set up a tenant", "new tenant", "switch tenant", "which tenant am I on", "configure tenant", or when another 1xops skill finds no tenant file.
argument-hint: "[new <name> | list | show | use <name>]"
---

# /1xops:tenant-setup

Manage the per-tenant settings that every operations skill reads. Read `references/tenant-config.md` first for the key list and rules.

## Steps

1. Locate the tenants folder: `tenants/` at the repository root. Each tenant's settings are `tenants/<name>/tenant.env`.
2. Act on the argument:
   - **list**: show each tenant folder and its `TENANT_DISPLAY`, and mark the active one.
   - **show**: print the active tenant's file with every key, and name any key still empty.
   - **use `<name>`**: write `<name>` as the only line of `tenants/.active`. Confirm the tenant file exists first.
   - **new `<name>`**: ask for each key in `references/tenant-config.md`, one group at a time (identity, approvers, tools, cloud, policy), offering the listed choices. Write `tenants/<name>/tenant.env` and a short `README.md` beside it. If `tenants/.active` does not exist yet, write `<name>` to it.
3. Refuse any key whose name looks secret (`TOKEN`, `SECRET`, `PASSWORD`, `KEY`, `CREDENTIAL`). Tell the user where secrets belong: the connector's own sign-in, never this file.
4. Store no cloud profile or account. Cloud access comes from the read-only sign-ins in the Rules of `references/tenant-config.md`.
5. End by printing the active tenant and the next step: run `/1xops:check` to see which connectors are ready.

## Rules

- Change nothing outside `tenants/`.
- Never copy one tenant's values into another without asking.
- Never commit; leave the files for the owner.
