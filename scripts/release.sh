#!/usr/bin/env bash
# VERSION=x.y.z STORY=n release.sh (both optional) - ship a version and prove it, as one command (owner only: it commits the version bump,
# merges into main and pushes a tag, each after the owner's yes or the green checks). VERSION defaults to the next patch
# after the latest tag. Local first: the tests, the Validate workflow (act) and the image build run on this machine
# before anything is pushed. Then it merges develop into main once green, tags vVERSION, waits for the owner's one
# approval and the publish, installs the release from every channel in clean containers, and posts that proof on STORY.
# Used by `task release`.
set -euo pipefail
R=nnthanh101/1xops
cd "$(git rev-parse --show-toplevel)"
git fetch -q origin --tags
last=$(git tag --list 'v*' --sort=-v:refname | head -1); last=${last#v}
V=${VERSION:-$(echo "${last:-0.0.0}" | awk -F. '{print $1"."$2"."$3+1}')}
STORY=${STORY:-}
[ "$(git branch --show-current)" = develop ] || { echo "release: run it on develop"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "release: commit or stash your changes first"; exit 1; }
[ "$(git rev-parse origin/develop)" = "$(git rev-parse HEAD)" ] || { echo "release: this clone is not at origin/develop; pull or push first"; exit 1; }
git rev-parse -q --verify "refs/tags/v$V" >/dev/null && { echo "release: v$V already exists"; exit 1; }
echo "release: v$V (latest released: v${last:-none})"

mkdir -p tmp
echo "release: local check 1/3, tests"
task test >/dev/null || { echo "release: tests fail; run task test"; exit 1; }
echo "release: local check 2/3, the Validate workflow with act"
act pull_request -W .github/workflows/validate.yml --rm >tmp/act-release.log 2>&1 || { echo "release: Validate fails locally; see tmp/act-release.log"; exit 1; }
echo "release: local check 3/3, the image"
docker build -q --build-arg VERSION="$V" -t "1xops:release-check" packages/python >/dev/null \
  && [ "$(docker run --rm 1xops:release-check --version)" = "1xops $(grep -E '^version = ' packages/python/pyproject.toml | cut -d'"' -f2)" ] \
  || { echo "release: the image does not build or run"; exit 1; }

py=$(grep -E '^version = ' packages/python/pyproject.toml | cut -d'"' -f2)
js=$(node -p "require('./packages/npm/package.json').version")
if [ "$py" != "$V" ] || [ "$js" != "$V" ]; then
  sed -i.bak -E "s/^version = \"[^\"]+\"/version = \"$V\"/" packages/python/pyproject.toml && rm packages/python/pyproject.toml.bak
  npm pkg set version="$V" --prefix packages/npm
  uv lock --project packages/python -q
  git --no-pager diff --stat
  read -r -p "release: commit and push the version bump $py -> $V to develop? [y/N] " ok
  [ "$ok" = y ] || { git checkout -- packages/python/pyproject.toml packages/python/uv.lock packages/npm/package.json; echo "release: stopped; nothing pushed"; exit 1; }
  git commit -q -m "chore: release v$V${STORY:+ (Refs #$STORY)}" packages/python/pyproject.toml packages/python/uv.lock packages/npm/package.json
  git push -q origin develop
fi

pr=$(gh pr list -R $R --base main --head develop --state open --json number --jq '.[0].number // empty')
[ -n "$pr" ] || pr=$(gh pr create -R $R --base main --head develop --title "release: v$V" --body "Release v$V" | grep -oE '[0-9]+$')
echo "release: pull request #$pr; waiting for its checks"
gh pr checks "$pr" -R $R --watch --fail-fast
gh pr merge "$pr" -R $R --merge
git fetch -q origin
git tag "v$V" origin/main
git push -q origin "v$V"

run=""
for _ in $(seq 30); do
  run=$(gh run list -R $R -w release.yml -b "v$V" -L 1 --json databaseId --jq '.[0].databaseId // empty')
  [ -n "$run" ] && break
  sleep 2
done
[ -n "$run" ] || { echo "release: no Release run started for v$V; see https://github.com/$R/actions"; exit 1; }
echo "release: approve the 'release' environment once: https://github.com/$R/actions/runs/$run"
gh run watch "$run" -R $R --exit-status >/dev/null || { echo "release: the Release run failed; see the link above"; exit 1; }

mkdir -p tmp
proof=tmp/evidence-$V.md
set +e; bash scripts/verify-release.sh "$V" | tee "$proof"; failed=${PIPESTATUS[0]}; set -e
[ -n "$STORY" ] && gh issue comment "$STORY" -R $R --body-file "$proof"
[ "$failed" -eq 0 ] || { echo "release: v$V is published but $failed check(s) failed; the story stays open"; exit 1; }
echo "release: v$V shipped and proven${STORY:+; proof posted on #$STORY}"
