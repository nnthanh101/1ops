---
name: capacity-plan
description: Plan capacity from real utilisation: current load, growth, headroom and when a limit is reached. Use when the user says "capacity plan", "are we running out", "forecast usage", "right-size", "headroom", or "plan for growth". Reads the active tenant's settings from tenants/<name>/tenant.env.
argument-hint: "<service, account or resource group>"
---

# /1xops:capacity-plan

Resolve the tenant first (see `../tenant-setup/references/tenant-config.md`).

## Steps

1. Confirm scope: which service, account or group, and the planning horizon.
2. Run `1xops doctor` before the first cloud call. A row saying `can change things` means stop.
3. Read utilisation from the tenant's `METRICS` source (CloudWatch, Grafana or Prometheus) and cost from the read-only billing profile. Cite the source and time range of each figure.
4. Compute for each resource: current and peak use, growth rate, headroom against `CAPACITY_HEADROOM_PCT`, and the date the limit is reached at that rate.
5. Present a table ranked by time to limit, then recommendations (scale, right-size, leave) with cost impact per month.
6. State the assumptions and data gaps. Offer a change request through `/1xops:change-request` for anything that needs action.

## Rules

- Read-only throughout. Propose changes; the owner runs them.
- No forecast without at least the data span you name; say when data is too short.
