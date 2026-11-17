# 1xops: rules for sessions working in this repo

Owner and only IP holder: nnthanh101 | oceansoft.io. Public prose (README, docs, issues) names no AI vendor, tool or "agent".

## What ships
- One product, three native channels, the same commands and byte-identical output files:
  PyPI = native Python (`packages/python`), npm = native Node.js (`packages/npm`, no dependencies), Docker image.
  No channel may need another channel's runtime. Never ship a wrapper or launcher.
- Docker image: `FROM nnthanh101/runbooks:prod`, pinned by digest, built from `uv.lock` (house style: adlc-framework/.devcontainer).
  Bump the digest when runbooks is rebuilt. Never a separate base image for 1xops.
- Settings live in `.env.1xops` (non-secret `KEY=value`; secret-looking keys are refused). Guided setup: `1xops setup`.
- Dependencies: latest stable, official only. A new third party needs the owner's yes and a line in `NOTICE`.

## How to work
- `task` lists everything; logic lives in `scripts/`, decisions in `docs/adr/`. Add code only with a named business purpose.
- Git: work on `feature/*`, prove it with `task test` and `task ci`, stage it on `develop` (`git merge --squash`),
  delete the branch. The owner commits and pushes. Never commit, push, tag, publish or approve a deployment.
- Guard rails advise or ask; they never block the owner.
- Cloud access is read-only. Sessions use only read-only sign-ins: an AWS read-only role, from `AWS_BILLING_PROFILE` / `AWS_OPERATIONS_PROFILE`, never a typed name; an Azure Reader identity in its own `AZURE_CONFIG_DIR`, never the owner's own login. Run `1xops doctor` before the first cloud call; a row saying `can change things` means stop. Any AWS or Azure write asks first (`.claude/settings.json`), and the session proposes it, the owner runs it. Follow skill `read-only-cloud` (plugins/1xops). The identity is the boundary; the rules only ask.

## Definition of done
A criterion is done only when it is proven on what customers install (the published package, in a clean container)
and the command and its real output are posted on the issue. `task release VERSION=x.y.z STORY=n` does this.
Commits say `Refs #N`, never `Closes`. Sessions move a story to Approval at most; only the owner closes it.

## Mistakes already made here. Do not repeat them
| Mistake | Rule |
|---|---|
| The npm package was a launcher that needed Python and uv, kept only to read YAML | Native code per channel; change the file format before adding a runtime |
| `cmd \| tail; echo $?` reported tail's exit code; zsh did not word-split `$X`; empty output was read as a pass | Capture the exit code of the command itself (`cmd >log; echo $?` or `PIPESTATUS`); a check that printed nothing failed |
| A test harness error (non-root image writing to `/`) looked like a product failure | Before reporting a failure, prove the check can pass, under the same user and paths the customer has |
| An issue closed by `Closes #13` with criteria unproven | `Refs #N`; proof on the published artifact first |
| A Dockerfile written from scratch on `python:3.14-slim` (386 MB, unpinned, unlocked) | Reuse the owner's platform images and their conventions first; measure before and after |
| `1xops doctor` (17 Nov 2026) found the default Azure login on the owner's Mac can change things | Sessions never use the owner's own cloud login; read-only identity only, checked with `1xops doctor` first |
| A blocking git hook, a GitHub App, two approvals for one release, four tasks for one goal | Least that delivers the outcome; one command, one approval |
