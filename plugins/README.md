# Plugins: build your own from proven free parts

This folder is the catalogue. It holds a link to each selected free, open-source plugin of trusted vendors, beside the plugins built from them, so every part you can build from is in one visible place.

| Kind | In this folder as | Ships to customers |
|---|---|---|
| **Library** | a link into `upstream/<vendor>/` (`knowledge-work-plugins`, `agent-toolkit-for-aws`, `shopify-ai-toolkit`, `vercel-plugin`, `hashicorp-agent-skills`, `superpowers`; more vendors to come), each pinned | never: a part to build from |
| **Worked example** | a folder: `1xops` | yes: it is listed in [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) |
| **Your own** | a folder you built from the library, under your own name | only after review, once you list it in your `marketplace.json` |

**1xops is the worked example.** It is built from this same catalogue, with the same parts and steps you use, so it proves the path end to end. Build your own 1xops-like plugin the same way.

**Build your own.** Start from a library plugin with `cowork-plugin-management` (a `1xops plugin new --from <vendor>/<name>` command is planned). It copies the plugin once into its own folder here, renamed into your namespace, with its licence and NOTICE line kept. A link never turns into a copy in place: the copy is a new folder, and the link stays in the catalogue.

**Review before it ships.** A library plugin can carry servers or steps that change things. For example, the AWS library's `aws-core`, `aws-data-analytics` and `aws-startup-advisor` use a server that can call any AWS API, so a read-only role is what keeps them read-only. Check every skill and server of your copy, and run `1xops doctor`, before you list it.

**What ships is decided in one file.** Links here never ship; only entries in `marketplace.json` do, and only folders (the release check refuses a link).

**Library updates.** A library changes only when its pin in `upstream/` moves; the links follow that pin. Your copies never change by themselves.

**Free and paid.** This open-source repository shows how a one-off plugin is built from trusted vendors' free plugins. Advanced capabilities and high-value template plugins, built the same way, are available from [OceanSoft.io](https://www.oceansoft.io).
