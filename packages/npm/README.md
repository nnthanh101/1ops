# 1xops

The `1xops` command line of [1ops by OceanSoft.io](https://github.com/nnthanh101/1xops), native to Node.js: Node 24 or later, no dependencies, nothing else to install.

```bash
npx 1xops doctor                       # prerequisites and read-only sign-in (account IDs masked)
npx 1xops install --yes                # add the marketplaces and install the plugin
npx 1xops setup                        # guided: asks a few questions, writes .env.1xops, shows the diff
npx 1xops config --scope team --connectors aws azure itsm   # shows a diff; add --yes to write
```

The same commands, scopes and `.env.1xops` file as the Python package; both write identical files. Details: [packages/python/README.md](https://github.com/nnthanh101/1xops/tree/develop/packages/python).

Licence: Apache-2.0. © 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com), OceanSoft.io. Licence, trademarks and third-party components: [NOTICE](https://github.com/nnthanh101/1xops/blob/develop/NOTICE).
