# 1ops

An enterprise platform and operations add-on for Anthropic's free **operations** plugin. Anthropic's plugin gives the general playbooks: change request, runbook, risk, compliance, capacity, status, vendor review and process. This add-on adds only what enterprise platform teams need on top:
- every connector checked before a playbook runs;
- figures taken from the real asset, each with its source;
- a person's yes before anything is written.

## How it builds on Anthropic's plugin

`plugin.json` declares `dependencies: ["operations@knowledge-work-plugins"]`, so installing this add-on also installs Anthropic's free plugin. Anthropic's commands stay `/operations:*`, and ours are `/1ops:*`. We never ship a plugin named `operations`: a same-name plugin replaces Anthropic's whole plugin, which we tested on 2026-11-16 and which matches the Claude Code docs on name conflicts.

## Install

```
/plugin marketplace add anthropics/knowledge-work-plugins
/plugin install operations@knowledge-work-plugins
/plugin marketplace add 1xOps/1ops      # private: your GitHub account needs access
/plugin install 1ops@1ops
```

Tested against `anthropics/knowledge-work-plugins` at e91a134584eb (operations 1.3.0).

## What it adds

| Capability | Status | Serves |
|---|---|---|
| Connector gate: `command-center check` before any playbook | Check shipped (#118); gate planned (#120) | Cloud engineer, SRE |
| Change request from a real Terraform plan, every replace and destroy flagged from the plan file | Planned (OPS-002, #82) | Change manager, cloud engineer |
| Status and compliance from live AWS, ServiceNow/JSM, Jira and GitHub, every figure with its source | Planned (OPS-003, OPS-005) | Platform & operations head, security analyst |

A capability ships only after it beats Anthropic's skill used alone, side by side, on a real asset.

Connectors in `.mcp.json` are vendor-official only: GitHub, Azure DevOps, Atlassian, Notion and Slack.

Copyright (c) 2026 Nhat-Thanh Nguyen. All rights reserved. See [LICENSE](LICENSE). "Anthropic" and "Claude" are named only to identify the required plugin. This add-on is not made or endorsed by Anthropic.
