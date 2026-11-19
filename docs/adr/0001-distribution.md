# 0001. One repository, four ways in

- Status: accepted · 2026-11-17 · owner: Nhat-Thanh Nguyen
- Story: [#13](https://github.com/nnthanh101/1xops/issues/13)

## Context

End users should get 1xops with one command, whatever they already use. The free base plugins upstream keep evolving and must be tracked without copying their text into this repository.

## Decision

| Concern | Decision |
|---|---|
| Upstream base plugins | Git submodules, each pinned to a commit: `upstream/knowledge-work-plugins` and `upstream/agent-toolkit-for-aws` (added 19 Nov 2026). Each of their plugins is a relative link in `plugins/`, so `plugins/` is the one catalogue to build from. A monthly workflow opens a pull request that moves the `knowledge-work-plugins` pin; the AWS pin is moved by hand (`git submodule update --remote upstream/agent-toolkit-for-aws`) and reviewed the same way. |
| Plugin installs | `.claude-plugin/marketplace.json` decides what ships, and lists only reviewed folders, never a link (the Release workflow refuses one). Today that is `plugins/1xops`, which depends on the base plugins through their own marketplace. A plugin built from the library is a copy in its own folder, with its licence and NOTICE line. |
| Command line | One implementation, Python, in `packages/python` (PyPI `1xops`, import `one_xops`, command `1xops`; PyPI refused the earlier name `1ops` as too similar to the existing `iops`). |
| npm | `packages/npm` is a **native Node.js** command line (Node 24 built-ins, no dependencies) with the same commands and output files as the Python one. Each channel is native to its runtime: npm needs only Node.js, PyPI only Python, the image only Docker (owner decision 17 Nov 2026; the earlier npm launcher, which needed Python and uv, was a mistake). |
| Container | Built from `packages/python`; published to ghcr.io and mirrored to Docker Hub ([0002](0002-release-identity.md)). |
| Layout | Language packages live under `packages/`, never at the root: the root is the plugin marketplace, and every marketplace install fetches it. |
| Configuration | `.env.1xops` (plain `KEY=value`) holds non-secret values, readable by the shell, Python and Node.js without a library; shared files keep `${VAR}` references, because the host expands them from the shell environment only (measured 2026-11-17). |

## Consequences

- `git clone --recurse-submodules` gives the plugin plus the pinned upstream; a plain clone leaves the link dangling until `git submodule update --init`.
- Two implementations must stay identical: both test suites cover the same cases, the connector profiles have one source (the npm package copies them in when packed), and CI checks both versions match. On 17 Nov 2026 both produced byte-identical files from the same input.
- What if the upstream moves `operations/`: the bump workflow stops before opening a pull request, and the pin stays where it was.
