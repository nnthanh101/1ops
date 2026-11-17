# 1xops

**Reduce cloud and AI costs. Automate operational work. Keep your team in control.**

1xops by [OceanSoft.io](https://www.oceansoft.io) is a free, open-source operations plugin for engineering teams on AWS, Azure and AI services. It finds cost savings, writes change requests and runs runbooks on your real systems, and it shows where every number came from.

[![Validate](https://github.com/nnthanh101/1xops/actions/workflows/validate.yml/badge.svg)](https://github.com/nnthanh101/1xops/actions/workflows/validate.yml) · Licence: [Apache-2.0](LICENSE)

## Principles

1. **Every figure has a source.** Each saving, risk or status line names the API, file or board item it came from. If a number can't be sourced, it isn't shown.
2. **Read-only by default.** Checks use read-only cloud roles. Nothing needs write access to give you an answer.
3. **Nothing changes without a yes.** Filing a record, sending a report or running a change step always waits for a person's explicit approval.

## Install

```
/plugin marketplace add nnthanh101/1xops
/plugin install 1xops@1xops
/1xops:check        # ships with #5 (Sprint 1)
```

`/1xops:check` lists each configured connector as ready, signed out or missing, and how to fix it. The plugin declares its one dependency (the free base `operations` plugin) in the [plugin manifest](plugins/1xops/).

### Other ways to get 1xops

| Channel | Command | What you get |
|---|---|---|
| git | `git clone --recurse-submodules https://github.com/nnthanh101/1xops` | The plugin, plus the upstream base plugins pinned in `upstream/` (`plugins/operations` links to it) |
| PyPI | `uvx 1xops doctor` | The `1xops` command line ([packages/python](packages/python/)) |
| npm | `npx 1xops doctor` | The same command line, run through uv ([packages/npm](packages/npm/)) |
| Container | `docker run --rm -v "$PWD:/work" ghcr.io/nnthanh101/1xops doctor` (or Docker Hub `nnthanh101/1xops`) | The same command line in a container |

The command line sets up the plugin, settings and read-only connectors for a whole organisation, a team or tenant folder, one project, or one person:

```bash
1xops doctor                                              # prerequisites and read-only sign-in
1xops install --yes                                       # marketplaces + plugin
1xops config --scope team --connectors aws azure itsm     # shows a diff; add --yes to write
```

Connector profiles (`aws`, `azure`, `itsm`) use only the vendors' own servers, pinned to exact versions, in read-only mode where the server offers one. Bring your own profile with `--connectors ./my-profile.json`.

## What it does

| Capability | For | Status |
|---|---|---|
| `/1xops:check`: connector readiness, with exact fixes | Platform engineers | Sprint 1 · [#5](https://github.com/nnthanh101/1xops/issues/5) |
| `/1xops:cost-check`: top 3 AWS savings, each with \$/month and source, from read-only access | CTOs, cloud leads | Sprint 1 · [#6](https://github.com/nnthanh101/1xops/issues/6) |
| Same check for Azure subscriptions | Engineering leads | Sprint 2 · [#7](https://github.com/nnthanh101/1xops/issues/7) |
| CAB-ready change request from a real Terraform plan | Change managers | Sprint 2 · [#8](https://github.com/nnthanh101/1xops/issues/8) |
| AI spend by team, vendor and seat vs API | FinOps leads | Sprint 3 · [#9](https://github.com/nnthanh101/1xops/issues/9) |
| Executable runbooks that wait for a yes and leave evidence | On-call engineers | Sprint 4 · [#10](https://github.com/nnthanh101/1xops/issues/10) |
| Weekly status report from the live project board | Delivery leads | Sprint 5 · [#11](https://github.com/nnthanh101/1xops/issues/11) |

Roadmap: [milestones](https://github.com/nnthanh101/1xops/milestones). Sprints run Monday to Friday.

## Free vs paid

| | 1xops (this repo) | OceanSoft Cloud & AI Operations |
|---|---|---|
| Price | Free, Apache-2.0 | Fixed-price assessment, then monthly |
| Who runs it | You, on your own systems | OceanSoft, with your team |
| What you get | Self-serve checks and playbooks | **Assessment:** a read-only review of your AWS, Azure and AI spend, with priced findings, evidence and a 90-day plan. **Managed:** OceanSoft runs and maintains the approved automations, and reports verified savings every month. |
| Where | GitHub | [www.oceansoft.io](https://www.oceansoft.io) · [shop.oceansoft.io](https://shop.oceansoft.io) |

OceanSoft helps NZ and Australian businesses implement and maintain practical AWS, Azure, and AI workflows.

## Contributing

- Branches: `feature/*` → pull request into `develop`; `main` receives releases only.
- One capability per pull request, proven on a real asset. Fixtures are for tests only.
- Setup for users, contributors and releases: [docs/setup.md](docs/setup.md). Decisions: [docs/adr](docs/adr/).
- Local first: turn on the hooks (`git config core.hooksPath .githooks`) and run the CI with [act](https://github.com/nektos/act) before a pull request: `act pull_request -W .github/workflows/validate.yml`. GitHub Actions runs only for `main`, tags, the monthly upstream bump or by hand.
- Releases: a `v*` tag on `main` publishes PyPI, npm, ghcr.io and Docker Hub after the maintainer approves.
- New dependencies: official vendor libraries and servers only; anything third-party needs the maintainer's approval and a line in [NOTICE](NOTICE).
- Ideas and bugs: [open an issue](https://github.com/nnthanh101/1xops/issues).

## Licence

Apache-2.0 ([LICENSE](LICENSE)). Copyright, trademarks and every third-party component: [NOTICE](NOTICE).
