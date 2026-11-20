# Workflow spec: <job name>

| | |
|---|---|
| Status | draft · ready to build · built · in use |
| Evidence | <previous artefact in `examples/`, or "from memory"> |
| Tenant | <one tenant: company, team or customer> |
| Version | 0.1.0 (previous working version: <none or tag>) |

## 1. The job (owner: business owner)
- Decision it supports:
- Who acts on it (named owner):
- Trigger and frequency:
- Current artefact:
- Baseline: <minutes per run> by <role>, <runs per month>, reviewer <role>, cost per run <figure or "not measured">

## 2. A useful result (owner: analyst)
- A finding is actionable when:
- Routinely dismissed (exclusions):
- Thresholds and confidence:
- Worked example of a good result: `examples/good-1.md`
- Worked example of a dismissed result: `examples/dismissed-1.md`

## 3. Minimum data (owner: engineer)
| Source | Identifier expected | Time range | Approved connector | Doctor status |
|---|---|---|---|---|
| | | | <name or "not approved yet"> | <ready · signed out · missing · not checked> |

## 4. Authority (owner: administrator)
| Operation | Permission | Approver | Destination |
|---|---|---|---|
| Read costs | read | — | — |
| Draft a ticket | draft | — | <project> |
| File a ticket | after a yes | <name or role> | <project> |
| Change a resource | never · after a yes | <name or role> | — |

## 5. Customisation from the sample
| Change asked for | Rule it implies |
|---|---|

## 6. Proof of the first run
- Compared with: <previous artefact>
- Reviewer and pass mark:
- Known differences:
- Result: accepted · rejected · open

## 7. Improvement
- Corrections recorded in:
- Replay set: <at least five past cases in `examples/`>
- A change is approved by <role> and rolled back by <how>

## Open questions
| Question | For role |
|---|---|
