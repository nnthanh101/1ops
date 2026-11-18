# Tenant config

One file per tenant: `tenants/<name>/tenant.env`. Plain `KEY=value`, non-secret. The active tenant is the one name in `tenants/.active`. These are the skills' settings; the connectors stay in `.env.1xops`, which `1xops setup` owns and rewrites, so neither file overwrites the other.

Every operations skill resolves the tenant first: read `tenants/.active`, load that tenant's file, and use its values for names, approvers, templates and tools. If `tenants/.active` is missing, use the only tenant folder; if there are several, ask which one. If none exists, run `/1xops:tenant-setup new`.

## Keys

| Group | Key | Meaning | Choices |
|---|---|---|---|
| Identity | `TENANT_DISPLAY` | Name printed in documents | free text |
| Identity | `TENANT_LANGUAGE` | Document language | `en`, `vi`, ... |
| Identity | `DOC_PREFIX` | Prefix for ids (`CHG`, `VND`, `PRC`) | free text |
| Approvers | `APPROVER` | Accountable approver, by role | free text |
| Approvers | `CHANGE_BOARD` | Who reviews changes | free text |
| Approvers | `COMPLIANCE_OWNER` | Owns the control register | free text |
| Tools | `CHANGE_TRACKER` | Where change requests are filed | `atlassian`, `notion` |
| Tools | `CHAT` | Where updates are sent | `slack`, `teams` |
| Tools | `KNOWLEDGE_BASE` | Where process docs live | `notion`, `confluence`, `obsidian`, `sharepoint` |
| Tools | `DOC_STORE` | Where contracts and evidence live | `gdrive`, `onedrive` |
| Tools | `ESIGN` | Contract signing status | `docusign`, `none` |
| Cloud | `CLOUDS` | Clouds in scope | `aws`, `azure`, `aws,azure` |
| Cloud | `METRICS` | Utilisation source | `cloudwatch`, `grafana`, `prometheus` |
| Policy | `CHANGE_FREEZE` | Freeze windows | free text |
| Policy | `RETENTION_DAYS` | Evidence retention | number |
| Policy | `CAPACITY_HEADROOM_PCT` | Target headroom | number |

## Rules

- No secret-looking key is stored here. Sign-ins belong to each connector.
- Cloud access is read-only: use the profiles named by `AWS_BILLING_PROFILE` and `AWS_OPERATIONS_PROFILE`, and an Azure Reader identity in its own `AZURE_CONFIG_DIR`. Run `1xops doctor` before the first cloud call; a row saying `can change things` means stop.
- A tool not listed in the tenant file is not used. Say so and ask, rather than falling back to another tool.
- Output carries the tenant's `TENANT_DISPLAY`, ids use `DOC_PREFIX`, and the language follows `TENANT_LANGUAGE`.
