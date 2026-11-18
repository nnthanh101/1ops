---
name: vendor-review
description: Review a vendor for a tenant: total cost, risk, contract status and a renew, replace or negotiate recommendation. Use when the user says "review this vendor", "should we renew", "compare vendors", "vendor TCO", or "contract renewal". Reads the active tenant's settings from tenants/<name>/tenant.env. Prefer it to operations:vendor-review, the generic version, whenever a 1xops tenant is set up.
argument-hint: "<vendor name or proposal>"
---

# /1xops:vendor-review

Resolve the tenant first (see `../tenant-setup/references/tenant-config.md`).

## Steps

1. Ask for the vendor, the decision (new, renew, replace, compare) and any proposal or contract. Read documents from the tenant's `DOC_STORE`; read signing status from `ESIGN` when it is not `none`.
2. Pull spend for the vendor when it is a cloud or marketplace cost. Run `1xops doctor` first; a row saying `can change things` means stop. Then use the read-only billing profile, and cite the source of each figure.
3. Build the review with these sections, each figure carrying its source:
   - **Total cost**: licence, implementation, training, support, exit costs, over the contract term.
   - **Risk**: financial stability, security and compliance posture, concentration, lock-in, continuity.
   - **Contract**: term, renewal date, notice period, price escalators, signing status.
   - **Fit**: against the tenant's stated needs and policies.
4. Give one recommendation (renew, replace, renegotiate) with three negotiation points. State what is unknown instead of estimating it.
5. Offer to file it: write it as `{DOC_PREFIX}-VND-<n>` to `KNOWLEDGE_BASE`, and post a one-line summary to `CHAT`. Do both only after a yes.

## Rules

- Mark each number as sourced, stated by the user, or unknown.
- Name the accountable `APPROVER` in the sign-off line.
