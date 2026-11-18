#!/usr/bin/env bash
# Copy templates/settings/*.json into the Python and npm packages before any build, so PyPI, npm and the image ship the same files.
set -euo pipefail
cd "$(dirname "$0")/.."
for dir in packages/python/src/one_xops/templates/settings packages/npm/templates/settings; do
  rm -rf "$dir" && mkdir -p "$dir" && cp templates/settings/*.json "$dir/"
done
