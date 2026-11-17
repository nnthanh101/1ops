// The 1xops commands: doctor, install, config, env, profiles, setup. Same behaviour as the Python
// package (packages/python/src/one_xops/cli.py and setup.py). Nothing changes unless --yes is given.
import { spawnSync } from 'node:child_process';
import { accessSync, constants, existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import path, { join } from 'node:path';
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
// Any 12-digit run (an AWS account ID) in any text, masked: doctor output is pasted onto issues as evidence.
export const scrub = (text) => String(text).replace(/\d{12}/g, (d) => mask(d));
// read: the role cannot change anything; write: it can; unknown: cannot tell from the name.
export function accessFromRole(arn = '') {
  const role = arn.match(/:assumed-role\/([^/]+)\//)?.[1] ?? arn.match(/:(user|root)\b/)?.[1] ?? '';
  if (/readonly|viewonly|securityaudit|readaccess|viewer/i.test(role)) return 'read';
  if (/admin|poweruser|fullaccess|root/i.test(role)) return 'write';
  return 'unknown';
}
const ACCESS = { read: 'read-only', write: 'can change things: use a read-only role', unknown: 'access unknown: use a read-only role' };

// The same look as the Python CLI's rich table: a heavy header, light rows, colour on a terminal. No dependency.
// On a terminal the table fits the window: the widest columns shrink and their cells wrap, as rich does.
// Piped (the assistant, evidence) it sizes to its content, so both CLIs print the same bytes.
const visible = (s) => String(s).replace(/\x1b\[[0-9;]*m/g, '').length;
function wrap(text, w) {
  if (visible(text) <= w) return [String(text)];
  // A coloured cell wraps on its plain text; each line then gets the colour again, so no code is cut or bleeds.
  const styled = String(text).match(/^(\x1b\[[0-9;]*m)(.*?)(\x1b\[[0-9;]*m)$/s);
  if (styled) return wrap(styled[2], w).map((l) => styled[1] + l + styled[3]);
  const lines = [];
  let line = '';
  for (const word of String(text).split(' ')) {
    for (let piece = word; piece.length; ) {
      const room = line ? w - line.length - 1 : w;
      if (piece.length <= room) { line = line ? `${line} ${piece}` : piece; piece = ''; }
      else if (line) { lines.push(line); line = ''; }
      else { lines.push(piece.slice(0, w)); piece = piece.slice(w); }
    }
  }
  if (line) lines.push(line);
  return lines;
}
function table(title, columns, rows) {
  const width = columns.map((c, i) => Math.max(c.length, ...rows.map((r) => visible(r[i]))));
  const limit = process.stdout.isTTY ? (process.stdout.columns || 80) - (3 * width.length + 1) : Infinity;
  while (width.reduce((a, w) => a + w, 0) > limit) {
    const i = width.indexOf(Math.max(...width));
    if (width[i] <= 8) break;
    width[i] -= 1;
  }
  const pad = (c, i) => String(c) + ' '.repeat(Math.max(0, width[i] - visible(c)));
  const cells = (r, bar) => {
    const parts = r.map((c, i) => wrap(c, width[i]));
    const height = Math.max(...parts.map((p) => p.length));
    return Array.from({ length: height }, (_, k) => `${bar} ${parts.map((p, i) => pad(p[k] ?? '', i)).join(` ${bar} `)} ${bar}`).join('\n');
  };
  const rule = (l, m, r, h) => l + width.map((w) => h.repeat(w + 2)).join(m) + r;
  const total = width.reduce((a, w) => a + w + 3, 1);
  const left = Math.max(0, Math.floor((total - title.length) / 2));
  console.log(' '.repeat(left) + color('bold', title) + ' '.repeat(Math.max(0, total - left - title.length)));
  console.log(rule('┏', '┳', '┓', '━'));
  console.log(cells(columns.map((c) => color('bold', c)), '┃'));
  console.log(rule('┡', '╇', '┩', '━'));
  for (const r of rows) console.log(cells(r, '│'));
  console.log(rule('└', '┴', '┘', '─'));
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

// Which 1xops plugin edition is installed, from the host's own plugin records. Read-only.
export function checkEdition() {
  const folder = path.join(process.env.CLAUDE_CONFIG_DIR || path.join(homedir(), `.${s.HOST}`), 'plugins');
  const read = (name) => { try { return JSON.parse(readFileSync(path.join(folder, name), 'utf8')); } catch { return {}; } };
  const installed = read('installed_plugins.json').plugins ?? {};
  const version = (key) => (installed[key]?.[0]?.version ?? '');
  if ('1xops@1xops' in installed) {
    if (read('known_marketplaces.json')['1xops']?.source?.repo === 'nnthanh101/1xops') return ['edition', false, false, 'free, old marketplace name: run 1xops install --yes'];
    return ['edition', false, true, `enterprise ${version('1xops@1xops')}`.trim()];
  }
  if ('1xops@1ops' in installed) return ['edition', false, true, `free ${version('1xops@1ops')}`.trim()];
  return ['edition', false, false, 'plugin not installed: 1xops install --yes'];
}

// Read-only sign-in checks. Account IDs are masked, never printed in full.
export function checkSignIn(awsProfile) {
  const rows = [];
  if (which('aws')) {
    const args = ['sts', 'get-caller-identity', '--output', 'json', ...(awsProfile ? ['--profile', awsProfile] : [])];
    const { code, out } = run('aws', args);
    if (code === 0) {
      let id = {};
      try { id = JSON.parse(out); } catch { /* not JSON */ }
      const access = accessFromRole(id.Arn);
      rows.push(['aws sign-in', false, true, `signed in, account ${mask(id.Account ?? '')}`]);
      rows.push(['aws access', false, access === 'read', ACCESS[access]]);
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

// (status, fix) for a failed AWS identity call, from the AWS CLI's own error text.
export function awsFix(error, profile) {
  if (/could not be found/i.test(error)) return ['missing', `profile ${profile} not found: aws configure sso --profile ${profile}, or set AWS_CONFIG_FILE`];
  if (/expired|refresh failed|sso.*token|nocredentials|unable to locate credentials/i.test(error)) return ['signed out', `aws sso login --profile ${profile}`];
  const first = error.split('\n').find((l) => l.trim()) ?? 'AWS identity call failed';
  return ['check', first.replace(/^aws: \[ERROR\]: /, '').slice(0, 120)];
}

// read: Reader roles only; write: any role that can change things; unknown: no roles seen.
export function azureAccess(roles = []) {
  if (!roles.length) return 'unknown';
  if (roles.some((r) => /owner|contributor|administrator/i.test(r))) return 'write';
  if (roles.every((r) => /reader/i.test(r))) return 'read';
  return 'unknown';
}
const AZURE_ACCESS = { read: 'read-only', write: 'can change things: use a read-only (Reader) identity', unknown: 'access unknown: use a read-only (Reader) identity' };

function awsConnector(v, values) {
  const name = `aws ${v}`;
  const profile = values[v] || process.env[v] || '';
  if (!profile) return [name, 'missing', `set ${v} in .env.1xops or the shell (1xops setup)`];
  if (!which('aws')) return [name, 'missing', 'install the AWS CLI'];
  const { code, out } = run('aws', ['sts', 'get-caller-identity', '--output', 'json', '--profile', profile]);
  if (code !== 0) return [name, ...awsFix(out, profile)];
  let id;
  try { id = JSON.parse(out); } catch { return [name, 'check', 'AWS identity call returned no account']; }
  const access = accessFromRole(id.Arn ?? '');
  return [name, access === 'read' ? 'ready' : 'check', `profile ${profile}, account ${mask(id.Account ?? '')}, ${ACCESS[access]}`];
}

function azureConnector() {
  if (!which('az')) return ['azure', 'missing', 'install the Azure CLI'];
  const who = run('az', ['account', 'show', '--query', 'user.name', '--output', 'tsv']);
  if (who.code !== 0 || !who.out) return ['azure', 'signed out', 'az login with a read-only (Reader) identity, in its own AZURE_CONFIG_DIR'];
  const roles = run('az', ['role', 'assignment', 'list', '--assignee', who.out, '--all', '--query', '[].roleDefinitionName', '--output', 'json'], 60000);
  let names = [];
  try { names = roles.code === 0 ? JSON.parse(roles.out) : []; } catch { /* not JSON */ }
  const access = azureAccess(names);
  return ['azure', access === 'read' ? 'ready' : 'check', AZURE_ACCESS[access]];
}

// [connector, status, fix] for each connector in .env.1xops. Read-only identity calls only.
export function checkConnectors(file) {
  if (!existsSync(file)) return [['connectors', 'missing', `no ${file} here: run 1xops setup`]];
  let cfg;
  try { cfg = cf.load(file); } catch (err) { return [['connectors', 'missing', err.message]]; }
  if (!Object.keys(cfg.connectors).length) return [['connectors', 'missing', `ONEXOPS_CONNECTORS is empty in ${file}: run 1xops setup`]];
  const rows = [];
  for (const connector of Object.keys(cfg.connectors)) {
    let servers;
    try { servers = s.loadProfile(connector).mcpServers; } catch (err) { rows.push([connector, 'missing', err.message]); continue; }
    const awsVars = [];
    let azure = false;
    for (const [serverName, server] of Object.entries(servers)) {
      const env = server.env ?? {};
      if ('AWS_PROFILE' in env) awsVars.push(...[...env.AWS_PROFILE.matchAll(/\$\{([A-Z0-9_]+)(?::-[^}]*)?\}/g)].map((m) => m[1]));
      else if ('AZURE_TENANT_ID' in env) azure = true;
      else if (server.type === 'http') rows.push([serverName, 'check', `signs in inside the host: run /mcp and choose ${serverName}`]);
      else rows.push([serverName, 'check', 'no sign-in check for this connector']);
    }
    rows.push(...[...new Set(awsVars)].map((v) => awsConnector(v, cfg.values)));
    if (azure) rows.push(azureConnector());
  }
  return rows;
}

const RESULT_STYLE = { ok: 'green', ready: 'green', missing: 'red', 'signed out': 'yellow', check: 'yellow' };

export function doctor(opts, version) {
  // The identity calls take seconds; a status line on a terminal (cleared after), nothing when piped.
  const tty = process.stdout.isTTY;
  if (tty) process.stdout.write(color('dim', 'Checking tools, sign-ins and connectors (read-only)…'));
  const rows = [...checkTools(), checkEdition(), ...checkSignIn(opts['aws-profile'])];
  const connectors = checkConnectors(opts.file);
  if (tty) process.stdout.write('\r\x1b[K');
  const shown = rows.map(([name, required, ok, detail]) => [name, required ? 'required' : 'optional', ok ? 'ok' : required ? 'missing' : 'check', scrub(detail)]);
  shown.push(...connectors.map(([name, status, fix]) => [name, 'connector', status, scrub(fix)]));
  // Required tools and configured connectors that are not ok or ready. Optional tools stay in the table only.
  const todo = shown.filter((r) => r[2] !== 'ok' && r[2] !== 'ready' && r[1] !== 'optional');
  for (const r of shown) r[2] = color(RESULT_STYLE[r[2]], r[2]);
  table(`1xops ${version} doctor`, ['check', 'needed', 'result', 'detail'], shown);
  // What to do next, in table order (see todo above).
  if (!todo.length) console.log(color('green', 'All set: nothing to fix.'));
  else {
    console.log(color('bold', 'Next:'));
    todo.forEach((r, i) => console.log(`  ${i + 1}. ${r[0]}: ${r[3]}`));
  }
  const failed = rows.filter((r) => r[1] && !r[2]).map((r) => r[0]);
  if (failed.length) {
    console.log(color('red', `Required: ${failed.join(', ')}`));
    return 1;
  }
  return 0;
}

// ── install ─────────────────────────────────────────────────────────────────

// Installing an edition replaces the other (or the free edition under its old marketplace name, 1xops).
const INSTALL_STEPS = [
  [s.HOST, 'plugin', 'marketplace', 'add', 'anthropics/knowledge-work-plugins'],
  [s.HOST, 'plugin', 'uninstall', '1xops@1xops'],
  [s.HOST, 'plugin', 'marketplace', 'remove', '1xops'],
  [s.HOST, 'plugin', 'marketplace', 'add', 'nnthanh101/1xops'],
  [s.HOST, 'plugin', 'install', '1xops@1ops'],
]

const SHOP = 'https://shop.oceansoft.io';

// Free edition out, enterprise in: the same plugin name 1xops, from the unpacked bundle as marketplace 1xops.
const enterpriseSteps = (folder) => [
  [s.HOST, 'plugin', 'marketplace', 'add', 'anthropics/knowledge-work-plugins'],
  [s.HOST, 'plugin', 'uninstall', '1xops@1ops'],
  [s.HOST, 'plugin', 'marketplace', 'remove', '1xops'],
  [s.HOST, 'plugin', 'marketplace', 'add', folder],
  [s.HOST, 'plugin', 'install', '1xops@1xops'],
];

// The enterprise bundle's version, read without unpacking (the system tar, so no dependency).
export function bundleVersion(file) {
  const member = (m) => { const r = run('tar', ['-xzOf', file, m]); if (r.code !== 0) throw new Error(); return JSON.parse(r.out); };
  let market, plugin;
  try { market = member('.claude-plugin/marketplace.json'); plugin = member('plugins/1xops/.claude-plugin/plugin.json'); }
  catch { throw new Error(`${file} is not a 1xops enterprise bundle`); }
  if (market.name !== '1xops' || plugin.name !== '1xops') throw new Error(`${file} is not a 1xops enterprise bundle`);
  return String(plugin.version ?? '0');
}

export function install(opts) {
  if (!which(s.HOST)) {
    console.log(color('red', `'${s.HOST}' CLI not found; run '1xops doctor'.`));
    return 1;
  }
  let steps = INSTALL_STEPS;
  if (opts.edition === 'enterprise') {
    if (!opts.file) {
      console.log(`The enterprise edition is sold at ${SHOP}. Download the bundle from your order, then run:`);
      console.log('  1xops install --edition enterprise --file <1xops-enterprise-x.y.z.tar.gz> --yes');
      return 2;
    }
    let version;
    try { version = bundleVersion(opts.file); } catch (err) { console.log(color('red', err.message)); return 2; }
    const folder = path.join(homedir(), '.1xops', 'enterprise', version);
    steps = enterpriseSteps(folder);
    console.log(color('bold', `$ unpack ${opts.file} into ${folder}`));
    if (opts.yes) {
      mkdirSync(folder, { recursive: true });
      const r = run('tar', ['-xzf', opts.file, '-C', folder]);
      if (r.code !== 0) { console.log(r.out); return r.code; }
    }
  }
  for (const base of steps) {
    const step = [...base, '--scope', opts.scope];
    console.log(color('bold', `$ ${step.join(' ')}`));
    if (!opts.yes) continue;
    const { code, out } = run(step[0], step.slice(1), 180000);
    console.log(out);
    // removing the edition being replaced may fail harmlessly: it was not installed
    if (code !== 0 && !step.includes('uninstall') && !step.includes('remove')) return code;
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
    else if (i < n && (j === m || lcs[i + 1][j] >= lcs[i][j + 1])) out.push(`-${a[i++]}`); // removed first, as difflib
    else out.push(`+${b[j++]}`);
  }
  return out;
}

function showChange(file, before, after, linesToo = true) {
  if (s.dumps(before) === s.dumps(after)) {
    console.log(color('dim', `${file}: already up to date`));
    return false;
  }
  const lines = diffLines(s.dumps(before).trimEnd().split('\n'), s.dumps(after).trimEnd().split('\n')).filter((l) => l[0] !== ' ');
  const added = lines.filter((l) => l[0] === '+').length;
  console.log(color('bold', `${file}: ${added} lines added, ${lines.length - added} removed`));
  if (linesToo) for (const l of lines) console.log(color(l[0] === '+' ? 'green' : 'red', l));
  return true;
}

function write(file, data) {
  mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp`;
  writeFileSync(tmp, typeof data === 'string' ? data : s.dumps(data), { flush: true }); // on disk before the swap
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
  if (showChange(target, before, after, opts.preview !== 'summary')) planned.push([target, after]);

  const hostCmds = [];
  if (Object.keys(servers).length) {
    const mcpFile = s.mcpPath(scope, project, out);
    if (mcpFile) {
      const b = s.readJson(mcpFile);
      const a = s.merge(b, { mcpServers: servers });
      if (showChange(mcpFile, b, a, opts.preview !== 'summary')) planned.push([mcpFile, a]);
    } else {
      const hostScope = scope === 'personal' ? 'user' : 'local';
      for (const [name, spec] of Object.entries(servers)) {
        hostCmds.push([s.HOST, 'mcp', 'add-json', '-s', hostScope, name, JSON.stringify(spec)]);
        console.log(color('bold', `$ ${s.HOST} mcp add-json -s ${hostScope} ${name} '…'`));
      }
    }
  }

  if (!opts.yes) {
    if (!opts.preview) console.log('Dry run. Re-run with --yes to write these changes.');
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
  // Azure IDs are read only from a separate read-only identity (AZURE_CONFIG_DIR), never the default login.
  const az = process.env.AZURE_CONFIG_DIR ? ok('az', ['account', 'show', '--query', '{t:tenantId,s:id}', '--output', 'json']) : { code: 1, out: '' };
  if (az.code === 0 && az.out) {
    try {
      const ids = JSON.parse(az.out);
      found.AZURE_TENANT_ID = ids.t;
      found.AZURE_SUBSCRIPTION_ID = ids.s;
    } catch { /* not JSON */ }
  }
  return found;
}

// (name, masked account, role) of AWS profiles whose configured role cannot change things. Read from the local AWS
// config only: no cloud call. Unknown and can-change profiles are left out.
export function readOnlyProfiles() {
  const cfg = process.env.AWS_CONFIG_FILE || join(homedir(), '.aws', 'config');
  if (!existsSync(cfg)) return [];
  const found = [];
  let name = '';
  let kv = {};
  const flush = () => {
    const arn = kv.role_arn ?? '';
    const role = kv.sso_role_name || arn.split('/').pop();
    if (name && role && accessFromRole(`:assumed-role/${role}/`) === 'read') {
      const acct = kv.sso_account_id || arn.split(':')[4] || '';
      found.push([name, acct ? `****${acct.slice(-4)}` : '-', role]);
    }
  };
  for (const raw of readFileSync(cfg, 'utf8').split('\n')) {
    const line = raw.trim();
    const m = line.match(/^\[(?:profile\s+)?([^\]]+)\]/);
    if (m) { flush(); name = m[1].trim(); kv = {}; }
    else if (line.includes('=') && !/^[#;]/.test(line)) { const i = line.indexOf('='); kv[line.slice(0, i).trim()] = line.slice(i + 1).trim(); }
  }
  flush();
  return found.sort((a, b) => (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
}

const SCOPE_HELP = {
  org: 'managed files for IT, every person in the organisation',
  team: 'a shared project or tenant folder',
  local: 'you, in this project only',
  personal: 'you, in every project',
};

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
    table('Who the settings are for', ['scope', 'for'], s.SCOPES.map((n) => [n, SCOPE_HELP[n]]));
    let scope;
    do scope = await ask(`Scope (${s.SCOPES.join('/')})`, 'team'); while (!s.SCOPES.includes(scope));
    const conf = { scope };
    if (scope === 'team' || scope === 'local') conf.dir = await ask('Project or tenant folder', '.');
    if (scope === 'org') conf.out = await ask('Folder to write the managed files to', '.');
    const found = detect();
    const connectors = {};
    let listed = false;
    for (const name of s.builtinProfiles()) {
      const profile = s.loadProfile(name);
      if (!(await yes(`Add ${name}: ${profile.description ?? ''}?`, false))) continue;
      const values = {};
      for (const v of cf.variables(profile)) {
        if (v.endsWith('_PROFILE')) {
          // Pick a read-only AWS profile: by number, or type part of a name to filter. A name outside the read-only
          // list cannot get in. The list is shown once; later questions refer to it.
          const options = readOnlyProfiles();
          if (!options.length) {
            if (!listed) { // say it once, not once per variable
              console.log('  No read-only AWS profile in ~/.aws/config yet.');
              console.log('  Create one with: aws configure sso (a role such as ReadOnlyAccess).');
              console.log('  Until then /1xops:check shows this connector as missing.');
              listed = true;
            }
            continue;
          }
          const numbered = options.map((o, i) => [i + 1, o]);
          const show = (rows, title) => table(title, ['#', 'profile', 'account', 'role'], rows.map(([n, [name, acct, role]]) => [String(n).padStart(String(options.length).length), name, acct, role]));
          if (!listed) { show(numbered, `Read-only AWS profiles (${options.length})`); listed = true; }
          const current = numbered.find(([, [name]]) => name === process.env[v]);
          const hint = current ? `Enter keeps ${current[0]}, - skips` : 'Enter skips';
          for (;;) {
            const pick = (await ask(`  ${v}: number or part of a name (${hint})`, current ? String(current[0]) : '')).trim();
            if (!pick || pick === '-') break;
            if (/^\d+$/.test(pick)) {
              if (Number(pick) >= 1 && Number(pick) <= options.length) { values[v] = options[Number(pick) - 1][0]; break; }
              console.log(`  No profile number ${pick}: pick 1 to ${options.length}.`);
              continue;
            }
            const q = pick.toLowerCase();
            const matches = numbered.filter(([, [name, , role]]) => name.toLowerCase().includes(q) || role.toLowerCase().includes(q));
            if (matches.length === 1) { values[v] = matches[0][1][0]; break; }
            if (matches.length) show(matches, `Matching '${pick}' (${matches.length})`);
            else console.log(`  No read-only profile matches '${pick}'.`);
          }
          continue;
        }
        const value = await ask(`  ${v} (blank to skip)`, process.env[v] || found[v] || '');
        if (value) values[v] = value;
      }
      connectors[name] = values;
    }
    const own = await ask('Your own profile .json file (blank to skip)');
    if (own) connectors[own] = {};
    conf.connectors = connectors;

    const text = cf.dump(conf);
    console.log(`\n${color('bold', file)}\n${text}`);
    if (existsSync(file) && !(await yes(`${file} exists. Replace it?`, false))) return 1;
    if (!(await yes(`Write ${file}?`, true))) return 1;
    write(file, text);
    cf.load(file); // same checks as `1xops config --file`

    console.log('\nChanges this would make:');
    if (config({ file, preview: 'summary' }) !== 0) return 2;
    if (await yes('Show every line first?', false)) config({ file, preview: 'full' });
    if (await yes('Apply them now?', false)) return config({ file, yes: true });
    console.log(`Apply later with: 1xops config --file ${file} --yes`);
    return 0;
  } finally {
    rl.close();
  }
}
