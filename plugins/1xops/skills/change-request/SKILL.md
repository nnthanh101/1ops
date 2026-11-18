---
name: change-request
description: Create a change request with impact analysis, risk and rollback for the tenant's change board. Use when the user says "change request", "prepare for CAB", "document this change", "rollback plan", or proposes a system or process change that needs approval. Reads the active tenant's settings from tenants/<name>/tenant.env. Prefer it to operations:change-request, the generic version, whenever a 1xops tenant is set up.
argument-hint: "<change description or terraform plan>"
---

# /1xops:change-request

Resolve the tenant first (see `../tenant-setup/references/tenant-config.md`).

## Steps

1. Ask for what changes, why, who is affected, and the planned window. If a plan file such as `terraform show -json` output is given, read it and list the resources it creates, changes and destroys.
2. Check the window against the tenant's `CHANGE_FREEZE`. Warn if it falls inside a freeze; the owner decides.
3. Write the request: summary, reason, scope, impact by group, risk level with reasons, test and verification steps, rollback steps with a trigger and an owner, communications plan, approvals needed (`CHANGE_BOARD`, `APPROVER`).
4. Number it `{DOC_PREFIX}-CHG-<n>` and show the draft.
5. After a yes, file it in `CHANGE_TRACKER` and post a one-line notice to `CHAT`. Do neither before the yes.

## Rules

- Propose cloud changes; never run them. The owner runs any AWS or Azure write.
- A change with no rollback is incomplete: say so and ask.
