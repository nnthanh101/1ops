# 0001. One repository, four ways in

- Status: accepted · 2026-11-17 · owner: Nhat-Thanh Nguyen
- Story: [#13](https://github.com/nnthanh101/1xops/issues/13)

## Context

End users should get 1xops with one command, whatever they already use. The free base plugins upstream keep evolving and must be tracked without copying their text into this repository.

## Decision

| Concern | Decision |
|---|---|
| Upstream base plugins | Git submodule `upstream/knowledge-work-plugins`, pinned to a commit; `plugins/operations` is a relative link into it. A monthly workflow opens a pull request that moves the pin. |
| Plugin installs | Unchanged: the marketplace lists only `plugins/1xops`, which depends on the base plugin through its own marketplace. The link is for clones and local development. |
| Command line | One implementation, Python, in `packages/python` (PyPI `1xops`, import `one_xops`, command `1xops`; PyPI refused the earlier name `1ops` as too similar to the existing `iops`). |
| npm | `packages/npm` is a **native Node.js** command line (Node 24 built-ins, no dependencies) with the same commands and output files as the Python one. Each channel is native to its runtime: npm needs only Node.js, PyPI only Python, the image only Docker (owner decision 17 Nov 2026; the earlier npm launcher, which needed Python and uv, was a mistake). |
| Container | Built from `packages/python`; published to ghcr.io and mirrored to Docker Hub ([0002](0002-release-identity.md)). |
| Layout | Language packages live under `packages/`, never at the root: the root is the plugin marketplace, and every marketplace install fetches it. |
| Configuration | `.env.1xops` (plain `KEY=value`) holds non-secret values, readable by the shell, Python and Node.js without a library; shared files keep `${VAR}` references, because the host expands them from the shell environment only (measured 2026-11-17). |

## Consequences

- `git clone --recurse-submodules` gives the plugin plus the pinned upstream; a plain clone leaves the link dangling until `git submodule update --init`.
- Two implementations must stay identical: both test suites cover the same cases, the connector profiles have one source (the npm package copies them in when packed), and CI checks both versions match. On 17 Nov 2026 both produced byte-identical files from the same input.
- What if the upstream moves `operations/`: the bump workflow stops before opening a pull request, and the pin stays where it was.
