---
name: discover
description: Turn a job the team already does into a workflow spec a plugin can be built from, starting from "show me the last time you did this". Use when the user says "I want a plugin for", "automate our review", "build a plugin for this job", "where do I start", "what should my plugin do" or "discover", or before /1xops:new-plugin when there is no spec yet. Works in a project folder, the desktop workspace, chat and headless runs.
argument-hint: "<the job, or a previous report, ticket or spreadsheet>"
---

# /1xops:discover

Build the spec from evidence of a job the team already does, not from a wish list of features. A previous report, ticket, handover or redacted spreadsheet shows four things:
- the real output
- who decides
- the words the team uses
- the exceptions

Ask for one first: **"Show me the last time you did this job."** If there is none, ask them to describe the last time, step by step, and mark the spec "from memory".

Write the questions in plain language, one step at a time. Never ask for passwords, keys or tokens.

## Who decides what

Three roles each own a part of the spec. Do not make one person answer for all three. Mark each section with its owner, and leave a section open for the right person rather than guessing.

| Role | Decides | 1xops handles |
|---|---|---|
| Analyst or business owner (FinOps lead, delivery lead) | business rules: what is useful, exclusions, thresholds, confidence, the report | collecting the evidence, reconciling it |
| Engineer (platform, cloud) | sources and integrations: accounts, services, time range, output format | checking sign-ins and connectors, a repeatable install |
| Administrator (security, customer admin) | access: data scope, approved destinations, permissions, revocation | a reviewable configuration and an audit record |

## The seven steps

| # | Ask | Write into the spec |
|---|---|---|
| 1 | Establish the job: "What decision did your last one support? Who acted on it? How often do you repeat it, and how long does it take?" | named owner, trigger, current artefact, frequency, baseline time and cost per run |
| 2 | Define a useful result: "What makes a finding actionable? Which recommendations do you routinely dismiss?" | acceptance rules, exclusions, one worked example of a good result and one of a dismissed one |
| 3 | Choose the minimum data: "Which accounts, projects and periods are in scope? Do we need metrics to judge utilisation?" | a source list bound to one tenant, expected account or project identifiers, permitted time range; each source mapped to an approved connector or marked "not approved yet" |
| 4 | Define authority: "May it read, draft a ticket, file it after approval, or change a resource?" | one permission per operation (read · draft · file after a yes · change after a yes · never), the approver, approved output destinations |
| 5 | Customise with a sample: "Here is a sample result from made-up data. What would you change?" | the changes they asked for, the sample, and the rule each change implies |
| 6 | Prove the run: "Does this reproduce your last one closely enough that the team would use it?" | how it will be compared with the previous artefact, the reviewer, the pass mark, known differences |
| 7 | Improve the next run: "When a finding is accepted, rejected, duplicated or later proved wrong, who records it?" | where corrections are kept, the replay set (at least five past cases), how a change is approved and rolled back |

### Rules for the steps
- **Step 3.**
  - Name connectors from the project's approved list: catalogue plugins' `.mcp.json`, `CONNECTORS.md`, or the owner's list.
  - In a project folder with the command line installed, run `1xops doctor --brief`. It is read-only and shows which connectors are ready. Record what it says, not what you expect.
  - A source with no approved connector stays in the spec as a gap.
- **Step 4.**
  - Default every operation to the least: read, or draft.
  - Anything that changes a resource needs a named approver.
- **Step 5.**
  - Use synthetic or redacted data only.
  - Never put a real account number, customer name or person's name into the sample.
- **Steps 6 and 7.** These define how the plugin is judged. Without them the spec is not ready for `/1xops:new-plugin`. Say so.

## Write the spec

- **Project folder:** write `workflows/<job-slug>/spec.md` from `references/workflow-spec.md`. Put the redacted previous artefact and the worked examples in `workflows/<job-slug>/examples/`. Change no other file.
- **Desktop workspace:** write the same files to the outputs folder.
- **Chat:** show the spec in full in one message so it can be saved.
- **Headless run:**
  - Take answers from the brief or an existing spec.
  - List every question left unanswered under `Open questions`.
  - Stop before step 5 if steps 1 to 4 are not answered.

End with:
- what is decided, and by whom
- what is still open, and for which role
- the next step: `/1xops:new-plugin workflows/<job-slug>/spec.md`, or `/1xops:customize-plugin` when one catalogue plugin already does most of the job
