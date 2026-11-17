#!/usr/bin/env bash
# release.sh VERSION [STORY] - ship a version and prove it, as one command (owner only: it merges into main and
# pushes a tag). Checks, then merges develop into main once green, tags vVERSION, waits for the owner's one approval
# and the publish, installs the release from every channel in clean containers, and posts that proof on STORY.
# Used by `task release`.
set -euo pipefail
V=${1:?usage: release.sh VERSION [STORY]}
STORY=${2:-}
R=nnthanh101/1xops
cd "$(git rev-parse --show-toplevel)"

py=$(grep -E '^version = ' packages/python/pyproject.toml | cut -d'"' -f2)
js=$(node -p "require('./packages/npm/package.json').version")
if [ "$py" != "$V" ] || [ "$js" != "$V" ]; then
  echo "release: the packages say $py (Python) and $js (Node.js), not $V. Set it, commit and push, then run again:"
  echo "  sed -i '' -E 's/^version = \"[^\"]+\"/version = \"$V\"/' packages/python/pyproject.toml && npm pkg set version=$V --prefix packages/npm && uv lock --project packages/python -q"
  exit 1
fi
git fetch -q origin
[ "$(git rev-parse origin/develop)" = "$(git rev-parse HEAD)" ] || { echo "release: push develop first; this clone is not at origin/develop"; exit 1; }
git rev-parse -q --verify "refs/tags/v$V" >/dev/null && { echo "release: v$V already exists"; exit 1; }

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
