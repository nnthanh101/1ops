# 0001. One repository, four ways in

- Status: accepted · 2026-11-17 · owner: Nhat-Thanh Nguyen
- Story: [#13](https://github.com/nnthanh101/1xops/issues/13)

## Context

End users should get 1xops with one command, whatever they already use. The free base plugins upstream keep evolving and must be tracked without copying their text into this repository.

## Decision

| Concern | Decision |
|---|---|
| Upstream library | One git submodule per vendor under `upstream/`, each pinned to a commit and never shipped: `knowledge-work-plugins`, `agent-toolkit-for-aws` (19 Nov 2026), later others. A monthly workflow moves every pin in one pull request. Picks and rejections are recorded in `upstream/README.md` (owner decision 19 Nov 2026: customers see only 1xops). |
| Plugin installs | `plugins/` holds only `1xops` and reviewed copies, never a link; `.claude-plugin/marketplace.json` decides what ships (the Release workflow refuses a link). A pick enters 1xops as a copied `/1xops:<outcome>` skill with its licence and NOTICE line, or as a dependency installed from its vendor's own marketplace, as the 12 base plugins are. |
| Command line | One implementation, Python, in `packages/python` (PyPI `1xops`, import `one_xops`, command `1xops`; PyPI refused the earlier name `1ops` as too similar to the existing `iops`). |
| npm | `packages/npm` is a **native Node.js** command line (Node 24 built-ins, no dependencies) with the same commands and output files as the Python one. Each channel is native to its runtime: npm needs only Node.js, PyPI only Python, the image only Docker (owner decision 17 Nov 2026; the earlier npm launcher, which needed Python and uv, was a mistake). |
| Container | Built from `packages/python`; published to ghcr.io and mirrored to Docker Hub ([0002](0002-release-identity.md)). |
| Layout | Language packages live under `packages/`, never at the root: the root is the plugin marketplace, and every marketplace install fetches it. |
| Configuration | `.env.1xops` (plain `KEY=value`) holds non-secret values, readable by the shell, Python and Node.js without a library; shared files keep `${VAR}` references, because the host expands them from the shell environment only (measured 2026-11-17). |

## Consequences

- `git clone --recurse-submodules` gives the plugin plus the pinned library; a plain clone works without it, since nothing in `plugins/` points into `upstream/`.
- Two implementations must stay identical: both test suites cover the same cases, the connector profiles have one source (the npm package copies them in when packed), and CI checks both versions match. On 17 Nov 2026 both produced byte-identical files from the same input.
- What if an upstream moves or removes a plugin 1xops depends on: the bump workflow stops before opening a pull request, and every pin stays where it was.
