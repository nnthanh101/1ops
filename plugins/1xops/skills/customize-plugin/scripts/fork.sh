#!/bin/sh
# Copy a catalogue plugin into its own folder under a new name, keep its licence and origin,
# and list everything in it that can run commands or change things. Never edits marketplace.json.
# Usage: fork.sh <source-plugin-folder> <new-name> [--dest <parent-folder>] [--notice <NOTICE file>]
set -eu

usage() { echo "usage: fork.sh <source-plugin-folder> <new-name> [--dest <parent>] [--notice <NOTICE>]" >&2; exit 2; }
[ $# -ge 2 ] || usage
src_in=$1; name=$2; shift 2
dest_parent=""; notice=""
while [ $# -gt 0 ]; do
  case $1 in
    --dest) [ $# -ge 2 ] || usage; dest_parent=$2; shift 2 ;;
    --notice) [ $# -ge 2 ] || usage; notice=$2; shift 2 ;;
    *) usage ;;
  esac
done

case $name in
  *[!a-z0-9-]*|-*|"") echo "name '$name' must be lowercase kebab-case (a-z, 0-9, -)" >&2; exit 2 ;;
esac
[ -d "$src_in" ] || { echo "source '$src_in' is not a folder" >&2; exit 2; }
src=$(cd "$src_in" && pwd -P)
[ -f "$src/.claude-plugin/plugin.json" ] || { echo "source '$src_in' has no .claude-plugin/plugin.json: not a plugin" >&2; exit 2; }
[ -n "$dest_parent" ] || dest_parent=$(dirname "$src_in")
dest="$dest_parent/$name"
[ ! -e "$dest" ] || { echo "'$dest' already exists: choose another name or remove it first" >&2; exit 3; }

# Origin: the git repository the source lives in, and the commit it is pinned at.
repo_url=unknown; commit=unknown; rel=$src
if top=$(git -C "$src" rev-parse --show-toplevel 2>/dev/null); then
  commit=$(git -C "$src" rev-parse HEAD)
  repo_url=$(git -C "$src" remote get-url origin 2>/dev/null || echo unknown)
  rel=${src#"$top"/}
fi
old_name=$(sed -n 's/^[[:space:]]*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$src/.claude-plugin/plugin.json" | head -n 1)

mkdir -p "$dest_parent"
cp -RL "$src" "$dest"

# Licence: keep the plugin's own; else take the repository's, cut at the end of the licence text.
licence_file=""
for f in LICENSE LICENSE.txt LICENSE.md COPYING; do
  [ -f "$dest/$f" ] && { licence_file="$f (the plugin's own)"; break; }
done
if [ -z "$licence_file" ] && [ -n "${top:-}" ] && [ -f "$top/LICENSE" ]; then
  if head -n 3 "$top/LICENSE" | grep -q "Apache License"; then
    last=$(grep -n "limitations under the License\." "$top/LICENSE" | tail -n 1 | cut -d: -f1)
    if [ -n "$last" ]; then head -n "$last" "$top/LICENSE" > "$dest/LICENSE"; else cp "$top/LICENSE" "$dest/LICENSE"; fi
  else
    cp "$top/LICENSE" "$dest/LICENSE"
  fi
  licence_file="LICENSE (copied from the repository root)"
fi
[ -n "$licence_file" ] || { echo "no licence found for '$src_in': copy stopped, '$dest' removed" >&2; rm -rf "$dest"; exit 4; }
licence_name=$(head -n 5 "$dest/LICENSE"* 2>/dev/null | grep -o -m 1 -E "Apache License|MIT License|BSD [0-9]-Clause|Mozilla Public License|GNU [A-Z ]*General Public License" || echo "see LICENSE")
[ "$licence_name" = "Apache License" ] && licence_name="Apache-2.0"

# Rename: only the plugin's own name, the first "name" key in plugin.json.
pj="$dest/.claude-plugin/plugin.json"
awk -v n="$name" 'done==0 && /"name"[[:space:]]*:/ { sub(/"name"[[:space:]]*:[[:space:]]*"[^"]*"/, "\"name\": \"" n "\""); done=1 } { print }' "$pj" > "$pj.tmp" && mv "$pj.tmp" "$pj"

# Review list: everything that can run a command, reach a service or change files.
review=$(
  cd "$dest"
  [ -f .mcp.json ] && awk '
    { buf = buf $0 "\n" }
    END {
      wrapped = (buf ~ /"mcpServers"[[:space:]]*:/); want = wrapped ? 2 : 1; depth = 0; n = length(buf); i = 1
      while (i <= n) {
        c = substr(buf, i, 1)
        if (c == "\"") {
          j = i + 1; key = ""
          while (j <= n && substr(buf, j, 1) != "\"") { if (substr(buf, j, 1) == "\\") j++; key = key substr(buf, j, 1); j++ }
          k = j + 1; while (k <= n && substr(buf, k, 1) ~ /[ \t\n\r]/) k++
          if (substr(buf, k, 1) == ":") { k++; while (k <= n && substr(buf, k, 1) ~ /[ \t\n\r]/) k++
            if (substr(buf, k, 1) == "{" && depth == want && key != "mcpServers") print "- connector: " key }
          i = j + 1; continue
        }
        if (c == "{") depth++; else if (c == "}") depth--
        i++
      }
    }' .mcp.json
  [ -f hooks/hooks.json ] && echo "- hook: hooks/hooks.json runs on events without being asked"
  find . -type f \( -name '*.sh' -o -name '*.py' -o -name '*.js' -o -name '*.mjs' -o -name '*.ts' -o -name '*.ps1' \) | sed 's|^\./||; s/^/- script: /'
  grep -rl -E '^(allowed-)?tools:.*(Bash|Write|Edit)' --include='*.md' . 2>/dev/null | sed 's|^\./||; s/^/- can write or run commands: /'
  grep -rl '!`' --include='*.md' . 2>/dev/null | sed 's|^\./||; s/^/- runs a shell command when loaded: /'
  true
)
[ -n "$review" ] || review="- nothing found that runs commands, reaches a service or changes files"

today=$(date +%Y-%m-%d)
notice_line="  $name  derived on $today from $repo_url ($rel, commit $commit)  $licence_name  $dest"
cat > "$dest/UPSTREAM.md" <<REC
# Origin of $name

| | |
|---|---|
| Copied from | \`$rel\` (plugin \`$old_name\`) |
| Repository | $repo_url |
| Pinned commit | \`$commit\` |
| Copied on | $today |
| Licence | $licence_name, $licence_file |

Changes from the source are this team's own. To take an upstream update, compare the source at the commit above with
the new pin, and apply only what the team approves. This folder never changes by itself.

## Review before it ships

Decide for each line: keep, remove, or keep but ask a person first. It ships only once it is listed in
\`marketplace.json\`, and the release check accepts only folders, never links.

$review
REC

if [ -n "$notice" ]; then
  [ -f "$notice" ] || { echo "NOTICE file '$notice' not found" >&2; exit 2; }
  if ! grep -q "derived on .* $dest\$" "$notice"; then
    [ -z "$(tail -c 1 "$notice")" ] || printf '\n' >> "$notice"
    printf '%s\n' "$notice_line" >> "$notice"
  fi
fi

echo "Copied $src_in to $dest as '$name' (was '$old_name')."
echo "Origin: $repo_url, $rel, commit $commit. Licence: $licence_name ($licence_file)."
echo "Review before it ships:"
printf '%s\n' "$review"
echo "NOTICE line:"
printf '%s\n' "$notice_line"
[ -n "$notice" ] && echo "(added to $notice)"
echo "marketplace.json was not changed."
