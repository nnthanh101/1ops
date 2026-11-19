# Plugins: one catalogue to build from

Every plugin you can build from sits in this folder, so you start a new plugin from proven, free, open-source parts instead of from scratch.

| Kind | In this folder as | Ships to customers |
|---|---|---|
| **Ours** | a folder (`1xops`) | yes, when listed in [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) |
| **Library** | a link into `upstream/` (`upstream/knowledge-work-plugins`, `upstream/agent-toolkit-for-aws`), each pinned | no, never: a source to copy from |
| **Your own** | a folder you copied from the library, renamed into your namespace | only after review, and only once it is listed in `marketplace.json` |

**Build your own.** Start from a library plugin with `cowork-plugin-management` (a `1xops plugin new --from <library>/<name>` command is planned). It copies the plugin once into its own folder here, under your name, with its licence and NOTICE line kept. A link never changes into a copy in place: the copy is a new folder, and the link stays as the library entry.

**Review before it ships.** A library plugin can carry servers that change things. For example, the AWS library's `aws-core`, `aws-data-analytics` and `aws-startup-advisor` use a server that can call any AWS API, so a read-only role is what keeps them read-only. Check every skill and server of a copy, and run `1xops doctor`, before you list it in `marketplace.json`.

**Library updates.** A library changes only when its pin in `upstream/` is moved; the links follow that pin. Copies never change by themselves.
