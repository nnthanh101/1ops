---
name: read-only-cloud
description: Use before any AWS or Azure command or connector call (aws, az, the AWS or Azure MCP servers). Keeps the work read-only. Check the sign-in's access first, use read operations only, and turn any change into a proposal the person approves.
---

# Read-only AWS and Azure

The sign-in is the boundary. Permission rules only ask; they can't stop the same program called another way. So the identity has to be read-only.

## Before the first cloud call

1. Run `1xops doctor`. Read the `aws …` and `azure` rows.
2. `ready` with `read-only`: go on.
3. `can change things` or `access unknown`: stop. Tell the person which row it is, and the fix in its detail column. Don't use that sign-in.
4. `signed out` or `missing`: show the fix from the detail column and wait. Don't sign in for the person.

## While working

- AWS: only `describe-*`, `list-*`, `get-*` and `lookup-*` calls, `aws s3 ls`, Cost Explorer reads. Pass the profile from `AWS_BILLING_PROFILE` or `AWS_OPERATIONS_PROFILE`; never type a profile name from memory.
- Azure: only `show`, `list` and `query` commands, with the read-only identity's own `AZURE_CONFIG_DIR`. Never the person's own Azure login, which can change things.
- Connectors: the Azure server runs with `--read-only`. Never switch on a write option (`ALLOW_WRITE`, `--allow-write`) for any server.
- Never read credential files (`~/.aws/credentials`, `~/.azure/*token*`, `.env`, `.env.*`).

## When a change is needed

Don't run it. Write the exact command, what it changes, and how to undo it. Then ask. The person runs it, or approves the prompt for that one command.

## Output

Mask every 12-digit account ID (`****1234`). Give each figure with the command it came from.
