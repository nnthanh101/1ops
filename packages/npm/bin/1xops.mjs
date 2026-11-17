#!/usr/bin/env node
// 1xops by OceanSoft.io: set up the 1xops plugin, settings and read-only cloud connectors for an
// organisation, a team or tenant folder, a project, or one person. Native Node.js; no dependencies.
import { readFileSync } from 'node:fs';
import { parseArgs } from 'node:util';
import * as cmd from '../src/commands.mjs';
import { DEFAULT_FILE } from '../src/config-file.mjs';
import { SCOPES } from '../src/settings.mjs';

const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));

const HELP = `Usage: 1xops <command> [options]

  doctor     check prerequisites, sign-in and connectors    [--aws-profile NAME] [--file PATH]
  install    add the marketplaces and install the plugin    [--scope user|project|local] [--yes]
  setup      guided setup: asks questions, writes ${DEFAULT_FILE}   [--file PATH]
  config     write settings and connectors for a scope      [--scope ${SCOPES.join('|')}] [--dir DIR]
                                                             [--out DIR] [--connectors NAME...] [--file PATH] [--yes]
  env        print export lines for the values in ${DEFAULT_FILE}    [--file PATH]
  profiles   list built-in connector profiles

Nothing changes unless you pass --yes.`;

const argv = process.argv.slice(2);
if (argv[0] === '--version' || argv[0] === '-V') {
  console.log(`1xops ${version}`);
  process.exit(0);
}
const [command, ...rest] = argv;
if (!command || command === '--help' || command === '-h') {
  console.log(HELP);
  process.exit(command ? 0 : 2);
}

const OPTIONS = {
  doctor: { 'aws-profile': { type: 'string' }, file: { type: 'string', default: DEFAULT_FILE } },
  install: { scope: { type: 'string', default: 'user' }, yes: { type: 'boolean', default: false } },
  setup: { file: { type: 'string', default: DEFAULT_FILE } },
  config: {
    scope: { type: 'string', default: 'team' },
    dir: { type: 'string', default: '.' },
    out: { type: 'string' },
    connectors: { type: 'string', multiple: true, default: [] },
    file: { type: 'string' },
    yes: { type: 'boolean', default: false },
  },
  env: { file: { type: 'string', default: DEFAULT_FILE } },
  profiles: {},
};
if (!(command in OPTIONS)) {
  console.error(`1xops: unknown command '${command}'\n\n${HELP}`);
  process.exit(2);
}

let opts;
try {
  // --connectors takes one or more names: `--connectors aws azure itsm`
  const expanded = [];
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] !== '--connectors') { expanded.push(rest[i]); continue; }
    while (i + 1 < rest.length && !rest[i + 1].startsWith('--')) expanded.push('--connectors', rest[++i]);
  }
  opts = parseArgs({ args: expanded, options: OPTIONS[command], strict: true }).values;
} catch (err) {
  console.error(`1xops ${command}: ${err.message}`);
  process.exit(2);
}
if (command === 'config' && !SCOPES.includes(opts.scope)) {
  console.error(`1xops config: --scope must be one of ${SCOPES.join(', ')}`);
  process.exit(2);
}
if (command === 'install' && !['user', 'project', 'local'].includes(opts.scope)) {
  console.error('1xops install: --scope must be one of user, project, local');
  process.exit(2);
}

const handlers = {
  doctor: () => cmd.doctor(opts, version),
  install: () => cmd.install(opts),
  setup: () => cmd.setup(opts),
  config: () => cmd.config(opts),
  env: () => cmd.env(opts),
  profiles: () => cmd.profiles(),
};
process.exit(await handlers[command]());
