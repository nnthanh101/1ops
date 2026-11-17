#!/usr/bin/env bash
# status.sh - one screen for the owner and the C-suite: what customers can install today, the state of each story
# against its acceptance evidence, and CI health. Read-only (public registries and gh). Used by `task status`.
set -uo pipefail
R=nnthanh101/1xops

latest() { # channel name, command printing a version
  local v; v=$(eval "$2" 2>/dev/null); printf '  %-22s %s\n' "$1" "${v:-not published}"
}
echo "What customers can install today"
latest "PyPI 1xops" "curl -sf https://pypi.org/pypi/1xops/json | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"info\"][\"version\"])'"
latest "npm 1xops" "curl -sf https://registry.npmjs.org/1xops | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"dist-tags\"][\"latest\"])'"
latest "GitHub release" "gh release view -R $R --json tagName --jq .tagName"
echo
echo "Stories (open first; proof = acceptance comments on the issue)"
gh issue list -R $R --state all --limit 50 --json number,title,state,comments \
  --jq 'sort_by(.state) | reverse | .[] | "  #\(.number) \(.state|ascii_downcase) \(.title[0:70])  [\([.comments[]|select(.body|test("^\\*\\*(Acceptance|Evidence|1xops )"))]|length) proof]"'
echo
echo "Product health: full check on develop and main (latest run)"
for b in develop main; do
  gh run list -R $R -w release.yml -b "$b" -L 1 --json conclusion,createdAt --jq ".[] | \"  $b: \(.conclusion // \"running\") (\(.createdAt[0:16]))\""
done
