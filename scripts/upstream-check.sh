#!/bin/bash
# Customers see only 1xops; upstream/<vendor>/ is the library (plugins/README.md, upstream/README.md).
# Checks, read-only: plugins/ holds no links; each folder in it is a plugin; marketplace.json lists only those
# folders; every dependency of a shipped plugin is still in the pinned upstream that serves its marketplace.
# Run by the Release workflow on every change and by upstream-bump.yml before it opens a pull request.
# Usage: bash scripts/upstream-check.sh   (from the repository root; needs jq and initialised submodules)
set -uo pipefail
fail=0
bad() { echo "upstream-check: $*"; fail=1; }

for p in plugins/*; do
  [ -L "$p" ] && bad "$p is a link: plugins/ holds only 1xops and reviewed copies; the library stays in upstream/"
done
for p in plugins/*/; do
  [ -f "$p.claude-plugin/plugin.json" ] || bad "$p has no .claude-plugin/plugin.json"
done
for s in $(jq -r '.plugins[].source | strings' .claude-plugin/marketplace.json); do
  p=${s#./}
  { [ -d "$p" ] && [ ! -L "$p" ]; } || bad "$p is listed in marketplace.json but is a link or missing: copy and review it first"
done

# name@marketplace -> the upstream/ submodule whose own marketplace.json has that name
for dep in $(jq -r '.dependencies[]? | strings' plugins/*/.claude-plugin/plugin.json | sort -u); do
  name=${dep%@*} market=${dep#*@} dir=""
  for m in upstream/*/.claude-plugin/marketplace.json; do
    [ -f "$m" ] && [ "$(jq -r .name "$m")" = "$market" ] && dir=${m%/.claude-plugin/marketplace.json}
  done
  if [ -z "$dir" ]; then bad "$dep: no submodule in upstream/ serves marketplace $market"; continue; fi
  src=$(jq -r --arg n "$name" '.plugins[] | select(.name == $n) | .source | strings' "$dir/.claude-plugin/marketplace.json")
  { [ -n "$src" ] && [ -f "$dir/${src#./}/.claude-plugin/plugin.json" ]; } \
    || bad "$dep: not in $dir at its pin $(git -C "$dir" rev-parse --short HEAD 2>/dev/null)"
done

[ $fail -eq 0 ] && echo "upstream-check: plugins/ holds no links; every shipped plugin and dependency resolves"
exit $fail
