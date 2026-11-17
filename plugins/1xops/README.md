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
| `/1xops:cost-check` | Top AWS and Azure savings, each with \$/month and its source | Enterprise |
| `/1xops:change-request` | A change request ready for your change board, from `terraform show -json` | Enterprise |
| `/1xops:ai-spend` | AI spend by team, vendor, and seat vs API | Enterprise |
| `/1xops:runbook` | A runbook with a person's yes at each step, and evidence | Enterprise |
| `/1xops:status` | The weekly status, from a live project board | Enterprise |
| `/1xops:read-only-cloud` (skill) | Keeps AWS and Azure work read-only: checks access first, proposes any change | Enterprise |

### Naming convention

| Rule | Example |
|---|---|
| Every command and skill is `/1xops:<name>` | `/1xops:check` |
| `<name>` is the outcome the user gets: lowercase kebab-case, 1–2 words | `cost-check`, `change-request` |
| No edition, vendor or version in the name | not `/1xops:pro-cost`, not `/1xops:aws-cost-v2` |
| A skill is named for the rule it enforces | `/1xops:read-only-cloud` |
| A shipped name never changes meaning | `check` is the same command in both editions |

Free: marketplace `1ops` (this repository), `/plugin install 1xops@1ops`. Enterprise: marketplace `1xops` (private `1xOps/1xops-enterprise`), `/plugin install 1xops@1xops`: the same `1xops` plugin with every command above. Install one edition.

## Connectors

Defined in [`.mcp.json`](.mcp.json): GitHub, Azure DevOps, Atlassian, Notion and Slack, each the vendor's official endpoint.

## Dependency

`plugin.json` declares the free base `operations` plugin as its only dependency. 1xops commands are namespaced `/1xops:*` and never replace the base plugin's commands.

## Licence

Apache-2.0. See [LICENSE](../../LICENSE) and [NOTICE](../../NOTICE). © 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com), OceanSoft.io.
