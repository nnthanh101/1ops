// The 1xops commands: doctor, install, config, env, profiles, setup. Same behaviour as the Python
// package (packages/python/src/one_xops/cli.py and setup.py). Nothing changes unless --yes is given.
import { spawnSync } from 'node:child_process';
import { accessSync, constants, existsSync, mkdirSync, renameSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { createInterface } from 'node:readline/promises';
import { styleText } from 'node:util';
import * as cf from './config-file.mjs';
import * as s from './settings.mjs';

const color = (style, text) => styleText(style, text, { stream: process.stdout });

export function which(cmd) {
  for (const dir of (process.env.PATH ?? '').split(path.delimiter)) {
    const file = path.join(dir, cmd);
    try {
      accessSync(file, constants.X_OK);
      return file;
    } catch {
      // not here
    }
  }
  return null;
}

export function run(cmd, args, timeout = 20000) {
  const p = spawnSync(cmd, args, { encoding: 'utf8', timeout });
  if (p.error) return { code: 1, out: String(p.error.message) };
  return { code: p.status ?? 1, out: (p.stdout || p.stderr || '').trim() };
}

export const mask = (account) => (account.length >= 4 ? `****${account.slice(-4)}` : '****');

function table(title, columns, rows) {
  const width = columns.map((c, i) => Math.max(c.length, ...rows.map((r) => String(r[i]).length)));
  const line = (cells) => cells.map((c, i) => String(c).padEnd(width[i])).join('  ');
  console.log(color('bold', title));
  console.log(color('dim', line(columns)));
  for (const r of rows) console.log(line(r));
}

// ── doctor ──────────────────────────────────────────────────────────────────

export function checkTools() {
  const tools = [['git', true], [s.HOST, true], ['uv', false], ['npx', false], ['docker', false], ['gh', false], ['aws', false], ['az', false]];
  return tools.map(([name, required]) => {
    const where = which(name);
    if (!where) return [name, required, false, 'not found on PATH'];
    const { code, out } = run(name, ['--version']);
    return [name, required, code === 0, out ? out.split('\n')[0] : where];
  });
}

// Read-only sign-in checks. Account IDs are masked, never printed in full.
export function checkSignIn(awsProfile) {
  const rows = [];
  if (which('aws')) {
    const args = ['sts', 'get-caller-identity', '--output', 'json', ...(awsProfile ? ['--profile', awsProfile] : [])];
    const { code, out } = run('aws', args);
    if (code === 0) {
      let account = '';
      try { account = JSON.parse(out).Account ?? ''; } catch { /* not JSON */ }
      rows.push(['aws sign-in', false, true, `signed in, account ${mask(account)}`]);
    } else rows.push(['aws sign-in', false, false, 'not signed in (aws sso login)']);
  }
  if (which('az')) {
    const { code } = run('az', ['account', 'show', '--output', 'none']);
    rows.push(['azure sign-in', false, code === 0, code === 0 ? 'signed in' : 'not signed in (az login)']);
  }
  if (which('gh')) {
    const { code } = run('gh', ['auth', 'status']);
    rows.push(['github sign-in', false, code === 0, code === 0 ? 'signed in' : 'not signed in (gh auth login)']);
  }
  return rows;
}

export function doctor(opts, version) {
  const rows = [...checkTools(), ...checkSignIn(opts['aws-profile'])];
  const shown = rows.map(([name, required, ok, detail]) => [
    name,
    required ? 'required' : 'optional',
    ok ? color('green', 'ok') : required ? color('red', 'missing') : color('yellow', 'optional'),
    detail,
  ]);
  table(`1xops ${version} doctor`, ['check', 'needed', 'result', 'detail'], shown);
  const failed = rows.filter((r) => r[1] && !r[2]).map((r) => r[0]);
  if (failed.length) {
    console.log(color('red', `Required: ${failed.join(', ')}`));
    return 1;
  }
  return 0;
}

// ── install ─────────────────────────────────────────────────────────────────

const INSTALL_STEPS = [
  [s.HOST, 'plugin', 'marketplace', 'add', 'anthropics/knowledge-work-plugins'],
  [s.HOST, 'plugin', 'marketplace', 'add', 'nnthanh101/1xops'],
  [s.HOST, 'plugin', 'install', '1xops@1xops'],
];

export function install(opts) {
  if (!which(s.HOST)) {
    console.log(color('red', `'${s.HOST}' CLI not found; run '1xops doctor'.`));
    return 1;
  }
  for (const base of INSTALL_STEPS) {
    const step = [...base, '--scope', opts.scope];
    console.log(color('bold', `$ ${step.join(' ')}`));
    if (!opts.yes) continue;
    const { code, out } = run(step[0], step.slice(1), 180000);
    console.log(out);
    if (code !== 0) return code;
  }
  if (!opts.yes) console.log('Dry run. Re-run with --yes to install.');
  return 0;
}

// ── config ──────────────────────────────────────────────────────────────────

// A line diff of two JSON documents (longest common subsequence; settings files are small).
function diffLines(a, b) {
  const n = a.length, m = b.length;
  const lcs = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) {
    lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
  }
  const out = [];
  let i = 0, j = 0;
  while (i < n || j < m) {
    if (i < n && j < m && a[i] === b[j]) { out.push(` ${a[i]}`); i++; j++; }
    else if (j < m && (i === n || lcs[i][j + 1] >= lcs[i + 1][j])) out.push(`+${b[j++]}`);
    else out.push(`-${a[i++]}`);
  }
  return out;
}

