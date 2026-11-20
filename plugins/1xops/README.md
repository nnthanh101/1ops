# 1xops plugin

1xops by [OceanSoft.io](https://www.oceansoft.io): cloud and AI cost checks, change requests and runbooks on real assets.

- Every figure carries its source.
- Read-only by default.
- Nothing is written, filed or changed without a person's yes.

## Install

```
/plugin marketplace add nnthanh101/1xops
/plugin install 1xops@1ops
```

## Commands

One namespace for free and enterprise: every command and skill is `/1xops:<name>`. Install one source or the other; the names never change.

| Command | What it does | Edition |
|---|---|---|
| `/1xops:check` | Each connector as ready, signed out or missing, with the exact fix; runs `1xops doctor` | Free (this repository) |
| `/1xops:tenant-setup` (skill) | Create, list, show or switch the active tenant; one non-secret settings file per tenant | Free |
| `/1xops:change-request` (skill) | A change request with impact, risk and rollback for your change board, from a description or `terraform show -json`; filed only after a yes | Free |
| `/1xops:vendor-review` (skill) | Total cost, risk and contract status of a vendor, with one recommendation; every figure sourced | Free |
| `/1xops:process-doc` (skill) | A process document (SOP, workflow, RACI) saved to your knowledge base after a yes | Free |
| `/1xops:capacity-plan` (skill) | Load, growth, headroom and when a limit is reached, from real utilisation | Free |
| `/1xops:compliance-tracking` (skill) | Controls and evidence: status, gaps, owners and due dates | Free |
| `/1xops:cost-check` | Top AWS and Azure savings, each with \$/month and its source | Enterprise |
| `/1xops:ai-spend` | AI spend by team, vendor, and seat vs API | Enterprise |
| `/1xops:runbook` | A runbook with a person's yes at each step, and evidence | Enterprise |
| `/1xops:status` | The weekly status, from a live project board | Enterprise |
| `/1xops:read-only-cloud` (skill) | Keeps AWS and Azure work read-only: checks access first, proposes any change | Enterprise |

### Tenants

The skills work per tenant: a company, a team or a customer you operate for. Each tenant is one file of non-secret settings, `tenants/<name>/tenant.env` (names, approvers, where documents and changes go, which clouds). The active tenant is the one name in `tenants/.active`. `/1xops:tenant-setup new <name>` asks for each value; nothing secret is stored, and sign-ins stay with each connector.

### Session start

When a session opens in a tenant folder (one with a `.env.1xops`), 1xops names each connector that is not ready, with its fix, before the first prompt. When everything is ready it prints nothing, and it never holds the session up: the check stops after 4 seconds and says so in one line. Removing the plugin removes the check.

It looks at the tenant's connectors in `.env.1xops`, the servers of this plugin and of the `operations` plugin it depends on. It reads no token. Two optional keys in `.env.1xops`:

| Key | What it does |
|---|---|
| `AWS_BILLING_ACCOUNT`, `AWS_OPERATIONS_ACCOUNT` | The account the profile must sign in to; a different one is named as the wrong account, masked as `****1234` |
| `ONEXOPS_IGNORE` | Connector names to leave out, comma separated, for example `gmail,google calendar` |

`1xops doctor` lists every connector for the tenant; `1xops doctor --brief` shows what the session start shows.

### Naming convention

| Rule | Example |
|---|---|
| Every command and skill is `/1xops:<name>` | `/1xops:check` |
| `<name>` is the outcome the user gets: lowercase kebab-case, 1–2 words | `cost-check`, `change-request` |
| No edition, vendor or version in the name | not `/1xops:pro-cost`, not `/1xops:aws-cost-v2` |
| A skill is named for the rule it enforces | `/1xops:read-only-cloud` |
| A shipped name never changes meaning | `check` is the same command in both editions |

Free: marketplace `1ops` (this repository), `1xops install --yes` or `/plugin install 1xops@1ops`. Enterprise: marketplace `1xops` (private `1xOps/1xops-enterprise`), bought at [shop.oceansoft.io](https://shop.oceansoft.io) and installed with `1xops install --edition enterprise --file <bundle> --yes`: the same `1xops` plugin with every command above. Installing one edition replaces the other.

## Connectors

Defined in [`.mcp.json`](.mcp.json): GitHub, Azure DevOps, Atlassian, Notion and Slack, each the vendor's official endpoint.

Azure DevOps needs your organisation: set `AZURE_DEVOPS_ORG` in your environment to use it. Without it the connector is listed as failed, which changes nothing else; every other connector asks for its own sign-in the first time.

## Dependency

`plugin.json` declares 12 free plugins from Anthropic's `knowledge-work-plugins` marketplace as dependencies, installed with 1xops: `operations` (the base the 1xops skills build on), `cowork-plugin-management`, `customer-support`, `data`, `engineering`, `enterprise-search`, `finance`, `human-resources`, `marketing`, `product-management`, `sales` and `small-business`. Together they bring about 60 connectors; the session start checks only those of 1xops and `operations`, so a connector you do not use never fills the screen (`ONEXOPS_IGNORE` leaves out more). 1xops commands are namespaced `/1xops:*` and never replace the base plugin's commands. Five 1xops skills share a name with an `operations` skill (`change-request`, `capacity-plan`, `compliance-tracking`, `process-doc`, `vendor-review`): the `operations:*` one is the generic version, and the `/1xops:*` one adds the active tenant's approvers, freeze window and filing targets, and asks before anything is filed.

## Skills for building your own plugin

Beside the dependencies above, a clone of this repository turns on `document-skills` (`document-skills:docx`, `:pdf`, `:pptx`, `:xlsx`) for every member, so a plugin you build can produce real Word, PDF, PowerPoint and Excel files, and `skill-creator` to write the skills. `commerce-builder` is there as a reference for building agents whose writes are staged and approved by a person. They are not part of this plugin and are not copied into it. See [`plugins/README.md`](../README.md).

## Licence

Apache-2.0. See [LICENSE](../../LICENSE) and [NOTICE](../../NOTICE). © 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com), OceanSoft.io.
