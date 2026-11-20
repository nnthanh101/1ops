# Origin of /1xops:customize-plugin

| | |
|---|---|
| Copied from | `cowork-plugin-management/skills/cowork-plugin-customizer` (plugin `cowork-plugin-management`) |
| Repository | https://github.com/anthropics/knowledge-work-plugins |
| Pinned commit | `e91a134584eb798bac7fb0379358006a2b63b965` |
| Copied on | 2026-11-20 |
| Licence | Apache-2.0: the repository's `LICENSE`; every third party is listed in its `NOTICE` |
| Modifications | Copyright 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com), OceanSoft.io (oceansoft.io), Apache-2.0 |

## What 1xops changed

- Renamed by outcome; SKILL.md rewritten: runs in a project folder, the desktop workspace, chat and headless runs instead of aborting outside the desktop workspace.
- Added Fork mode and `scripts/fork.sh`: copy into the team's own name, keep licence and origin, list what can change things, never edit `marketplace.json`.
- Placeholder search ignores code and reference files that only teach the pattern; connectors limited to approved ones; registry tools named as host-specific.
- `references/` and `examples/` kept as copied, plus one note in `references/mcp-servers.md`.

## Review before it ships

- script: scripts/fork.sh (copies files into a new folder; with --notice, appends one line to NOTICE)
