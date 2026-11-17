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
| npm | `packages/npm` is a launcher that runs the same PyPI version through uv. No second implementation. |
| Container | Built from `packages/python`; published to ghcr.io and mirrored to Docker Hub ([0002](0002-release-identity.md)). |
| Layout | Language packages live under `packages/`, never at the root: the root is the plugin marketplace, and every marketplace install fetches it. |
| Configuration | `1xops.yaml` holds non-secret values; shared files keep `${VAR}` references, because the host expands them from the shell environment only (measured 2026-11-17). |

## Consequences

- `git clone --recurse-submodules` gives the plugin plus the pinned upstream; a plain clone leaves the link dangling until `git submodule update --init`.
- The npm launcher needs uv on the machine, and its version must equal the PyPI version; CI checks both versions match.
- What if the upstream moves `operations/`: the bump workflow stops before opening a pull request, and the pin stays where it was.
