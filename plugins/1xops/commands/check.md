---
description: Show each configured connector as ready, signed out or missing, with the exact fix. Changes nothing.
allowed-tools: Bash(1xops doctor:*), Bash(command -v 1xops)
---

Run `1xops doctor` in the current folder. Reply with its output exactly as printed, inside one code block, and nothing else: no heading, no list, no summary. Its last lines already say what to do next.

If `1xops` is not installed (`command -v 1xops` prints nothing), reply with only this:

```
1xops is not installed. Install it, then run /1xops:check again:
  uv tool install 1xops        (or: npm install -g 1xops)
```

Do not run anything else, sign in, or change any file.
