# 1xOps Operations Enterprise

Enterprise platform and operations add-ons for Anthropic's free **operations** plugin. Anthropic's plugin supplies the general playbooks. This repo adds only what enterprise platform teams need on top of them:
- each connector is checked before a playbook runs;
- every figure comes from the real asset, with its source;
- nothing is written until a person says yes.

- Plugin: [`plugins/operations-enterprise`](plugins/operations-enterprise/README.md)
- Marketplace: `1xops` (`/plugin marketplace add 1xOps/operations-enterprise`)
- Decision record: CC-ADR-079 in `1xOps/command-center-enterprise`. Option C was chosen: an owned add-on on top of Anthropic's plugin, never a copy of it.

## How we deliver
- **Branches:** `feature/*` → pull request into `develop`; `main` takes only the owner's release PR.
- **One capability per PR.** It ships only after it beats Anthropic's skill alone, side by side, on a real asset.
- **CI:** `claude plugin validate --strict` on every pull request.

Copyright (c) 2026 Nhat-Thanh Nguyen (nnthanh101@gmail.com). All rights reserved. See [LICENSE](LICENSE). "Anthropic" and "Claude" are named only to identify the required plugin. This add-on is not made or endorsed by Anthropic.
