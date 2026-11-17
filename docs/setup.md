# Setup

Two audiences: people who **use** 1xops, and the maintainer who **releases** it. Decisions behind each step are in [docs/adr](adr/).

## Use 1xops

| Step | Command |
|---|---|
| Check prerequisites and sign-in | `uvx 1xops doctor` |
| Install the plugin | `uvx 1xops install --yes` |
| Configure (guided) | `uvx 1xops setup` → writes `1xops.yaml`, shows the diff, asks before writing |
| Configure (file) | `uvx 1xops config --file 1xops.yaml --yes` |
| Team or org scope: load your values | `eval "$(uvx 1xops env)"` |

Scopes, the `1xops.yaml` format and the connector profiles are in the [command-line README](../packages/python/README.md). Keep a personal `1xops.yaml` out of git.

## Contribute (every clone)

```bash
git clone --recurse-submodules https://github.com/nnthanh101/1xops && cd 1xops
git config core.hooksPath .githooks      # secret scan, commit message and quick checks, as advice
act pull_request -W .github/workflows/validate.yml   # the full CI, locally, before any pull request
```

Rules: one capability per pull request, proven on a real asset (fixtures are for tests only); official vendor libraries only, and anything third-party needs the maintainer's approval and a line in [NOTICE](../NOTICE).

Flow ([ADR 0003](adr/0003-git-standard.md)): `feature/*` is proven locally, then lands on `develop`; `develop` reaches `main` only by pull request; each release is a `v*` tag on `main`. GitHub Actions runs only for `main`, tags, the monthly schedule or by hand.

## Release (maintainer, once)

Each step names who does it. Tokens are typed only by the maintainer, never by a session, and never into a file in the repository.

| # | Step | Where | Who | Done when |
|---|---|---|---|---|
| 1 | Rulesets: `develop` and `main` cannot be force-pushed or deleted; `main` takes only a pull request | `gh api` (below) | session, with the maintainer's yes | `bash ../landing-zone/scripts/git-standard.sh audit .` shows `rules` pass |
| 2 | Environment `release`: required reviewer = maintainer; deployments from tags `v*` only | Settings → Environments | session, with the maintainer's yes | the release waits for approval |
| 3 | PyPI trusted publisher (pending): project `1xops` (registered 2026-11-17), owner `nnthanh101`, repo `1xops`, workflow `release.yml`, environment `release` | pypi.org → Your account → Publishing | maintainer, browser | listed under pending publishers |
| 4 | npm, first release only: granular token, *publish* on package `1xops`, 7-day expiry | npmjs.com → Access Tokens | maintainer | `gh secret set NPM_TOKEN --env release -R nnthanh101/1xops` |
| 5 | Docker Hub mirror: access token, *Read & Write*, repository `nnthanh101/1xops` | hub.docker.com → Personal access tokens | maintainer | `gh secret set DOCKERHUB_USERNAME --env release` and `gh secret set DOCKERHUB_TOKEN --env release` |
| 6 | Actions may open pull requests (monthly upstream bump) | Settings → Actions → General | session, with the maintainer's yes | the bump workflow opens its PR |
| 7 | Local act secrets | `cp .secrets.act.example .secrets`, filled in by the maintainer | maintainer | `.secrets` stays untracked |

After the first release:

| # | Step | Who |
|---|---|---|
| 8 | npm → package `1xops` → Settings → Trusted publisher: GitHub Actions, `nnthanh101/1xops`, `release.yml`, environment `release`; then `gh secret delete NPM_TOKEN --env release` and revoke the token | maintainer |
| 9 | ghcr.io package `1xops` → visibility *public*, linked to the repository | maintainer |
| 10 | Review the Docker Hub waiver by its date in [ADR 0002](adr/0002-release-identity.md) | maintainer |

Step 1 commands (read them before running; each applies one ruleset):

```bash
gh api -X POST repos/nnthanh101/1xops/rulesets --input .github/rulesets/develop.json
gh api -X POST repos/nnthanh101/1xops/rulesets --input .github/rulesets/main.json
```

## Release a version

1. Bump the same version in `packages/python/pyproject.toml` and `packages/npm/package.json` on a `feature/*` branch; land on `develop`.
2. Open the pull request `develop` → `main`; CI runs; merge.
3. Tag on `main`: `git tag v0.2.0 && git push origin v0.2.0`.
4. Approve the `release` environment. PyPI goes first, then npm (the launcher runs the PyPI version), with the images in parallel.
5. Check: `uvx 1xops@0.2.0 --version`, `npx 1xops@0.2.0 --version`, `docker run --rm ghcr.io/nnthanh101/1xops:0.2.0 --version`.
