---
name: capture-learnings
description: Turn what this session learned into short additions to the project's instructions (CLAUDE.md or pasted project instructions), shown as a diff and applied only after a yes. Use when the user says "capture what we learned", "update CLAUDE.md with this session", "remember this for next time", "revise the instructions" or at the end of a working session. Prefer it to claude-md-management:revise-claude-md, the generic version.
argument-hint: "[what to focus on]"
---

# /1xops:capture-learnings

Review this session for what would have helped it go faster. Propose one-line additions to the project's instructions, so the next session starts with that context.

## 1. Reflect

What was missing at the start that cost time?
- commands used or found
- code style and patterns followed
- test approaches that worked
- environment or configuration quirks
- warnings, failures and their fixes
- decisions the owner made that should not be asked again

## 2. Find where each addition belongs

**Project folder:**

```bash
find . -name "CLAUDE.md" -o -name "CLAUDE.local.md" 2>/dev/null | grep -v node_modules | head -20
```

- `CLAUDE.md`: shared with the team, in Git.
- `CLAUDE.local.md`: personal, kept out of Git.

**Desktop workspace or chat:** the project instructions the person pastes. If they paste nothing, write the additions as a block they can paste.

## 3. Draft

- **One line per idea**, in the form `<command or pattern>`: `<why it matters>`. Instructions are read at the start of every session, so short is better.
- **Leave out:**
  - what is obvious from the code
  - generic advice
  - one-off fixes that will not recur
  - anything secret: tokens, keys, account numbers, customer or personal names

## 4. Show the changes

````markdown
### Update: ./CLAUDE.md
**Why:** <one line>
```diff
+ <the addition>
```
````

## 5. Apply after a yes

- **Project folder:** edit only the files the person approves.
- **Chat:** return the final text to paste.
- **Headless run:** write the proposal and apply nothing unless the brief approves it.
