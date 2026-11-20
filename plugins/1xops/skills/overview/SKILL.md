---
name: overview
description: Show a plugin you built or copied as one page a CEO, a CTO or a security lead can read, covering what it does, what it is built from, who approves what, what is proven and what comes next. Then refresh it after every change, and close a session with a recap. Use when the user says "overview", "show me the plugin", "plugin page", "wrap up", "where does my plugin stand" or "share the plugin", and at the end of /1xops:new-plugin or /1xops:customize-plugin. Works in a project folder, the desktop workspace, chat and headless runs.
---

# /1xops:overview

Usage: `/1xops:overview [plugin folder]`. Without a folder, use the plugin built or copied in this session, or ask which one.

The page is the outcome of a build: one place where the buyer sees what they now own. Its facts come from the plugin's own files, so the page never says more than the folder proves.

## Two outputs, one set of facts

| File | For | What |
|---|---|---|
| `plugin.xlsx` | the people who own the rules | data first: one sheet per role (Job, Business rules, Integrations, Access, Proof, Next), plus Components filled from the folder and a hidden `_sync` sheet. Template: `../discover/references/plugin-template.xlsx` |
| `plugin-overview.html` | CEO, CTO, CFO, security lead, approver | one page from the same facts (template `references/overview-template.html`), light and dark, readable on a phone, printable |
| `overview.css` | the page | copied once from `references/overview.css`, linked and never inlined, never edited in the plugin |

All three live in the plugin's own folder; the workbook may also stay in `workflows/<job>/` where `/1xops:discover` wrote it. Before the first write, show the paths and ask for a yes. Write nothing else. Never touch `marketplace.json`.

## Keep the workbook and the plugin in sync

Not yet proven: this two-way sync has not run on a real plugin. Say so when you use it, show every difference before changing anything, and record the first real run.

Both can be edited: an analyst changes a threshold in Excel, and an engineer changes a skill in the folder.
- `_sync` holds a fingerprint (a hash) of each fact at the last sync.
- **Only one side changed a fact:** show the difference as a short table (fact, old, new, which side) and apply it to the other side after a yes.
- **Both sides changed the same fact:** show both values and let the person pick. Never merge silently.
- **A rule the owning role did not change:** never change it on its sheet without that role's yes. Name the role in the question.
- After a sync, update `_sync`, then refresh the page.

## 1. Read the facts

Read only what exists, and record each fact with the file it came from.

| Card on the page | Read from |
|---|---|
| Every role's decisions | `plugin.xlsx` (after the sync above) |
| Name, version, description, owner | `.claude-plugin/plugin.json` |
| The job, the owner, the decision it supports, the pass mark | the workflow spec (`workflows/<job>/spec.md`, linked in the plugin README) |
| Skills and commands, and what each can change | `skills/*/SKILL.md`, `commands/*.md` (frontmatter `allowed-tools`, and the operations table in the README) |
| Connectors | `.mcp.json`: name, host, read or write |
| Hooks | `hooks/hooks.json`: event and what it runs. Each hook is marked "runs without being asked" |
| Agents, settings | `agents/*.md`, `settings.json` |
| Origin and licence | `UPSTREAM.md` and the NOTICE line: source, pinned commit, what changed |
| Who approves each operation | the spec's authority table (step 4): read · draft · after a yes · never |
| Readiness | `1xops doctor --brief` if the command is installed (read-only), otherwise "not checked" |
| Proof | `evals/`, the spec's step 6 result, `claude plugin validate --strict` exit code if run in this session |
| Next versions | the spec's open questions and anything deferred in this session |

Rules:
- **Facts only.** A field with no source shows `not yet` (or `open`), never a guess.
- **No timings, money or volumes** unless the spec states them. Quote the owner's own words for the job and the value.
- **Mask account numbers** (`****1234`). Never name a customer or a person the spec does not name.

## 2. Write or refresh the page

- **First time:**
  - Copy `references/overview.css` next to the page.
  - Write `plugin-overview.html` from the template. Fill each `data-slot` (named `Sheet.field`) from the workbook or the plugin files, and delete the example content.
  - Keep the template's structure, its light and dark modes, the theme switch and its print styles.
- **Later:** Edit only the slots whose facts changed. Never rewrite the whole page.
- **Order on the page:** the outcome first, for leadership.
  1. The value in the owner's words.
  2. The business case: baseline, target, measured and cases passed, only figures the Job and Proof sheets hold.
  3. The decision asked of leadership, with who reviewed it.
  4. Then how it works, the parts, who approves what, the evals and the next versions, for the technical reviewers.
- **Brand:** the page wears the buyer's brand from the Brand sheet:
  - the display name, the logo (`assets/logo.png` in the plugin, with an emoji fallback) and the legal line;
  - two colour tokens on the root element: `style="--brand:#…; --brand-accent:#…"`.
  The stylesheet lightens the brand colour in dark mode. With no Brand sheet, keep the neutral defaults; never invent a brand.
- **State pill**, one of:
  - `PLANNED` (spec only)
  - `BUILT` (folder exists)
  - `VALIDATED` (strict validation passed)
  - `PROVEN` (the pass mark from the spec was met on a real case)
  - `LISTED` (in `marketplace.json`)

  The title attribute holds the one-line reason.
- Mark every skill, command, connector or hook that can change things with the `change` chip and its approver. Anything above "read" with no approver shows `approver: open` in red.

## 3. Show it

- **Project folder or desktop:** open the page (`open plugin-overview.html`, `xdg-open` on Linux, `start` on Windows) and say its path.
- **Chat:** return the page and the stylesheet as files, or in full if files are not available.
- **Headless:** write the files and list any `open` fields.

## 4. Wrap-up (when asked, or at the end of a build)

Reply in this order, short and in tables:
1. One sentence on what the buyer now owns, in their own words from the spec.
2. **What you own**: one row per component (skill, command, connector, hook, agent, setting): what it is, what it can change, who approves, and its card on the page.
3. **Proof**: what is proven (with the evidence file) and what is not yet.
4. **Next**: one or two next versions that matter most for this job, each with what it gives and what it needs. Everything else stays on the page's version rail.
5. A quiet hygiene sweep, mentioning only what the person must act on:
   - a secret-looking value in a file
   - a write with no approver
   - a copied part with no licence
   - an unlisted folder they think is shipped

Do not change the plugin here. Changes go through `/1xops:customize-plugin` or `/1xops:new-plugin`. To record what this session learned, use `/1xops:capture-learnings`.
