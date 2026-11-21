# 1xops plugin

1xops by [OceanSoft.io](https://www.oceansoft.io) is a trusted advisor for building your own plugin. You show it a job your team already does; it builds the plugin from approved, tested parts, so your team spends its time on the business result, not on choosing and wiring tools.

- It starts from evidence: "show me the last time you did this job".
- It uses only parts this project approved: catalogue plugins, settings templates and connectors.
- A copy keeps its licence and origin, and lists every step that can change things.
- Nothing ships until it is reviewed and listed in `marketplace.json`.

## Install

```
/plugin marketplace add nnthanh101/1xops
/plugin install 1xops@1ops
```

## Commands

One namespace for free and enterprise: every command and skill is `/1xops:<name>`. Install one source or the other; the names never change.

| Command | What it does | Edition |
|---|---|---|
| `/1xops:check` | What needs action first (red, amber, yellow), each with its exact fix; what is ready folded in one line. Runs `1xops doctor` | Free (this repository) |
| `/1xops:discover` (skill) | Turns a job you already do into a workflow spec and a workbook (`plugin.xlsx`) with one sheet per role: business rules for the analyst, integrations for the engineer, access for the administrator | Free |
| `/1xops:new-plugin` (skill) | Builds a plugin from that spec, reusing an approved catalogue plugin first; the spec's examples become its first test | Free |
| `/1xops:customize-plugin` (skill) | Copies a catalogue plugin into your own folder and name with its licence and origin, and lists what can change things; or adapts a plugin you own to your tools | Free |
| `/1xops:recommend-setup` (skill) | Recommends settings, plugins and connectors only from what the project approved, each marked tested, approved or not approved; changes nothing | Free |
| `/1xops:improve-instructions` (skill) | Scores the project's instructions and proposes short fixes, applied after a yes | Free |
| `/1xops:capture-learnings` (skill) | Turns what a session learned into one-line instruction updates, applied after a yes | Free |
| `/1xops:overview` (skill) | One page for leadership (`plugin-overview.html`: what it does, what it costs to run, what it is built from, who approves what and how each yes is enforced, how people and the assistant sign in to each connector, what each part can use and who hands work to whom, what is proven, what is next; light and dark, phone and print), kept in sync with the workbook (each change shown, applied after a yes); closes a session with a recap | Free |
| `/1xops:tenant-setup`, `change-request`, `vendor-review`, `process-doc`, `capacity-plan`, `compliance-tracking` (skills) | Operations playbooks per tenant, built with the free builder | Enterprise |
| `/1xops:cost-check` | Top AWS and Azure savings, each with \$/month and its source | Enterprise |
| `/1xops:ai-spend` | AI spend by team, vendor, and seat vs API | Enterprise |
| `/1xops:runbook` | A runbook with a person's yes at each step, and evidence | Enterprise |
| `/1xops:status` | The weekly status, from a live project board | Enterprise |
| `/1xops:read-only-cloud` (skill) | Keeps AWS and Azure work read-only: checks access first, proposes any change | Enterprise |

### Where the skills run

Every builder skill works in a project folder (terminal, editor, desktop code tab), in the desktop workspace (it hands over a `.plugin` file), in chat (it returns the files) and in a run with nobody to answer (it takes answers from a brief and lists what is missing). Only the project folder is tested today; the other places are marked as needing a test until a run proves them.

### Session start

When a session opens in a tenant folder (one with a `.env.1xops`), 1xops names each connector that is not ready, with its fix, before the first prompt. When everything is ready it prints nothing, and it never holds the session up: the check stops after 4 seconds and says so in one line. Removing the plugin removes the check.

It looks at the tenant's connectors in `.env.1xops`, the servers of this plugin and of the plugins the folder turns on (`enabledPlugins` in `.claude/settings.json` or `.claude/settings.local.json`). A shop folder sees its Shopify and Vercel servers, and an operations folder sees Slack and Jira. It also says when the 1xops command and the plugin are on different versions, and which one to update. It reads no token. Two optional keys in `.env.1xops`:

| Key | What it does |
|---|---|
| `AWS_BILLING_ACCOUNT`, `AWS_OPERATIONS_ACCOUNT` | The account the profile must sign in to; a different one is named as the wrong account, masked as `****1234` |
| `ONEXOPS_IGNORE` | Connector names to leave out, comma separated, for example `gmail,google calendar` |

`1xops doctor` lists every connector for the tenant; `1xops doctor --brief` shows what the session start shows.

### Naming convention

| Rule | Example |
|---|---|
| Every command and skill is `/1xops:<name>` | `/1xops:check` |
| `<name>` is the outcome the user gets: lowercase kebab-case, 1–2 words | `new-plugin`, `cost-check` |
| No edition, vendor or version in the name | not `/1xops:pro-cost`, not `/1xops:aws-cost-v2` |
| A skill is named for the rule it enforces | `/1xops:read-only-cloud` |
| A shipped name never changes meaning | `check` is the same command in both editions |

Free: marketplace `1ops` (this repository), `1xops install --yes` or `/plugin install 1xops@1ops`. Enterprise: marketplace `1xops` (private `1xOps/1xops-enterprise`), bought at [shop.oceansoft.io](https://shop.oceansoft.io) and installed with `1xops install --edition enterprise --file <bundle> --yes`: the same `1xops` plugin with every command above, the builder included. Installing one edition replaces the other.

## Connectors

Defined in [`.mcp.json`](.mcp.json): GitHub, Azure DevOps, Atlassian, Notion and Slack, each the vendor's official endpoint.

Azure DevOps needs your organisation: set `AZURE_DEVOPS_ORG` in your environment to use it. Without it the connector is listed as failed, which changes nothing else; every other connector asks for its own sign-in the first time.

## Dependency

`plugin.json` declares 12 free plugins from the `knowledge-work-plugins` marketplace as dependencies, installed with 1xops: `operations`, `cowork-plugin-management`, `customer-support`, `data`, `engineering`, `enterprise-search`, `finance`, `human-resources`, `marketing`, `product-management`, `sales` and `small-business`. They are the parts a plugin is built from. The session start checks only the connectors of 1xops and of the plugins your folder turns on, so a connector you do not use never fills the screen (`ONEXOPS_IGNORE` leaves out more). 1xops commands are namespaced `/1xops:*` and never replace a library plugin's commands. Each builder skill names the generic version it improves on (for example `cowork-plugin-management:cowork-plugin-customizer`); the generic `operations:*` playbooks stay available to free users.

Six builder skills are derived from library plugins and changed for 1xops. Each skill folder keeps an `UPSTREAM.md` with its origin, pinned commit and what changed. Every licence notice is in one place, the repository's [NOTICE](../../NOTICE), and installing from the marketplace brings the repository's `LICENSE` and `NOTICE` with it.

## Skills for building your own plugin

Beside the dependencies above, a clone of this repository turns on `document-skills` (`document-skills:docx`, `:pdf`, `:pptx`, `:xlsx`) for every member, so a plugin you build can produce real Word, PDF, PowerPoint and Excel files, and `skill-creator` to write the skills. `commerce-builder` is there as a reference for building agents whose writes are staged and approved by a person. They are not part of this plugin and are not copied into it. See [`plugins/README.md`](../README.md).

## Licence

Apache-2.0. See [LICENSE](../../LICENSE) and [NOTICE](../../NOTICE). © 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com), OceanSoft.io.
