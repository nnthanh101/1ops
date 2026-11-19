# Upstream library

Free, open-source plugins we pick from. Each vendor is a git submodule pinned to a commit and never shipped; a monthly workflow ([`upstream-bump.yml`](../.github/workflows/upstream-bump.yml)) moves every pin in one pull request and checks that each plugin 1xops depends on is still there. Customers see only [`plugins/1xops`](../plugins/README.md).

**Add a vendor:** `git submodule add -b main <url> upstream/<name>`, set `ignore = untracked` in `.gitmodules`, add its `NOTICE` line, and add a section below. The bump workflow finds it by itself.

## Index

**Picked** ships with 1xops (a copied skill or a dependency). **Not picked** was reviewed and left out, with the reason. **Not reviewed** has not been looked at yet.

### `knowledge-work-plugins` (Apache-2.0)

| Plugin | Status | Why |
|---|---|---|
| `operations` | Picked: dependency | Base of the 1xops operations skills |
| `cowork-plugin-management` | Picked: dependency | Builds a customer's own plugin from the library |
| `customer-support`, `data`, `engineering`, `enterprise-search`, `finance`, `human-resources`, `marketing`, `product-management`, `sales`, `small-business` | Picked: dependency | Business roles 1xops serves; read-only connectors |
| `design`, `legal`, `productivity` | Not picked | Outside cloud and operations work today |
| Every other plugin in the marketplace | Not reviewed | |

### `agent-toolkit-for-aws` (Apache-2.0)

| Plugin | Status | Why |
|---|---|---|
| `aws-agents` | Not reviewed | Reads AWS documentation only (hosted knowledge server): the simplest first pick |
| `aws-core`, `aws-data-analytics`, `aws-startup-advisor` | Not reviewed | Their server can call any AWS API, writes included: needs a read-only role and a review of each step |
| `aws-agents-for-devsecops` | Not reviewed | Connects to AWS's hosted DevOps service |
| `aws-continuum` | Not reviewed | Ships its own `SAFETY.md`: read it before any pick |
