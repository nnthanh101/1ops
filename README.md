# 🥇 ONE 🧰 Cloud & AI Operations ⚙️

**Reduce cloud and AI costs. Automate operational work. Keep your team in control.**

1xops is a free, open-source toolkit from [OceanSoft.io](https://www.oceansoft.io) for engineering teams on AWS, Azure and AI services. It connects your team's assistant to your cloud accounts and your Jira and Confluence, read-only, in a few minutes, for one person, a team or a whole organisation.

> **Status:** v0.2 is published on [PyPI](https://pypi.org/project/1xops/), [npm](https://www.npmjs.com/package/1xops), [Docker Hub](https://hub.docker.com/r/nnthanh101/1xops) and [ghcr.io](https://github.com/users/nnthanh101/packages/container/package/1xops).

## What you can do today

| You are | You get |
|---|---|
| A platform lead | One command sets up the same connections and safeguards for every team, project or person, from one file |
| An engineer | A check of what is installed and signed in on your machine, with the fix for anything missing |
| A security or compliance lead | Connections to your cloud accounts and Jira that can read but not change anything, and a preview of every change before it is made |

## Planned

| Outcome | For | Milestone |
|---|---|---|
| Every session starts by naming the broken connectors, with the fix | SREs, on-call engineers | [v0.3](https://github.com/nnthanh101/1xops/milestone/2) |
| The assistant asks before any AWS or Azure write, or a call on an expired sign-in or the wrong account | Cloud engineers | [v0.3](https://github.com/nnthanh101/1xops/milestone/2) |
| Runbooks, change requests, status reports and risk assessments from your own tools, read-only, in 15 minutes | Platform engineers | [v0.3](https://github.com/nnthanh101/1xops/milestone/2) |

Cost checks, change requests from a Terraform plan, AI spend, evidenced runbooks and status from the project board are in the enterprise edition at [shop.oceansoft.io](https://shop.oceansoft.io).

## Get started

```bash
uv tool install 1xops     # or: npm install -g 1xops  (Node.js only, no Python)
1xops install --yes       # add the 1xops plugin to your assistant
1xops setup               # choose connectors; every change is shown before it is written
```

Then, in your assistant, run `/1xops:check`. Free and included: `/1xops:tenant-setup` for one settings file per tenant, then `/1xops:change-request`, `/1xops:vendor-review`, `/1xops:process-doc`, `/1xops:capacity-plan` and `/1xops:compliance-tracking`, each drafted for that tenant and filed only after your yes.

**Upgrade to the enterprise edition:** buy it at [shop.oceansoft.io](https://shop.oceansoft.io), download the bundle from your order, then run `1xops install --edition enterprise --file 1xops-enterprise-x.y.z.tar.gz --yes`. Same `/1xops:*` names, one plugin: the free edition is replaced, nothing to relearn. `1xops doctor` shows the installed edition. It shows each connector as **ready**, **signed out** or **missing**, with the exact fix, and changes nothing. The same check runs on the command line as `1xops doctor`. See [setup](docs/setup.md).

## Your data stays yours

- **Read-only identities.** Connect with read-only sign-ins only: an AWS read-only role, an Azure Reader identity. `1xops doctor` shows the access of each sign-in and flags any that can change things.
- **Read-only connections.** AWS, Azure and Jira/Confluence are connected through each vendor's own server, pinned to a known version. Azure runs in read-only mode, and every Jira or Confluence action asks first.
- **Nothing changes until you say yes.** Every configuration change is shown first and written only when you confirm.
- **No secrets in files.** Sign-in stays with AWS SSO, `az login` and Atlassian's own sign-in.

## Free vs paid

| | 1xops (this repository) | OceanSoft Cloud & AI Operations |
|---|---|---|
| Price | Free, Apache-2.0 | Fixed-price assessment, then monthly |
| Who runs it | You, on your own systems | OceanSoft, with your team |
| What you get | Self-serve setup, checks and playbooks | **Assessment:** a read-only review of your AWS, Azure and AI spend, with priced findings, evidence and a 90-day plan. **Managed:** OceanSoft runs the approved automations and reports verified savings every month. |
| Where | GitHub | [www.oceansoft.io](https://www.oceansoft.io) · [shop.oceansoft.io](https://shop.oceansoft.io) |

OceanSoft helps NZ and Australian businesses implement and maintain practical AWS, Azure and AI workflows.

## Contributing

Ideas and bugs: [open an issue](https://github.com/nnthanh101/1xops/issues). To contribute code, start with [setup](docs/setup.md).

## Licence

Apache-2.0 ([LICENSE](LICENSE)). Copyright, trademarks and third-party components: [NOTICE](NOTICE).
