#!/usr/bin/env bash
# git-guard: PreToolUse hook on Bash. Commits, merges and pushes into develop or main are the owner's manual job.
# A session may commit and push only on feature/* and open pull requests; it never merges them.
# Blocks (exit 2, reason on stderr) when a Bash command writes git history and either
#   - a repository it touches (the session folder, any `cd DIR`, any `git -C DIR`) is on develop or main, or
#   - the command names develop or main outside quotes (checkout develop && commit, push origin HEAD:main, …).
# Always blocks `gh pr merge`. Fails closed if it cannot read its input.
# Self-test: bash .claude/hooks/git-guard.sh --self-test
set -uo pipefail
PROTECTED='develop|main'
WRITE='git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+(commit|merge|push|cherry-pick|revert|am|rebase)([[:space:]]|$)'

judge() { # <command> <cwd>: prints a reason and returns 2 to block, returns 0 to allow
  local cmd=$1 cwd=$2 bare dir b dirs
  if printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]_-])gh[[:space:]]+pr[[:space:]]+merge([[:space:]]|$)'; then
    echo "git-guard: merging a pull request is the owner's manual job (develop and main)"; return 2; fi
  printf '%s' "$cmd" | grep -Eq "$WRITE" || return 0
  bare=$(printf '%s' "$cmd" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")   # ignore quoted text, e.g. commit messages
  # Step by step: a write that names develop or main, or any write after switching to them, is blocked.
  # Other steps may name them freely (gh pr create --base develop, git pull --ff-only origin develop).
  local step switched=0
  while IFS= read -r step; do
    if printf '%s' "$step" | grep -Eq "git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+(checkout|switch)([[:space:]]+-[^[:space:]]+)*[[:space:]]+($PROTECTED)([[:space:]]|$)"; then switched=1; fi
    printf '%s' "$step" | grep -Eq "$WRITE" || continue
    if [ "$switched" = 1 ] || printf '%s' "$step" | grep -Eq "(^|[[:space:]:/])($PROTECTED)([[:space:])]|$)"; then
      echo "git-guard: this step writes git history on develop or main; that is the owner's manual job"; return 2; fi
  done <<< "$(printf '%s' "$bare" | sed -E 's/(&&|\|\||;|\|)/\
/g')"
  dirs="$cwd"$'\n'"$(printf '%s' "$bare" | grep -Eo '(cd|-C)[[:space:]]+[^[:space:];&|]+' | awk '{print $2}')"
  while IFS= read -r dir; do
    [ -n "$dir" ] || continue
    case "$dir" in /*) ;; *) dir="$cwd/$dir" ;; esac
    b=$(git -C "$dir" branch --show-current 2>/dev/null) || continue
    case "$b" in develop|main) echo "git-guard: $dir is on $b; commits, merges and pushes there are the owner's manual job"; return 2 ;; esac
  done <<< "$dirs"
  return 0
}

if [ "${1:-}" = --self-test ]; then
  t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
  git -C "$t" init -q -b develop && git -C "$t" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
  git -C "$t" checkout -q -b feature/x
  ok=0 n=0
  expect() { n=$((n + 1)); judge "$2" "$3" >/dev/null; [ $? = "$1" ] && ok=$((ok + 1)) || echo "  [FAIL] expected $1: $2"; }
  expect 0 'git commit -m "fix main page"' "$t"                 # feature branch; "main" only inside the message
  expect 0 'git push -u origin feature/x' "$t"
  expect 2 'git checkout develop && git commit -m x' "$t"
  expect 2 'git push origin HEAD:main' "$t"
  expect 2 'gh pr merge 3 --squash' "$t"
  expect 0 'git status && git log -1' "$t"
  expect 0 'git commit -m x && gh pr create --base develop --title y' "$t"   # opening a PR to develop is allowed
  expect 0 'git push -u origin feature/x && gh pr create --base main' "$t"
  expect 2 'git checkout -q main && git push' "$t"
  git -C "$t" checkout -q develop
  expect 2 'git commit -m x' "$t"
  expect 2 "cd $t && git cherry-pick abc" /
  expect 2 "git -C $t push" /
  expect 0 'git pull --ff-only origin develop' "$t"             # syncing develop is allowed
  echo "git-guard self-test: $ok/$n cases as expected"; [ "$ok" = "$n" ]; exit $?
fi

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || { echo "git-guard: cannot read the hook input" >&2; exit 2; }
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
[ -n "$cmd" ] || exit 0
reason=$(judge "$cmd" "${cwd:-$PWD}"); rc=$?
[ $rc = 2 ] && { echo "$reason" >&2; exit 2; }
exit 0
