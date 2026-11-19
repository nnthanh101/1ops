# Connectors

How 1xops connects one tenant, then hundreds, to the tools its people and its assistant use. Every value is a
variable. No account ID, tenant ID, e-mail address or token is ever written in this repository.

> [!IMPORTANT]
> **Two layers, one identity provider.**
> **People** sign in once, through the tenant's identity provider (Microsoft Entra ID), and reach every tool from
> My Apps.
> **The assistant** uses only **read-only identities** that the tenant creates for it, and `1xops doctor` checks
> each one before the first cloud call.
> The identity is the boundary. The rules only ask.

---

## Contents

1. [How it fits together](#how-it-fits-together)
2. [Configuration: variables, never values](#configuration-variables-never-values)
3. [As-is: the reference tenant](#as-is-the-reference-tenant)
4. [To-be: connector catalogue](#to-be-connector-catalogue)
5. [Rollout 2026–2030](#rollout-20262030)
6. [Plan and licence limits](#plan-and-licence-limits)
7. [Add a connector](#add-a-connector)

---

## How it fits together

```mermaid
flowchart LR
  subgraph People["People (sign-in layer)"]
    U[Employee] --> E[Microsoft Entra ID]
    E --> MA[My Apps]
    MA -->|SAML| S1[AWS · HCP · Grafana · GitHub]
    MA -->|Linked + Entra sign-in| S2[HubSpot · Infracost]
    MA -->|native Entra| S3[Teams · M365 · Azure DevOps]
  end
  subgraph Assistant["Assistant (read-only layer)"]
    F[".env.1xops<br/>names + ssm: references"] --> V[(Vault<br/>AWS SSM Parameter Store)]
    F --> D[1xops doctor]
    D -->|ready / check / stop| C[Connectors]
    C -->|ReadOnlyAccess role| AWS[(AWS)]
    C -->|Reader identity| AZ[(Azure)]
    C -->|read-only token| SaaS[(SaaS APIs)]
  end
  E -. same identities .-> C
```

| Layer | Who | Proven by | Never |
|---|---|---|---|
| Sign-in | People | A tile launch from a **clean session** (signed out of the app first) | A pass from a session that was already signed in |
| Read-only | The assistant | `1xops doctor`: every row `ready` or `check`, none `can change things` | The owner's own login, a write role, a token that can change things |

---

## Configuration: variables, never values

A tenant is a folder with one `.env.1xops`. That file is tracked in git and holds **names and references only**.
Values live in a vault and are read at run time with the tenant's own read-only identity.

```dotenv
# tenants/<tenant>/.env.1xops : tracked, no values
ONEXOPS_CONNECTORS=aws,azure,itsm
AWS_CONFIG_FILE=~/.aws/tenants/<tenant>/config        # AWS's own local file, outside git
AWS_BILLING_PROFILE=<tenant>-billing-ReadOnly
AWS_OPERATIONS_PROFILE=<tenant>-<account>-ReadOnly
AWS_OPERATIONS_ACCOUNT=ssm:/1xops/tenants/<tenant>/AWS_OPERATIONS_ACCOUNT
AZURE_CONFIG_DIR=~/.azure-<tenant>-reader               # a Reader identity, never the owner's login
AZURE_DEVOPS_ORG=ssm:/1xops/tenants/<tenant>/AZURE_DEVOPS_ORG
GRAFANA_URL=ssm:/1xops/tenants/<tenant>/GRAFANA_URL
```

| Kind | Where it lives | Example | Read with |
|---|---|---|---|
| Names, profiles, paths | `.env.1xops` (git) | `AWS_BILLING_PROFILE` | — |
| IDs (account, subscription, org) | Vault, `String` | `/1xops/tenants/<tenant>/AWS_OPERATIONS_ACCOUNT` | the tenant's ReadOnly role |
| Tokens and keys | Vault, `SecureString` | `/1xops/tenants/<tenant>/GITHUB_TOKEN` | the tenant's ReadOnly role + decrypt |
| SSO start URL, region | AWS's own config file | `~/.aws/tenants/<tenant>/config` | the AWS CLI |

<details>
<summary><b>Why AWS SSM Parameter Store</b></summary>

- Standard parameters cost nothing, and the service is already in every AWS tenant: one less system to run.
- Access follows the same IAM role the assistant already uses, so there is no second credential to protect.
- Tenants without AWS use the same `ssm:`-style reference against Azure Key Vault (`kv:`); the shape of `.env.1xops` does not change.
- Rejected: secrets encrypted inside git (one leaked key opens every past commit), and a self-hosted vault (one more service to patch for a small team).

</details>

> [!WARNING]
> Values are written to the vault by a person with a write-capable profile, never by the assistant. `1xops` prints
> a value from the vault only masked (`****1234`) and never writes it to disk.

---

## As-is: the reference tenant

The `os` tenant, proven on **19 Nov 2026** in a real browser and a real terminal.

### Sign-in layer (Entra ID → My Apps)

| Tool | Sign-in | Status | Evidence | Next |
|---|---|:-:|---|---|
| AWS IAM Identity Center | SAML | ✅ | portal lists 3 accounts, each with `ReadOnlyAccess` | read-only profile per account |
| GitHub (org) | SAML | ✅ | lands in the org | fine-grained read-only token for the assistant |
| Grafana Cloud | SAML | ✅ | lands in the stack after wake-up | free stack sleeps: CAPTCHA on first visit |
| Azure DevOps | Entra native | ✅ | lands in the org | — |
| Atlassian · Jira · Confluence | Entra | ✅ | lands in the site | — |
| Slack | Entra | ✅ | lands in the workspace | — |
| Microsoft Teams | Entra native | ✅ | lands signed in | — |
| HashiCorp Cloud Platform | SAML (SP-initiated) | ⚠️ | URL migration done before the 31 Jan 2027 deadline; Entra issues the token, HCP rejects the owner e-mail | prove with a separate test user; the owner keeps IBMid as break-glass |
| HubSpot | Entra sign-in (OIDC), Linked tile | ⚠️ | SAML needs HubSpot Professional; the account is free | the tile opens the login page, then "Sign in with Microsoft" |
| Infracost | Linked tile | ⚠️ | no SSO setting on the current plan | GitHub/Google sign-in until Enterprise |
| M365 MCP app registrations | API only | ✅ | hidden from My Apps: they are not apps to launch | review Graph permissions: read-only, consent recorded |
| Salesforce (developer org) | SAML | 🔜 | requested | gallery app + SP-initiated proof |
| Assistant platform | SAML | 🔜 | requested | depends on the plan offering SSO |

### Read-only layer (`1xops doctor`, version 0.3.2)

| Connector | Status | Fix |
|---|:-:|---|
| AWS billing (`AWS_BILLING_PROFILE`) | ✅ ready | — |
| AWS operations (`AWS_OPERATIONS_PROFILE`) | ❌ | one ReadOnly profile per account, IDs from the vault |
| GitHub | ⚠️ check | the token can change things: use a fine-grained read-only token |
| Azure DevOps | ❌ broken | `AZURE_DEVOPS_ORG` from the vault |
| Azure | ⚠️ not checked | a Reader identity in its own `AZURE_CONFIG_DIR` |
| Atlassian · Slack · Notion | ➖ in host | sign in inside the assistant (`/mcp`) |
| Grafana · HCP Terraform · Infracost · HubSpot · M365 | ❌ none | to-be, see below |

---

## To-be: connector catalogue

Merged from every plugin's `CONNECTORS.md`. A plugin names a category (`~~chat`). The tenant decides which tool
fills it, and 1xops checks that tool's identity.

**Legend:**
- ✅ checked by `1xops doctor` today
- 🟡 in host: it signs in inside the assistant
- 🔜 planned, with the wave in brackets
- ➖ no supported server yet

| Category | Placeholder | Reference choice | Alternatives | People sign-in | Assistant identity | 1xops |
|---|---|---|---|---|---|:-:|
| Cloud: AWS | — | AWS | — | Entra → Identity Center (SAML) | ReadOnlyAccess role per account | ✅ |
| Cloud: Azure | — | Azure | — | Entra native | Reader in its own config folder | ✅ |
| Source control | `~~source control` | GitHub | GitLab, Bitbucket | SAML | fine-grained read-only token | ✅ |
| CI/CD | `~~CI/CD` | GitHub Actions | Azure Pipelines, CircleCI, Jenkins | as source control | same token, `actions:read` | 🔜 (W1) |
| Project tracker | `~~project tracker` | Jira, Azure DevOps | Linear, Asana, monday.com | Entra | read-only scope | 🟡 / ✅ |
| Knowledge base | `~~knowledge base` | Confluence | Notion, Guru, Coda | Entra | read-only scope | 🟡 |
| Chat | `~~chat` | Slack | Microsoft Teams | Entra | read-only scope | 🟡 |
| Email · calendar · office suite | `~~email` `~~calendar` `~~office suite` | Microsoft 365 | Google Workspace | Entra native | Entra app, read-only Graph scopes | 🔜 (W1) |
| Cloud storage | `~~cloud storage` | SharePoint / OneDrive | Box, Dropbox, Google Drive | Entra native | read-only Graph scopes | 🔜 (W1) |
| Monitoring | `~~monitoring` | Grafana | Datadog, New Relic, Splunk | SAML | viewer service-account token, no write | 🔜 (W1) |
| Infrastructure as code | — | HCP Terraform | — | SAML | read-only team token, operations off | 🔜 (W1) |
| Cloud cost | — | AWS Cost Explorer, Infracost | Azure Cost Management | Entra / Linked | billing read-only role, read-only API key | ✅ / 🔜 (W1) |
| ITSM | `~~ITSM` | Jira Service Management | ServiceNow, Zendesk, Freshservice | Entra | read-only scope | 🟡 |
| CRM | `~~CRM` | HubSpot | Salesforce, Pipedrive | Entra sign-in / SAML | read-only private-app token | 🔜 (W1) |
| Marketing automation | `~~marketing automation` | HubSpot | Marketo, Mailchimp | as CRM | as CRM | 🔜 (W2) |
| Support platform | `~~support platform` | HubSpot Service Hub | Intercom, Zendesk | as CRM | read-only | 🔜 (W2) |
| Data warehouse | `~~data warehouse` | Snowflake, Databricks | BigQuery, Redshift | SAML | read-only role | 🔜 (W2) |
| Analytics / BI | `~~analytics` | Power BI | Tableau, Looker | Entra native | viewer | ➖ |
| Incident management | `~~incident management` | — | PagerDuty, Opsgenie | SAML | read-only key | 🔜 (W2) |
| Design | `~~design` | — | Figma, Canva | SAML | read-only token | 🔜 (W3) |
| Product analytics | `~~product analytics` | — | Amplitude, Mixpanel | SAML | read-only key | 🔜 (W3) |
| Meeting transcription | `~~meeting transcription` | — | Fireflies, Gong | SAML | read-only | 🔜 (W3) |
| HRIS · ATS | `~~HRIS` `~~ATS` | — | Workday, BambooHR, Greenhouse | SAML | read-only report user | 🔜 (W3) |
| ERP · procurement | `~~erp` `~~procurement` | — | NetSuite, SAP, Coupa | SAML | read-only | ➖ |
| E-signature · CLM | `~~e-signature` `~~CLM` | — | DocuSign, Ironclad | SAML | read-only | 🔜 (W3) |

---

## Rollout 2026–2030

```mermaid
gantt
  title Connector rollout
  dateFormat YYYY-MM
  axisFormat %Y
  section W0 Reference tenant
  Sign-in layer fixed, vault, doctor rows      :w0, 2026-11, 2027-03
  section W1 First customer tenants
  M365, Grafana, Terraform, CRM, CI/CD checks  :w1, 2027-03, 2027-12
  section W2 Many tenants
  SCIM, group assignment, data + ITSM          :w2, 2028-01, 2028-12
  section W3 Self-serve at scale
  Policy as code, continuous attestation       :w3, 2029-01, 2030-12
```

| Wave | Scope | Exit gate (measurable) |
|---|---|---|
| **W0** · Nov 2026 – Mar 2027 | Reference tenant: every My Apps tile honest, vault in use, IDs out of git | 100% of tiles proven from a clean session; `doctor` shows 0 `can change things`; `git grep` finds 0 IDs |
| **W1** · 2027 | First customer tenants; M365, Grafana, HCP Terraform, CRM and CI/CD rows | New tenant onboarded in ≤ 1 day; ≥ 90% of its connectors `ready` or `check` on day one |
| **W2** · 2028 | 10+ tenants; SCIM provisioning and group assignment (Entra ID P1); data warehouse and ITSM | Joiner/mover/leaver reaches every app in ≤ 1 hour; `1xops tenants` shows every tenant on one screen |
| **W3** · 2029–2030 | Self-serve onboarding, connector policy as code, continuous attestation | 100+ tenants; quarterly access review generated, not hand-made; mean time to fix a broken connector < 1 business day |

---

## Plan and licence limits

These limits are what the vendors offer today. They are not workarounds. Each one is stated in the product and in
the tenant's own record.

| Vendor | Limit found | Effect | Path |
|---|---|---|---|
| Microsoft Entra ID (Free) | No group assignment for apps | Users are assigned one by one | Entra ID P1 at W2 |
| HubSpot (free) | SAML SSO needs Professional | Entra sign-in (OIDC) and a Linked tile | Professional when SSO enforcement is required |
| Infracost | SSO is an Enterprise feature | Linked tile; GitHub/Google sign-in | Enterprise when SSO enforcement is required |
| Grafana Cloud (free) | The stack sleeps when idle | A CAPTCHA wakes it; the first check can time out | Paid stack, or `doctor` reports `check: wakes on first visit` |
| HashiCorp Cloud Platform | Old SSO URL retires 31 Jan 2027; password sign-in ends the same day | Migration required; break-glass via IBMid | Done for the reference tenant |
| Microsoft 365 | Some MCP servers need licences the tenant may not hold | Server answers but every call fails | Check licences before you enable a server |

---

## Add a connector

1. **Pick the category** from the catalogue. The plugin stays unchanged, and the tenant chooses the tool.
2. **People:** add the vendor's gallery app in Entra. Use SAML when the plan allows it, and set the Sign-on URL so the tile starts the sign-in at the vendor (SP-initiated).
3. **Assistant:** create the vendor's **read-only** identity. Put its token in the vault (`SecureString`) and only its name in `.env.1xops`.
4. **Check:** `1xops doctor` must show the row `ready` or `check` before first use. A row that says `can change things` means stop.
5. **Prove it from clean:** sign out of the app, launch it from My Apps, and look at the result. Then sign out of the terminal session, run `doctor` again, and look again.
6. **Record:** update the tenant's row in its own private record, never here.
