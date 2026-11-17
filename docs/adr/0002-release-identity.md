# 0002. Release identity: short-lived first, one dated waiver

- Status: accepted · 2026-11-17 · owner: Nhat-Thanh Nguyen
- Story: [#13](https://github.com/nnthanh101/1xops/issues/13)

## Context

The git standard prefers a short-lived CI identity to any stored key. Each registry supports that differently.

## Decision

| Registry | Identity | Stored secret |
|---|---|---|
| PyPI `1xops` | Trusted publishing (OIDC), environment `release` | none (`PYPI_TOKEN` only for local act runs) |
| npm `1xops` | Trusted publishing (OIDC) from the second release; npm cannot register a publisher for a package that does not exist yet | `NPM_TOKEN` for the first release only: granular, publish on `1xops`, 7-day expiry, deleted after step 8 of [setup](../setup.md) |
| ghcr.io `nnthanh101/1xops` | The automatic `GITHUB_TOKEN`, `packages: write` on the image job only | none |
| Docker Hub `nnthanh101/1xops` | Access token; Docker Hub has no OIDC login for GitHub Actions | `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` — **waiver** below |

Every publish job runs in the `release` environment: deployments only from `v*` tags, and only after the maintainer approves. The first job refuses a tag that is not on `main` or a version that differs between the packages.

### Waiver: Docker Hub token

- Owner: Nhat-Thanh Nguyen (nnthanh101@gmail.com)
- Scope: one access token, *Read & Write*, repository `nnthanh101/1xops` only, held as a `release` environment secret
- Why: Docker Hub discoverability for end users; ghcr.io carries the same image with no stored key
- Review by: **2027-05-17**. Remove the mirror, or replace the token if Docker Hub offers OIDC by then.

## Consequences

- A leaked Docker Hub token can push only to that one repository, and only until it is revoked.
- What if the npm token is not deleted after the first release: it expires in 7 days; step 8 of the setup removes it sooner.
