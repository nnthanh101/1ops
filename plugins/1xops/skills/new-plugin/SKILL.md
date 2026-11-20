---
name: new-plugin
description: Build a new plugin from a workflow spec, using only approved catalogue parts. Use when the user says "build the plugin", "create a plugin", "make a new plugin", "scaffold a plugin", "turn this spec into a plugin" or "design a plugin". Works in a project folder, the desktop workspace, chat and headless runs. Prefer it to cowork-plugin-management:create-cowork-plugin, the generic version, whenever this project's approved catalogue is available.
argument-hint: "<workflow spec path, or a one-line description>"
---

# /1xops:new-plugin

Build a plugin that does one job the team already does, from approved parts, and prove it against the job's own examples.

Keep the conversation in plain language: what the plugin will do, not file paths or schema fields, unless the person asks.

## Where you are running

| Place | Write the plugin to | Deliver |
|---|---|---|
| Project folder | `plugins/<name>/` (never listed in `marketplace.json` by this skill) | the files; `git diff` to review |
| Desktop workspace | a temporary folder | a `.plugin` file in the outputs folder |
| Chat with no folder | — | every file in full; a `.plugin` zip if code execution is available |
| Headless run | the mounted repository | the files plus a report; unanswered design questions stop the run and are listed |

## Start from the job, not from components

1. **Spec.**
   - Read the workflow spec: `workflows/<job>/spec.md`, or the one the person gives.
   - If there is none, run `/1xops:discover` first. A one-line description is not enough to build from.
   - If the spec has no step 6 (proof) or step 7 (improvement), say so and stop.
2. **Reuse before building.**
   - Look in the approved catalogue first: links in `plugins/`, and plugins installed from approved marketplaces.
   - If one already does most of the job, use `/1xops:customize-plugin` to fork it. Then add only what is missing.
   - Build from scratch only when nothing fits, and say why.
3. **Plan the components.**
   - Show one table, including the types you decided not to use:

     | Component | Count | Purpose |
     |---|---|---|
     | Skills | 1 | <the job, as one skill> |
     | Connectors | n | <each from the spec's step 3, approved only> |
     | Agents | 0 | not needed |
     | Hooks | 0 | not needed |

   - Start with one skill per job.
   - Add agents or hooks only when the person asks and the spec needs them. A hook runs without being asked, so it needs the administrator's yes.
   - Get a yes before building.
4. **Design.**
   - Each skill:
     - its trigger phrases, from the words in the spec's evidence
     - its steps
     - the permission of each operation, from the spec's step 4
   - Each connector:
     - which approved server
     - how the person signs in
     - read-only first
   - Ask only what the spec leaves open, then confirm.

## Build

Create, in this order:
1. `.claude-plugin/plugin.json`:
   - `name` in kebab-case, in the team's own namespace
   - `version` `0.1.0`
   - `description`, `author` and `license`
2. One `skills/<job>/SKILL.md` per job. Write the body as instructions to follow, verb first:
   - Under 3,000 words, with detail in `references/`.
   - A third-person description with real trigger phrases.
   - Each operation states its permission from the spec. Anything above "read" waits for a person's yes, and names the approver.
   - Each finding names its source. The skill never presents an estimate as a measured figure.
3. `.mcp.json`, only for approved connectors from the spec:
   - Use `${VAR}` for every credential or host-specific value.
   - Never write a secret into a file.
   - Use HTTPS for remote servers.
4. `evals/<job>/`: the spec's worked examples (good, dismissed, and the replay set) as cases with their expected result. They are the plugin's first test.
5. `README.md`: what it does, who approves what, the connectors and how to sign in, and what has not been proven yet.
6. `UPSTREAM.md`, when any part was copied from the catalogue: the origin and the review list (see `/1xops:customize-plugin`).

Reference material:
- `references/component-schemas.md`: exact formats of skills, agents, hooks, connectors and commands
- `references/example-plugins.md`: three example plugins

Use `${CLAUDE_PLUGIN_ROOT}` for paths inside hooks and connector settings. Never hardcode an absolute path.

Use `~~category` placeholders only if the person says the plugin will be shared outside their organisation. Then add a `CONNECTORS.md` (see the references).

## Check and deliver

1. Summarise each component and its purpose. Ask for changes.
2. Validate:
   - With the command line: `claude plugin validate --strict plugins/<name>`.
   - Without it, check by hand:
     - `plugin.json` is valid JSON with a kebab-case `name`
     - every skill folder has a `SKILL.md`
     - hooks sit under a top-level `"hooks"` object
     - every referenced file exists
   - Fix every error before going on.
3. Run the job once on the spec's examples, with synthetic or redacted data. Show the result next to the expected one, with every difference. The reviewer named in the spec accepts or rejects it. Record the answer in the spec's step 6.
4. Deliver for the place you are running in (table above). Zip to a temporary folder first, then copy:

   ```bash
   cd <plugin> && zip -r "$TMPDIR/<name>.plugin" . -x "*.DS_Store" && cp "$TMPDIR/<name>.plugin" <outputs>/
   ```

5. Tell the person:
   - It ships only after review, once listed in `marketplace.json`.
   - Run `1xops doctor` first if it has connectors.
   - `/1xops:capture-learnings` keeps its instructions current after each run.
