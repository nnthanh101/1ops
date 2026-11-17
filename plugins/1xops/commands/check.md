---
description: Show each configured connector as ready, signed out or missing, with the exact fix. Changes nothing.
allowed-tools: Bash(1xops doctor:*), Bash(command -v 1xops)
---

Run `1xops doctor` in the current folder and show its output exactly as printed, as a code block. Do not run anything else, sign in, or change any file.

If `1xops` is not installed (`command -v 1xops` prints nothing), say so and show the install line instead:

```bash
uv tool install 1xops        # or: npm install -g 1xops
```

After the output, list only the rows whose result is not `ok` or `ready`, each with the fix from its detail column, in the order shown. Add nothing that the output does not say.
