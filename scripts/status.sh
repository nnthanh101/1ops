#!/usr/bin/env bash
# status.sh - one screen for the owner and the C-suite: what customers can install today, the state of each story
# and the local proof, and CI health. Read-only (public registries and gh). Used by `task status`.
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
echo "Stories (open first)"
gh issue list -R $R --state all --limit 50 --json number,title,state \
  --jq 'sort_by(.state) | reverse | .[] | "  #\(.number) \(.state|ascii_downcase) \(.title[0:80])"'
echo
# Proof stays on this machine (CLAUDE.md: never posted, it can carry tenant names), so it is read from tmp/.
echo "Proof on this machine (tmp/, newest first)"
proofs=$(ls -t tmp/evidence-*.md tmp/ux/report.md 2>/dev/null)
if [ -z "$proofs" ]; then echo "  none: task ux proves a build, task release proves a published version"
else
  for f in $proofs; do
    printf '  %-26s %s  %s\n' "$f" "$(date -r "$f" '+%Y-%m-%d %H:%M' 2>/dev/null)" \
      "$(grep -cE '\b(FAIL|failed)\b' "$f" | sed 's/^0$/no failures/; s/^\([1-9][0-9]*\)$/\1 failure line(s)/')"
  done
fi
echo
echo "Product health: full check on develop and main (latest run)"
for b in develop main; do
  gh run list -R $R -w release.yml -b "$b" -L 1 --json conclusion,createdAt --jq ".[] | \"  $b: \(.conclusion // \"running\") (\(.createdAt[0:16]))\""
done
