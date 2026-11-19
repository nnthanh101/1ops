# Plugins

This folder holds only what customers get: the `1xops` plugin, and any plugin copied from the library and reviewed. [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) decides what ships, and lists only folders here, never a link (the Release workflow refuses one).

**Where plugins come from.** Free, open-source plugins from several vendors sit in [`upstream/`](../upstream/README.md), each vendor a pinned submodule that is never shipped. We filter that library, pick the best, and bring a pick into `1xops` in one of two ways:

- **As a skill:** copy the part you need into `plugins/1xops/skills/`, name it `/1xops:<outcome>`, keep its licence, and add its line to `NOTICE`.
- **As a dependency:** list the whole plugin in `plugins/1xops/.claude-plugin/plugin.json`; it installs from its own vendor's marketplace with 1xops. The 12 base plugins come in this way.

**Review before it ships.** A library plugin can carry servers or steps that change things; for example, some AWS plugins use a server that can call any AWS API, so only a read-only role keeps them read-only. Check every skill and server of a pick, and run `1xops doctor`, before it is listed. Record the decision, picked or not, in [`upstream/README.md`](../upstream/README.md).

**Build your own.** Start from a library plugin with `cowork-plugin-management` (installed with 1xops; a `1xops plugin new --from <vendor>/<name>` command is planned). It copies the plugin once into its own folder under your name, with its licence and NOTICE line.