function showChange(file, before, after) {
  if (s.dumps(before) === s.dumps(after)) {
    console.log(color('dim', `${file}: already up to date`));
    return false;
  }
  console.log(`--- ${file}\n+++ ${file}`);
  for (const l of diffLines(s.dumps(before).trimEnd().split('\n'), s.dumps(after).trimEnd().split('\n'))) {
    if (l[0] !== ' ') console.log(l);
  }
  return true;
}

function write(file, data) {
  mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp`;
  writeFileSync(tmp, s.dumps(data));
  renameSync(tmp, file);
}

function resolveConfig(opts) {
  if (opts.file) {
    const cfg = cf.load(opts.file);
    return { scope: cfg.scope, project: path.resolve(cfg.dir), out: cfg.out ? path.resolve(cfg.out) : null, connectors: cfg.connectors };
  }
  return {
    scope: opts.scope,
    project: path.resolve(opts.dir),
    out: opts.out ? path.resolve(opts.out) : null,
    connectors: Object.fromEntries((opts.connectors ?? []).map((c) => [c, {}])),
  };
}

export function config(opts) {
  let scope, project, out, profiles;
  try {
    ({ scope, project, out } = resolveConfig(opts));
    profiles = Object.entries(resolveConfig(opts).connectors).map(([name, values]) => [s.loadProfile(name), values]);
  } catch (err) {
    console.log(color('red', err.message));
    return 2;
  }
  const personal = scope === 'local' || scope === 'personal';
  let servers = {};
  let wanted = s.BASELINE;
  for (const [profile, values] of profiles) {
    // Shared files keep ${VAR}; private host config gets the person's values.
    Object.assign(servers, personal ? cf.substitute(profile.mcpServers, values) : profile.mcpServers);
    wanted = s.merge(wanted, { permissions: profile.permissions ?? {} });
  }

  const planned = [];
  const target = s.settingsPath(scope, project, out);
  const before = s.readJson(target);
  const after = s.merge(before, wanted);
  if (showChange(target, before, after)) planned.push([target, after]);

  const hostCmds = [];
  if (Object.keys(servers).length) {
    const mcpFile = s.mcpPath(scope, project, out);
    if (mcpFile) {
      const b = s.readJson(mcpFile);
      const a = s.merge(b, { mcpServers: servers });
      if (showChange(mcpFile, b, a)) planned.push([mcpFile, a]);
    } else {
      const hostScope = scope === 'personal' ? 'user' : 'local';
      for (const [name, spec] of Object.entries(servers)) {
        hostCmds.push([s.HOST, 'mcp', 'add-json', '-s', hostScope, name, JSON.stringify(spec)]);
        console.log(color('bold', `$ ${s.HOST} mcp add-json -s ${hostScope} ${name} '…'`));
      }
    }
  }

  if (!opts.yes) {
    console.log('Dry run. Re-run with --yes to write these changes.');
    return 0;
  }
  if (hostCmds.length && !which(s.HOST)) {
    console.log(color('red', `${scope} scope adds connectors through the '${s.HOST}' CLI, which is not installed. Nothing was written. Install it, or use --scope team.`));
    return 1;
  }
  for (const [file, data] of planned) {
    write(file, data);
    console.log(color('green', `wrote ${file}`));
  }
  for (const cmd of hostCmds) {
    const { code, out: msg } = run(cmd[0], cmd.slice(1));
    console.log(msg);
    if (code !== 0) return code;
  }
  if (scope === 'org') console.log(`Give these files to IT to install in: ${s.managedDir()}`);
  if (!personal && profiles.some(([, v]) => Object.keys(v).length)) {
    console.log('Shared files use ${VAR}. Load your values with: eval "$(1xops env)"');
  }
  return 0;
}

// ── env and profiles ────────────────────────────────────────────────────────

const shellQuote = (v) => (/^[A-Za-z0-9@%+=:,./_-]+$/.test(v) ? v : `'${v.replaceAll("'", `'"'"'`)}'`);

