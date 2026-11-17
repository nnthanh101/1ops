# 1ops

**Reduce cloud and AI costs. Automate operational work. Keep your team in control.**

1ops by [OceanSoft.io](https://www.oceansoft.io) is a free, open-source operations plugin for engineering teams on AWS, Azure and AI services. It finds cost savings, writes change requests and runs runbooks on your real systems, and it shows where every number came from.

[![Validate](https://github.com/nnthanh101/1ops/actions/workflows/validate.yml/badge.svg)](https://github.com/nnthanh101/1ops/actions/workflows/validate.yml) · Licence: [Apache-2.0](LICENSE)

## Principles

1. **Every figure has a source.** Each saving, risk or status line names the API, file or board item it came from. If a number can't be sourced, it isn't shown.
2. **Read-only by default.** Checks use read-only cloud roles. Nothing needs write access to give you an answer.
3. **Nothing changes without a yes.** Filing a record, sending a report or running a change step always waits for a person's explicit approval.

## Install

```
/plugin marketplace add nnthanh101/1ops
/plugin install 1ops@1ops
/1ops:check        # ships with #5 (Sprint 1)
```

`/1ops:check` lists each configured connector as ready, signed out or missing, and how to fix it. The plugin declares its one dependency (the free base `operations` plugin) in the [plugin manifest](plugins/1ops/).

## What it does

| Capability | For | Status |
|---|---|---|
| `/1ops:check`: connector readiness, with exact fixes | Platform engineers | Sprint 1 · [#5](https://github.com/nnthanh101/1ops/issues/5) |
| `/1ops:cost-check`: top 3 AWS savings, each with \$/month and source, from read-only access | CTOs, cloud leads | Sprint 1 · [#6](https://github.com/nnthanh101/1ops/issues/6) |
| Same check for Azure subscriptions | Engineering leads | Sprint 2 · [#7](https://github.com/nnthanh101/1ops/issues/7) |
| CAB-ready change request from a real Terraform plan | Change managers | Sprint 2 · [#8](https://github.com/nnthanh101/1ops/issues/8) |
| AI spend by team, vendor and seat vs API | FinOps leads | Sprint 3 · [#9](https://github.com/nnthanh101/1ops/issues/9) |
| Executable runbooks that wait for a yes and leave evidence | On-call engineers | Sprint 4 · [#10](https://github.com/nnthanh101/1ops/issues/10) |
| Weekly status report from the live project board | Delivery leads | Sprint 5 · [#11](https://github.com/nnthanh101/1ops/issues/11) |

Roadmap: [milestones](https://github.com/nnthanh101/1ops/milestones). Sprints run Monday to Friday.

## Free vs paid

| | 1ops (this repo) | OceanSoft Cloud & AI Operations |
|---|---|---|
| Price | Free, Apache-2.0 | Fixed-price assessment, then monthly |
| Who runs it | You, on your own systems | OceanSoft, with your team |
| What you get | Self-serve checks and playbooks | **Assessment:** a read-only review of your AWS, Azure and AI spend, with priced findings, evidence and a 90-day plan. **Managed:** OceanSoft runs and maintains the approved automations, and reports verified savings every month. |
| Where | GitHub | [www.oceansoft.io](https://www.oceansoft.io) · [shop.oceansoft.io](https://shop.oceansoft.io) |

OceanSoft helps NZ and Australian businesses implement and maintain practical AWS, Azure, and AI workflows.

## Contributing

- Branches: `feature/*` → pull request into `develop`; `main` receives releases only.
- One capability per pull request, proven on a real asset. Fixtures are for tests only.
- CI runs strict plugin validation on every pull request.
- Ideas and bugs: [open an issue](https://github.com/nnthanh101/1ops/issues).

## Licence

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Copyright 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com), [OceanSoft.io](https://www.oceansoft.io). "1ops" and "OceanSoft" are trademarks of OceanSoft.io.
