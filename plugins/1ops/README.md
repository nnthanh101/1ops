# 1ops plugin

1ops by [OceanSoft.io](https://www.oceansoft.io): cloud and AI cost checks, change requests and runbooks on real assets.

- Every figure carries its source.
- Read-only by default.
- Nothing is written, filed or changed without a person's yes.

## Install

```
/plugin install 1ops --marketplace nnthanh101/1ops
```

## Commands

| Command | What it does | Status |
|---|---|---|
| `/1ops:check` | Lists each connector as ready, signed out or missing, with the fix | Sprint 1 |
| `/1ops:cost-check` | Top AWS (later Azure) savings with \$/month and source | Sprint 1–2 |
| `/1ops:change-request` | CAB-ready change request from `terraform show -json` | Sprint 2 |
| `/1ops:ai-spend` | AI spend by team, vendor and seat vs API | Sprint 3 |
| `/1ops:runbook` | Executable runbook with per-step approval and evidence | Sprint 4 |
| `/1ops:status` | Weekly status from a live project board | Sprint 5 |

## Connectors

Defined in [`.mcp.json`](.mcp.json): GitHub, Azure DevOps, Atlassian, Notion and Slack, each the vendor's official endpoint.

## Dependency

`plugin.json` declares the free base `operations` plugin as its only dependency. 1ops commands are namespaced `/1ops:*` and never replace the base plugin's commands.

## Licence

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). © 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com), OceanSoft.io.
