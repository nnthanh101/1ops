# 0003. Follow the git standard; official dependencies only

- Status: accepted · 2026-11-17 · owner: Nhat-Thanh Nguyen
- Source: the owner's git standard (`landing-zone/adlc/plans/git-standard.md`)

## Decision

| Control | In this repository |
|---|---|
| authorship | Commits name the owner; no `-by:` trailers |
| hooks | `.githooks/pre-commit` and `commit-msg` are the standard copies; `pre-push` runs the 1ops quick checks; on per clone with `git config core.hooksPath .githooks` |
| pins | Every action is pinned to a full commit SHA, the version in a comment |
| triggers | GitHub Actions runs only for `main`, `v*` tags, the monthly schedule or by hand; `develop` and `feature/*` are checked locally with act |
| ci-identity | No stored cloud key; registry identity per [0002](0002-release-identity.md) |
| session-guard | `.claude/settings.json` asks before every git write; attribution is empty |
| secrets-history | gitleaks over the whole history finds nothing unreviewed |
| rules | Rulesets in `.github/rulesets/`: `develop` and `main` keep their history; `main` takes only a pull request |

Dependencies: official vendor libraries, servers and tools only, at the latest stable version. A third-party component needs the maintainer's approval first and a line in [NOTICE](../../NOTICE).

## Check

```bash
bash ../landing-zone/scripts/git-standard.sh audit .
```

## Consequences

- Pull requests into `develop` do not spend Actions minutes; their proof is the local act run, so it must happen before review.
- Hooks are advice and per clone: they can be skipped. The rulesets and the `main` pull request checks are the hard gate.
- Under act, the runner image `nnthanh101/runbooks:latest` brings its own Node and has no Docker CLI: `setup-node` and the image jobs are skipped there, and `docker build packages/python` covers the image locally. npm 12 in that image holds install scripts until approved, so the validator's own install script is run explicitly.
