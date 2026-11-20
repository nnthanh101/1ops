# Origin of /1xops:new-plugin

| | |
|---|---|
| Copied from | `cowork-plugin-management/skills/create-cowork-plugin` (plugin `cowork-plugin-management`) |
| Repository | https://github.com/anthropics/knowledge-work-plugins |
| Pinned commit | `e91a134584eb798bac7fb0379358006a2b63b965` |
| Copied on | 2026-11-20 |
| Licence | Apache-2.0, `LICENSE` |

## What 1xops changed

- Renamed by outcome; SKILL.md rewritten: starts from a workflow spec (/1xops:discover), reuses an approved catalogue plugin before building, adds the spec's examples as evaluation cases, delivers per place.
- `references/component-schemas.md`: hooks example wrapped in a top-level "hooks" object; hook decisions updated to allow, deny, ask.
- `references/example-plugins.md` kept as copied.

## Review before it ships

- nothing runs commands; it writes plugin files after the person approves the plan
