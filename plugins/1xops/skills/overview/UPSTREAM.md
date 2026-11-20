# Origin of /1xops:overview

| | |
|---|---|
| Copied from | `.claude/skills/launch-your-agent/references/overview.css` and `overview-template.html`, and the close-out pattern of `.claude/skills/wrap-up` |
| Repository | https://github.com/1xOps/managed-agents (itself derived from Anthropic's Apache-2.0 reference skill; its notices are kept) |
| Pinned commit | `6d37c0836b33c3f2df1eb4ad26714fd29298c62d` |
| Copied on | 2026-11-20 |
| Licence | Apache-2.0: the repository's `LICENSE`; every third party is listed in its `NOTICE` |
| Modifications | Copyright 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com), OceanSoft.io |

## What 1xops changed

- `references/overview.css`: re-authored on 2026-11-20. It has its own palette (cool slate), type and spacing scale, and its own rules in place of the 64 lines still identical to Anthropic's original. Only bare syntax remains in common (`:root {`, `}`, one media query). The class names stay, so the template still works. Copyright: Nhat-Thanh Nguyen (nnthanh101@gmail.com), OceanSoft.io.
- `references/overview-template.html`: rewritten for a plugin instead of a managed agent:
  - The six primitive cards became skills, commands, connectors, hooks, agents and settings.
  - "Outcome" became the spec's proof of the first run.
  - Added: readiness from `/1xops:check`, origin and licence per copied part, and who approves each operation.
- `SKILL.md`: new. It writes the page from `plugin.xlsx` (data first, one sheet per role) and the plugin files after a build, keeps both in sync, refreshes it, and closes a session with a recap (the wrap-up pattern).

## Review before it ships

- Nothing runs commands except reading the plugin folder and, if installed, `1xops doctor --brief`.
- It writes only `plugin.xlsx`, `plugin-overview.html` and `overview.css` in the plugin's own folder, after the person says yes the first time.
