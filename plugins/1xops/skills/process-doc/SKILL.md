---
name: process-doc
description: Write or update a process document (SOP, workflow, RACI) in the tenant's knowledge base. Use when the user says "document this process", "write an SOP", "process documentation", "create a RACI", or "update the procedure". Reads the active tenant's settings from tenants/<name>/tenant.env.
argument-hint: "<process name>"
---

# /1xops:process-doc

Resolve the tenant first (see `../tenant-setup/references/tenant-config.md`).

## Steps

1. Ask the user to describe the process in their own words, or read an existing page from `KNOWLEDGE_BASE`.
2. Ask only for what is missing: trigger, inputs, steps and who does each, decisions, outputs, exceptions, systems, how it is measured.
3. Write the document: purpose, scope, roles and a RACI table, numbered steps, decision points, exceptions and escalation, measures, review date and owner.
4. Use the tenant's `TENANT_DISPLAY`, `TENANT_LANGUAGE` and `DOC_PREFIX` (`{DOC_PREFIX}-PRC-<n>`).
5. Show the draft. After a yes, save it to `KNOWLEDGE_BASE`. For `obsidian`, write a Markdown note with links to related processes and the owner.
6. Where a step is slow or manual, list up to three improvements. Do not change the process without approval.

## Rules

- Write steps a new colleague could follow without asking.
- Never invent a step; mark gaps as open questions for the owner.