export function env(opts) {
  let cfg;
  try {
    cfg = cf.load(opts.file);
  } catch (err) {
    console.error(err.message);
    return 2;
  }
  for (const [k, v] of Object.entries(cfg.values)) console.log(`export ${k}=${shellQuote(v)}`);
  return 0;
}

export function profiles() {
  const rows = s.builtinProfiles().map((name) => {
    const p = s.loadProfile(name);
    return [name, Object.keys(p.mcpServers).join(', '), cf.variables(p).join(', ') || '—', p.description ?? ''];
  });
  table('Connector profiles', ['profile', 'servers', 'values (.env.1xops keys)', 'description'], rows);
  console.log("Use your own: a .json file with an 'mcpServers' object, as a connector name.");
  return 0;
}

// ── setup ───────────────────────────────────────────────────────────────────

// Read-only lookups that make good defaults: AWS profiles and region, current Azure account.
function detect() {
  const found = {};
  const ok = (cmd, args) => (which(cmd) ? run(cmd, args) : { code: 1, out: '' });
  const profilesOut = ok('aws', ['configure', 'list-profiles']);
  if (profilesOut.code === 0 && profilesOut.out) found.awsProfiles = profilesOut.out.split(/\s+/);
  const region = process.env.AWS_REGION || (ok('aws', ['configure', 'get', 'region']).code === 0 ? ok('aws', ['configure', 'get', 'region']).out : '');
  if (region) found.AWS_REGION = region;
  const az = ok('az', ['account', 'show', '--query', '{t:tenantId,s:id}', '--output', 'json']);
  if (az.code === 0 && az.out) {
    try {
      const ids = JSON.parse(az.out);
      found.AZURE_TENANT_ID = ids.t;
      found.AZURE_SUBSCRIPTION_ID = ids.s;
    } catch { /* not JSON */ }
  }
  return found;
}

export async function setup(opts) {
  const rl = createInterface({ input: process.stdin, output: process.stdout, terminal: false });
  const lines = rl[Symbol.asyncIterator]();
  const ask = async (question, fallback = '') => {
    process.stdout.write(`${question}${fallback ? ` [${fallback}]` : ''}: `);
    const { value, done } = await lines.next();
    const answer = done ? '' : value.trim();
    return answer || fallback;
  };
  const yes = async (question, fallback) => {
    const a = (await ask(`${question} (y/n)`, fallback ? 'y' : 'n')).toLowerCase();
    return a.startsWith('y');
  };
  try {
    const file = opts.file;
    console.log(`${color('bold', '1xops setup')} — non-secret values only; secrets stay in your sign-in.\n`);
    let scope;
    do scope = await ask(`Scope (${s.SCOPES.join(' | ')})`, 'team'); while (!s.SCOPES.includes(scope));
    const conf = { scope };
    if (scope === 'team' || scope === 'local') conf.dir = await ask('Project or tenant folder', '.');
    if (scope === 'org') conf.out = await ask('Folder to write the managed files to', '.');
    const found = detect();
    const connectors = {};
    for (const name of s.builtinProfiles()) {
      const profile = s.loadProfile(name);
      if (!(await yes(`Add ${name}: ${profile.description ?? ''}?`, false))) continue;
      const values = {};
      for (const v of cf.variables(profile)) {
        if (v.endsWith('_PROFILE') && found.awsProfiles) console.log(`  AWS profiles on this machine: ${found.awsProfiles.join(', ')}`);
        const value = await ask(`  ${v} (blank to skip)`, process.env[v] || found[v] || '');
        if (value) values[v] = value;
      }
      connectors[name] = values;
    }
    const own = await ask('Your own profile .json file (blank to skip)');
    if (own) connectors[own] = {};
    conf.connectors = connectors;

    const text = cf.dump(conf);
    console.log(`\n${file}\n${text}`);
    if (existsSync(file) && !(await yes(`${file} exists. Replace it?`, false))) return 1;
    if (!(await yes(`Write ${file}?`, true))) return 1;
    writeFileSync(file, text);
    cf.load(file); // same checks as `1xops config --file`

    console.log('\nChanges this would make:');
    if (config({ file }) !== 0) return 2;
    if (await yes('Apply them now?', false)) return config({ file, yes: true });
    console.log(`Apply later with: 1xops config --file ${file} --yes`);
    return 0;
  } finally {
    rl.close();
  }
}
