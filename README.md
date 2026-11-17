# 1xops 🧰 Cloud & AI Operations ⚙️

**Reduce cloud and AI costs. Automate operational work. Keep your team in control.**

1xops is a free, open-source toolkit from [OceanSoft.io](https://www.oceansoft.io) for engineering teams on AWS, Azure and AI services. It connects your team's assistant to your cloud accounts and your Jira and Confluence, read-only, in a few minutes, for one person, a team or a whole organisation.

> **Status:** the first release (v0.2) is in review. The commands below work once it is published.

## What you can do today

| You are | You get |
|---|---|
| A platform lead | One command sets up the same connections and safeguards for every team, project or person, from one file |
| An engineer | A check of what is installed and signed in on your machine, with the fix for anything missing |
| A security or compliance lead | Connections to your cloud accounts and Jira that can read but not change anything, and a preview of every change before it is made |

## Planned

| Outcome | For | Milestone |
|---|---|---|
| The top 3 AWS savings, each with \$/month and where the figure came from | CTOs, cloud leads | [v0.3](https://github.com/nnthanh101/1xops/milestone/2) |
| The same for Azure subscriptions | Engineering leads | [v0.3](https://github.com/nnthanh101/1xops/milestone/2) |
| A change request ready for your change board, from a real Terraform plan | Change managers | [v0.4](https://github.com/nnthanh101/1xops/milestone/3) |
| Last month's AI spend by team and vendor | FinOps leads | [v0.4](https://github.com/nnthanh101/1xops/milestone/3) |
| Runbooks that wait for a person's yes at each step and keep a record | On-call engineers | [v0.5](https://github.com/nnthanh101/1xops/milestone/4) |
| The weekly status report, straight from the project board | Delivery leads | [v0.5](https://github.com/nnthanh101/1xops/milestone/4) |

## Get started

```bash
uvx 1xops doctor          # what is installed and signed in, and how to fix the rest
uvx 1xops install --yes   # install the plugin
uvx 1xops setup           # answer a few questions; see every change before it is written
```

Also available through npm and as a container image. See [setup](docs/setup.md).

## Your data stays yours

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
