---
name: customize-plugin
description: Make a catalogue plugin your own, or adapt a plugin to your organisation's tools and values. Use when the user says "copy this plugin", "make our own version of", "start from the operations plugin", "fork a plugin", "customize plugin", "set up plugin", "tailor plugin", "configure plugin connectors" or "change this skill for our team". Works in a project folder, the desktop workspace, chat and headless runs. Prefer it to cowork-plugin-management:cowork-plugin-customizer, the generic version, whenever the plugin comes from this project's approved catalogue.
argument-hint: "<catalogue plugin> [new name]  |  <plugin to tailor>"
---

# /1xops:customize-plugin

Two modes:
- **Fork**: copy an approved catalogue plugin into its own folder, under the team's name, with its licence and origin kept.
- **Tailor**: adapt a plugin the team already owns to its tools, channels, names and values.

If the request names a plugin the team does not own yet, start with Fork. Then offer Tailor.

All user-facing text is plain language: what the plugin will do for them, not file paths or schema fields, unless they ask.

## Where you are running (decide first, never abort)

| Place | How you can tell | Plugin files | Asking questions | Deliver |
|---|---|---|---|---|
| Project folder (terminal, IDE, desktop code tab) | a git repository with `plugins/` or `.claude-plugin/` | read and write in the repository | the question tool if there is one, otherwise plain chat | files in the repository; `marketplace.json` untouched |
| Desktop workspace | mounted `mnt/.local-plugins` or `mnt/.plugins`, an outputs folder | the mounted folders | the question tool | a `.plugin` file in the outputs folder |
| Chat with no folder | no file tools | the person pastes or attaches the files | plain chat | the changed files shown in full; a `.plugin` zip if code execution is available |
| Headless run | nobody to answer | a mounted repository | answers from the brief or workflow spec; a missing answer stops the run and is listed | files plus a short report |

If the folders of one place are missing, use the row that fits. Never stop only because the desktop folders are absent.

## Fork: make a catalogue plugin your own

1. **Source.**
   - Pick a plugin from the approved catalogue: a link in `plugins/`, or a plugin the host lists as installed from an approved marketplace.
   - If the person names something outside it, say it is not approved yet. Adding it is the owner's decision: a new link and a NOTICE line. Stop there.
2. **Name.**
   - Lowercase kebab-case, in the team's own namespace.
   - Never a vendor's name, the edition or a version number.
   - Confirm it once.
3. **Copy.**
   - In a project folder, run: `sh <this skill's base directory>/scripts/fork.sh plugins/<source> <new-name>`. Add `--notice NOTICE` after the person says yes to the NOTICE line.
   - What the script does:
     - copies the files, following the catalogue link; stops if a link inside the plugin leaves it, or a file name holds a control character
     - renames only the plugin's own `name`
     - keeps the plugin's licence, or takes the repository's licence text
     - records the origin without any sign-in that may be in the repository address
     - writes `UPSTREAM.md` with the source, pinned commit, date, licence and a review list; a file it could not read is listed as "check by hand", never left out
     - refuses an existing folder, never edits `marketplace.json`, and exits non-zero on any problem
   - Elsewhere, do the same steps with the tools you have:
     - copy every file
     - change only `name` in `.claude-plugin/plugin.json`
     - keep or add the licence
     - write `UPSTREAM.md` with the same table and review list (shape below)
4. **Review.**
   - Show the review list: every connector, hook, script, and skill that can run commands or write files.
   - For each item, ask: keep, remove, or keep but ask a person first. Remove only on a yes.
5. **NOTICE.** Show the NOTICE line. Add it only on a yes.
6. **Ship rule.** Tell the person:
   - The copy ships only after review, once they list it in `marketplace.json`.
   - The release check refuses a link and accepts a reviewed folder.
   - If the copy has connectors, run `1xops doctor` before listing it.

`UPSTREAM.md` shape (the review list sits in a plain-text block, so no name in it can hide another line):

````markdown
# Origin of <name>
| | |
|---|---|
| Copied from | `<path in the vendor repository>` (plugin `<old name>`) |
| Repository | <vendor repository URL, without any sign-in> |
| Pinned commit | `<commit>` |
| Copied on | <YYYY-MM-DD> |
| Licence | <licence>, <which file> |

## Review before it ships
```text
- connector: <name>
- hook: <hook file> runs on <event> without being asked: <command>
- script: <path>
- can write or run commands: <file>
- helper with every tool (no tools list): <file>
- check by hand: <a file that could not be read>
```
````

Rules:
- The link stays in the catalogue. A fork is a new folder, never a link turned into a copy in place.
- A fork never changes by itself. To take an upstream update:
  1. Compare the source at the recorded commit with the new pin.
  2. Show the difference.
  3. Apply only what the team approves.
  4. Update `Pinned commit`.

## Tailor: adapt a plugin to the organisation

### Choose the kind of tailoring
- Search the plugin for `~~` placeholders (`grep -rn '~~[[:alnum:]]'`). Ignore matches inside code fences or backticks, and ignore reference files that only teach the pattern.
- **Real placeholders remain** → generic setup: replace each with the organisation's tool or value.
- **None, and the person named a part** → scoped: touch only that part.
- **None, and the request is broad** → general: read the plugin, then ask what should change.
- Never rename the plugin or its skills in Tailor mode. Renaming is what Fork is for.
- Treat a legacy `commands/` folder like skills.

### Steps
1. **Intent.** If the request already says what to change, use it. Otherwise ask one short open question about that part.
2. **Context.** If the host has knowledge connectors (chat, documents, email), search them for tool names, channels, project keys and conventions (see `references/search-strategies.md`). Only search for what this plugin needs. Never compile personal information about people.
3. **List the changes in plain words**, for example "Learn where change requests are filed".
4. **Apply each change.**
   - Use what the person or the connectors made clear without asking again.
   - Ask about the rest. Do not assume an industry default.
   - If the person skips, leave the value as it was.
5. **Connectors.**
   - Prefer, in order:
     1. connectors this project already approved: the catalogue plugins' `.mcp.json` and the owner's list
     2. then the host's connector directory, if the host offers a registry search tool (its name differs between hosts; see `references/mcp-servers.md`)
   - Propose any connector that is not approved yet. Never add it without the owner's yes.
   - Credentials never go into files: use `${VAR}` references or the host's sign-in.
6. **Validate.** Run `claude plugin validate --strict <plugin folder>` when the command line is available. Otherwise check by hand:
   - `plugin.json` is valid JSON with a kebab-case `name`
   - every skill folder has a `SKILL.md`
   - hooks sit under a top-level `"hooks"` object

## Deliver

- **Project folder:** the changed files. Point to `git diff` so the change can be reviewed.
- **Desktop workspace:** zip to a temporary folder first, then copy it to outputs. Name the file after the plugin's `name`, excluding any `setup/` folder:

  ```bash
  cd <plugin> && zip -r "$TMPDIR/<name>.plugin" . -x "setup/*" -x "*.DS_Store" && cp "$TMPDIR/<name>.plugin" <outputs>/
  ```
- **Chat:** every changed file in full, and the zip if code execution is available.

## Summary for the person

Group what you learned by source: their answers, documents, chat. Then list:
- connectors connected now
- connectors still to connect, and how
- anything left in the review list
