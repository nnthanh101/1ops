# 1xops

Command line for [1xops by OceanSoft.io](https://github.com/nnthanh101/1xops): checks prerequisites, installs the 1xops plugin, and writes settings and read-only cloud connectors for an organisation, a team (or tenant folder), a project, or one person.

```bash
uvx 1xops doctor                       # prerequisites and read-only sign-in (account IDs masked)
uvx 1xops install --yes                # add the marketplaces and install the plugin
uvx 1xops setup                        # guided: asks a few questions, writes 1xops.yaml, shows the diff
uvx 1xops profiles                     # built-in connector profiles: aws, azure, itsm
uvx 1xops config --scope team --connectors aws itsm          # shows a diff
uvx 1xops config --scope team --connectors aws itsm --yes    # writes it
```

| Scope | Writes | Who it is for |
|---|---|---|
| `org` | `managed-settings.json`, `managed-mcp.json` in `--out`, for IT to deploy | Everyone in the organisation |
| `team` | `.claude/settings.json`, `.mcp.json` in `--dir` (a project or tenant folder) | Everyone on the project, via git |
| `local` | `.claude/settings.local.json` in `--dir`; connectors via the host CLI | You, in this project |
| `personal` | `~/.claude/settings.json`; connectors via the host CLI | You, in every project |

## 1xops.yaml

One file holds everything a person or team sets. It holds non-secret values only; secrets stay in AWS SSO, `az login` or the Atlassian sign-in.

```yaml
scope: team                       # org | team | local | personal
dir: .                            # project or tenant folder (team, local)
connectors:
  aws:
    AWS_BILLING_PROFILE: "billing-readonly"
    AWS_OPERATIONS_PROFILE: "ops-readonly"
    AWS_REGION: "ap-southeast-2"
  itsm: {}
  ./my-profile.json: {}           # your own profile
```

```bash
1xops config --file 1xops.yaml --yes    # apply it
eval "$(1xops env)"                    # team/org: load your values into the shell
```

- Keys are the `${VAR}` names each profile uses; `1xops profiles` lists them.
- At `team` and `org` scope the shared files keep `${VAR}`, so profile names and tenant IDs never reach git. The host reads these from your shell environment, so run `1xops env`.
- At `local` and `personal` scope the values are written into your private host configuration.
- Values must be quoted strings, and keys that look like secrets (`TOKEN`, `SECRET`, `PASSWORD`, `API_KEY`) are refused.
- Keep a personal `1xops.yaml` out of git.

## Rules

- Nothing changes without `--yes`.
- Existing values are never overwritten; only missing entries are added.
- Built-in profiles pin every server version and use `${VAR}` references for profiles, tokens and URLs, so no secret is written to a file.
- Your own profile is a JSON file with an `mcpServers` object: `--connectors ./my-profile.json`.

Licence: Apache-2.0. © 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com), OceanSoft.io. Licence, trademarks and third-party components: [NOTICE](https://github.com/nnthanh101/1xops/blob/develop/NOTICE).
