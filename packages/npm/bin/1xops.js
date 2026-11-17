#!/usr/bin/env node
// Runs the 1xops Python CLI at the same version as this package, through uv.
"use strict";
const { spawnSync } = require("node:child_process");
const { version } = require("../package.json");

const args = ["tool", "run", "--from", `1xops==${version}`, "1xops", ...process.argv.slice(2)];
const run = spawnSync("uv", args, { stdio: "inherit" });

if (run.error && run.error.code === "ENOENT") {
  console.error("1xops needs uv: https://docs.astral.sh/uv/getting-started/installation/");
  process.exit(127);
}
process.exit(run.status ?? 1);
