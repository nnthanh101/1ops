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
- Local first: run `task gate` (lint, tests, act, image, UX proof, as CI and a customer will) before saying done or asking for a commit.
- Git: work on `feature/*`, prove it with `task gate`, stage it on `develop` (`git merge --squash`),
  delete the branch. The owner commits and pushes. Never commit, push, tag, publish or approve a deployment.
- Guard rails advise or ask; they never block the owner.
- Cloud access is read-only. Sessions use only read-only sign-ins: an AWS read-only role, from `AWS_BILLING_PROFILE` / `AWS_OPERATIONS_PROFILE`, never a typed name; an Azure Reader identity in its own `AZURE_CONFIG_DIR`, never the owner's own login. Run `1xops doctor` before the first cloud call; a row saying `can change things` means stop. Any AWS or Azure write asks first (`.claude/settings.json`), and the session proposes it, the owner runs it. Follow skill `read-only-cloud` (plugins/1xops). The identity is the boundary; the rules only ask.

## Release standard
SemVer, tag `vX.Y.Z`, one version for PyPI, npm and the image. Next version = latest published + 1:
`task release STORY=n` is a patch (fixes, UX); `BUMP=minor` adds a command or capability; `BUMP=major` breaks a
command, file or setting. Commits follow Conventional Commits (`feat:`, `fix:`, `chore:`) and say `Refs #N`.

## Definition of done
A criterion is done only when it is proven end to end as a customer: the published package, installed and operated
in a real terminal (Terminal.app or iTerm2, screenshots with `screencapture`), read-only sign-ins and read-only
operations only. The proof stays local in `tmp/` and is summarised to the owner in chat; it is **never posted** on an
issue or anywhere public, because it can carry customer or tenant names. Write no new test code unless the owner asks; prove by running it end to end (`task ux`). Existing tests stay as the regression net.
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
| 0.2.4 shipped a misaligned table header; a literal `[bold]…[/]`, rows wrapped at 80 columns and 65 profiles listed twice reached the wizard. All 50 unit tests passed | A change to what a person sees is done only when seen: `task ux` (real terminal, clean container, checks + screenshots) passes, and the screenshots are looked at. Skill `visual-verify` (1ops-enterprise) |
| `rich` was removed to make stdout byte-identical, which cost the customer the UX | Byte-identical means the files and piped output. On a terminal, Python uses `rich` to the full (tables, colour, spinner, prompts) and Node.js draws the same natively |
| Release proof reported registry lag as a product failure, twice | The proof waits for the files an install fetches and retries a channel that printed nothing; it still fails a version that does not exist |
| A pty capture rendered to SVG was shown as a terminal screenshot | Say what it is. A real screenshot is `screencapture -l` of a Terminal.app or iTerm2 window; without Screen Recording permission, ask the owner to grant it or take it |
| CI failed on `ruff format --check` because `task test` never ran it and the change was handed over without act | `task gate` runs exactly what CI runs, locally, before every hand-over |
| A blocking git hook, a GitHub App, two approvals for one release, four tasks for one goal | Least that delivers the outcome; one command, one approval |
