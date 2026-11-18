# Settings templates: org, team, local, personal

Four real files, one per scope. `1xops setup` asks for the scope (default `team`) and `1xops config --scope <scope>` copies that file into place. It adds to what is already there and never overwrites it.

**Copilot mode:** `allow` runs on its own, `ask` waits for a person at each step, `deny` never runs. A tool that is not listed asks by default.

| | [org](org.json) | [team](team.json) | [local](local.json) | [personal](personal.json) |
|---|---|---|---|---|
| **Installed as** | `managed-settings.json` for IT to deploy | `.claude/settings.json`, committed | `.claude/settings.local.json`, not committed | `~/.claude/settings.json` |
| **Controlled by** | IT | the team | one person, one project | one person, every project |
| **Can a user override it?** | no | yes, in local | yes, in managed only | yes, in project files |
| **AWS and Azure: read** (`describe`, `list`, `get`, `show`) | allow | allow | allow | allow |
| **AWS and Azure: change** (create, update, delete, start, stop, `terraform apply`) | deny | deny | deny | deny |
| **AWS and Azure: reads that return a secret or token** | deny | deny | deny | deny |
| **GitHub (`gh`): read** (view, list, checks, diff) | allow | allow | allow | allow |
| **GitHub (`gh`): change** (create, edit, comment, merge, release, `gh api`) | ask | ask | ask | ask |
| **GitHub (`gh`): destructive** (delete or archive a repo or release) | deny | deny | deny | deny |
| **Jira and Confluence** | every call asks | every call asks | every call asks | every call asks |
| **Browser and computer automation: observe** (screenshot, read page, snapshot) | allow | allow | allow | allow |
| **Browser and computer automation: act** (click, type, navigate, upload, run script) | ask | ask | ask | ask |
| **Browser: run arbitrary code** (Playwright `run_code_unsafe`) | deny | deny | deny | deny |
| **Credentials** (`.env`, `~/.aws`, `~/.azure`, `~/.azure-reader`, `~/.config/gh`, `~/.ssh`) | deny | deny `.env`, ask the rest | same as team | deny `.env`, ask the rest |
| **Publishing** (`npm publish`, `uv publish`) | deny | deny | deny | not set |
| **Git writes** (commit, push, merge, tag, reset --hard, new branch) | ask | ask | ask | not set |
| **Force-push, push to `main`** | deny | ask | ask | not set |
| **Git reads** | allow | allow | allow | allow |
| **Everyday commands** (`mkdir`, `tree`, `cd`) | not set | not set | allow | allow |
| **Approved connectors** | only the listed servers | pre-approved | pre-approved | not set |
| **Enforced by IT** | yes (see below) | no | no | no |

The approved connectors are the ones `1xops` connects: AWS billing, CloudTrail, CloudWatch and security, Azure, Atlassian, and the plugin's GitHub, Azure DevOps, Notion and Slack. To approve another, add one `serverName` line to `org.json`.

## Why these rules
Each group follows a rule the owner already runs. The credential and publishing rules and the git set recur across the owner's real settings files, and the git set matches the git standard: ask before every git write, and sessions stage work for the owner to commit. Gmail and Calendar in those files already allow reads and deny writes, and the cloud rules apply the same model. Sessions sign in read-only, and the read-only sign-in is the real boundary.

## Limits to know
- Only the org file enforces. With `allowManagedPermissionRulesOnly` set, the team and local rules stop applying, by design.
- "Read" is decided by the command name. A name can hide a change, so the reads that return secrets (for example `secretsmanager get-secret-value`, `az account get-access-token`) are denied by name, and the sign-in itself should be read-only.
- Jira and Confluence: Atlassian groups its tools by permission and the tool names differ between versions, so every call asks. Limit the sign-in to read-only scopes to stop writes.
- A rule matches command text, not the program. Without the sandbox, a `curl` deny is not a boundary.
- Browser and computer tool names come from the owner's settings files and from the tools in use today. A renamed tool asks by default.
- The org keys come from the official documentation and have not been run on a live Claude Code here. The plugin servers are named `plugin:1xops:<server>`, the registration name the docs give, and that name is not confirmed against the allowlist.
- Where the org file lives: macOS `/Library/Application Support/ClaudeCode/`, Linux `/etc/claude-code/`, Windows `C:\Program Files\ClaudeCode\`.

Sources: [settings](https://code.claude.com/docs/en/settings), [managed settings](https://code.claude.com/docs/en/managed-settings), [permissions](https://code.claude.com/docs/en/permissions), [managed MCP](https://code.claude.com/docs/en/managed-mcp), [Atlassian supported tools](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/).
