#!/usr/bin/env bash
# verify-release.sh VERSION - prove what customers receive: install 1xops VERSION from each channel in a clean
# container and run the same checks. Prints a Markdown evidence table; exit 0 only when every channel passes.
# Read-only on the registries; needs Docker. `task release` runs it; run it alone to re-prove a live version.
set -uo pipefail
V=${1:?usage: verify-release.sh VERSION}
fails=0

# The checks every channel must pass, run inside the container as `1xops` (one string, run by sh -c).
CHECKS='set -e
v=$(1xops --version)
1xops profiles >/dev/null
mkdir -p /tmp/org && 1xops config --scope org --out /tmp/org --connectors aws azure itsm --yes >/dev/null
grep -q "@azure/mcp@" /tmp/org/managed-mcp.json && ! grep -q "@latest" /tmp/org/managed-mcp.json
grep -q "mcp__atlassian__\*" /tmp/org/managed-settings.json
mkdir -p /tmp/p && if 1xops config --scope local --dir /tmp/p --connectors aws --yes >/dev/null 2>&1; then exit 3; fi
[ -z "$(ls -A /tmp/p)" ]
echo "$v; profiles, org config (pinned, Jira asks first), local scope writes nothing without the host CLI"'

row() { # channel, image, install command
  local out
  if out=$(docker run --rm --pull always --entrypoint sh "$2" -c "$3 && $CHECKS" 2>&1 | tail -1) && [[ "$out" == "1xops $V;"* ]]; then
    echo "| $1 | pass | $out |"
  else
    echo "| $1 | **FAIL** | ${out:-no output} |"; fails=$((fails + 1))
  fi
}

echo "**1xops $V, verified $(date -u +%Y-%m-%dT%H:%MZ) in clean containers** (\`scripts/verify-release.sh $V\`)"
echo
echo "| Channel | Result | Output |"
echo "|---|---|---|"
row "PyPI (python:3.14-slim)" python:3.14-slim "pip install -q --root-user-action=ignore 1xops==$V >/dev/null 2>&1"
row "npm (node:24-slim, no Python)" node:24-slim "npm install -g --silent 1xops@$V >/dev/null 2>&1"
row "Docker Hub nnthanh101/1xops:$V" "nnthanh101/1xops:$V" "true"
row "ghcr.io/nnthanh101/1xops:$V" "ghcr.io/nnthanh101/1xops:$V" "true"
hub=$(docker buildx imagetools inspect "nnthanh101/1xops:$V" 2>/dev/null | awk '/^Digest/{print $2}')
gh=$(docker buildx imagetools inspect "ghcr.io/nnthanh101/1xops:$V" 2>/dev/null | awk '/^Digest/{print $2}')
if [ -n "$hub" ] && [ "$hub" = "$gh" ]; then echo "| Same image on both registries | pass | \`$hub\` |"; else echo "| Same image on both registries | **FAIL** | Docker Hub ${hub:-none}, ghcr.io ${gh:-none} |"; fails=$((fails + 1)); fi
echo
[ "$fails" -eq 0 ] && echo "All channels pass." || echo "$fails check(s) failed."
exit "$fails"
