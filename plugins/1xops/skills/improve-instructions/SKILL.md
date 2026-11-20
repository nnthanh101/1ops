---
name: improve-instructions
description: Audit and improve a project's instruction files (CLAUDE.md and its local and package versions, or project instructions pasted into chat), with a scored report first and changes only after a yes. Use when the user says "check our instructions", "audit CLAUDE.md", "improve CLAUDE.md", "fix the project instructions", "are our instructions current" or "project memory". Prefer it to claude-md-management:claude-md-improver, the generic version.
---

# /1xops:improve-instructions

Usage: `/1xops:improve-instructions [path or pasted instructions]`

Audit the instructions the assistant reads for this project, score them, and propose short, targeted improvements. Change nothing before the person approves the report.

## Where you are running

| Place | Instructions are | Apply changes |
|---|---|---|
| Project folder | instruction files on disk (below) | edit the approved files |
| Desktop workspace or chat | the project instructions the person pastes | return the improved text in full, to paste back |
| Headless run | files in the mounted repository | write the report; apply only what the brief approves |

## 1. Find the instruction files (project folder)

```bash
find . -name "CLAUDE.md" -o -name "CLAUDE.local.md" 2>/dev/null | grep -v node_modules | head -50
```

| Type | Location | Shared |
|---|---|---|
| Project root | `./CLAUDE.md` | yes, in Git |
| Personal | `./CLAUDE.local.md` | no; keep it out of Git |
| Personal, all projects | `~/.claude/CLAUDE.md` | no |
| Package or folder | `./packages/*/CLAUDE.md`, any subfolder | yes |

Instruction files in parent folders also apply, so in a monorepo read upwards too.

## 2. Score each file

Use `references/quality-criteria.md`.

| Criterion | Points | Check |
|---|---|---|
| Commands and workflows | 20 | build, test, release commands present and current |
| Architecture | 20 | the structure can be understood from it |
| Non-obvious patterns | 15 | gotchas and quirks recorded |
| Conciseness | 15 | no padding, no restating the code |
| Currency | 15 | matches the project today (check commands and paths exist) |
| Actionability | 15 | instructions can be followed as written |

Grades:

| Grade | Points |
|---|---|
| A | 90–100 |
| B | 70–89 |
| C | 50–69 |
| D | 30–49 |
| F | 0–29 |

## 3. Report first, always

```markdown
## Instruction quality report
- Files found: X · average score: X/100 · files needing an update: X

### 1. ./CLAUDE.md: XX/100 (grade X)
| Criterion | Score | Notes |
**Issues:** …
**Recommended additions:** …
```

## 4. Propose targeted changes

Follow `references/update-guidelines.md`.

- **Add only what helps the next session:** commands found, gotchas, relationships between parts, test approaches, configuration quirks.
- **Leave out:** what the code already shows, generic advice, one-off fixes, long explanations.
- **Show each change as a diff:**
  - the file
  - the addition or removal
  - one line on why

## 5. Apply after a yes

- **Project folder:** edit only the approved files, and keep their structure.
- **Chat:** return the full improved text.

Templates by project type are in `references/templates.md`.

Tips to share with the person:
- Keep commands copy-paste ready.
- Put personal preferences in `CLAUDE.local.md`, kept out of Git.
- Put defaults for every project in `~/.claude/CLAUDE.md`.
