// Same cases as the Python tests (packages/python/tests/test_config.py), run against the native
// Node.js CLI as a real subprocess. Offline; temporary folders only.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as cf from '../src/config-file.mjs';
import * as s from '../src/settings.mjs';
import { accessFromRole, awsFix, azureAccess, checkConnectors, mask, scrub } from '../src/commands.mjs';

const BIN = fileURLToPath(new URL('../bin/1xops.mjs', import.meta.url));
const tmp = () => mkdtempSync(path.join(os.tmpdir(), '1xops-'));
const cli = (args, env = {}) => spawnSync(process.execPath, [BIN, ...args], { encoding: 'utf8', env: { ...process.env, ...env } });
const json = (f) => JSON.parse(readFileSync(f, 'utf8'));

test('merge keeps user values, adds missing, and is idempotent', () => {
  const existing = { model: 'x', permissions: { deny: ['Read(./secrets)'] }, enabledPlugins: { '1xops@1xops': false } };
  const merged = s.merge(existing, s.BASELINE);
  assert.equal(merged.model, 'x');
  assert.equal(merged.enabledPlugins['1xops@1xops'], false);
  assert.equal(merged.permissions.deny[0], 'Read(./secrets)');
  assert.ok(merged.permissions.deny.includes('Read(./.env)'));
  assert.deepEqual(s.merge(merged, s.BASELINE), merged);
});

for (const name of ['aws', 'azure', 'itsm']) {
  test(`built-in profile ${name} is pinned and keeps secrets out`, () => {
    const profile = s.loadProfile(name);
    for (const server of Object.values(profile.mcpServers)) {
      assert.ok(!JSON.stringify(server).includes('@latest'));
      for (const [key, value] of Object.entries(server.env ?? {})) {
        if (['TOKEN', 'KEY', 'PROFILE', '_ID', 'USERNAME', 'URL'].some((k) => key.includes(k))) assert.ok(value.startsWith('${'), key);
      }
    }
  });
}

test('unknown or empty profiles are rejected; own profile file works', () => {
  const d = tmp();
  assert.throws(() => s.loadProfile('nope'));
  writeFileSync(path.join(d, 'bad.json'), '{}');
  assert.throws(() => s.loadProfile(path.join(d, 'bad.json')));
  writeFileSync(path.join(d, 'mine.json'), JSON.stringify({ mcpServers: { x: { type: 'http', url: 'https://example.invalid/mcp' } } }));
  assert.ok('x' in s.loadProfile(path.join(d, 'mine.json')).mcpServers);
});

test('team dry run writes nothing', () => {
  const d = tmp();
  assert.equal(cli(['config', '--scope', 'team', '--dir', d, '--connectors', 'aws']).status, 0);
  assert.ok(!existsSync(path.join(d, '.claude')) && !existsSync(path.join(d, '.mcp.json')));
});

test('team write keeps existing servers; second run is a no-op', () => {
  const d = tmp();
  writeFileSync(path.join(d, '.mcp.json'), JSON.stringify({ mcpServers: { mine: { command: 'x' } } }));
  const args = ['config', '--scope', 'team', '--dir', d, '--connectors', 'aws', 'itsm', '--yes'];
  assert.equal(cli(args).status, 0);
  const settings = json(path.join(d, '.claude', 'settings.json'));
  assert.equal(settings.enabledPlugins['1xops@1xops'], true);
  assert.ok(settings.permissions.ask.includes('mcp__atlassian__*'));
  const mcp = json(path.join(d, '.mcp.json')).mcpServers;
  assert.ok('mine' in mcp && 'awslabs-cloudtrail' in mcp && 'atlassian' in mcp);
  const before = readFileSync(path.join(d, '.mcp.json'), 'utf8');
  assert.equal(cli(args).status, 0);
  assert.equal(readFileSync(path.join(d, '.mcp.json'), 'utf8'), before);
});

test('org scope writes to the out folder only', () => {
  const d = tmp();
  assert.equal(cli(['config', '--scope', 'org', '--out', d, '--connectors', 'azure', '--yes']).status, 0);
  assert.ok(existsSync(path.join(d, 'managed-settings.json')));
  assert.ok('azure' in json(path.join(d, 'managed-mcp.json')).mcpServers);
});

test('mask never shows the full account', () => assert.equal(mask('123456789012'), '****9012'));

test('.env.1xops refuses secrets, unknown settings, bad scope and bad keys', () => {
  const d = tmp();
  const f = path.join(d, '.env.1xops');
  for (const [text, re] of [['GRAFANA_API_KEY=x\n', /secret/], ['ONEXOPS_SCOPES=team\n', /unknown setting/], ['ONEXOPS_SCOPE=everyone\n', /ONEXOPS_SCOPE/], ['aws_region=x\n', /KEY=value/]]) {
    writeFileSync(f, text);
    assert.throws(() => cf.load(f), re);
  }
});

test('.env.1xops parses quotes, comments and leading zeros', () => {
  const f = path.join(tmp(), '.env.1xops');
  writeFileSync(f, "# comment\nONEXOPS_CONNECTORS=aws, azure\nAZURE_TENANT_ID=0123  # kept as text\nAWS_REGION='ap-southeast-2'\n");
  const cfg = cf.load(f);
  assert.deepEqual(Object.keys(cfg.connectors), ['aws', 'azure']);
  assert.deepEqual(cfg.values, { AZURE_TENANT_ID: '0123', AWS_REGION: 'ap-southeast-2' });
  assert.equal(cfg.scope, 'team');
  assert.equal(cfg.dir, '.');
});

test('dump round-trips', () => {
  const f = path.join(tmp(), '.env.1xops');
  writeFileSync(f, cf.dump({ scope: 'local', dir: '/w', connectors: { aws: { AWS_REGION: 'r' }, itsm: {} } }));
  const cfg = cf.load(f);
  assert.equal(cfg.scope, 'local');
  assert.deepEqual(Object.keys(cfg.connectors), ['aws', 'itsm']);
  assert.deepEqual(cfg.values, { AWS_REGION: 'r' });
});

test('variables and substitute', () => {
  const vars = cf.variables(s.loadProfile('aws'));
  for (const v of ['AWS_BILLING_PROFILE', 'AWS_OPERATIONS_PROFILE', 'AWS_REGION']) assert.ok(vars.includes(v));
  assert.deepEqual(cf.substitute({ env: { A: '${AWS_REGION}', B: '${OTHER:-x}' } }, { AWS_REGION: 'r' }), { env: { A: 'r', B: '${OTHER:-x}' } });
});

test('team scope from .env.1xops keeps ${VAR} references out of git', () => {
  const d = tmp();
  const f = path.join(d, '.env.1xops');
  writeFileSync(f, `ONEXOPS_SCOPE=team\nONEXOPS_DIR=${d}\nONEXOPS_CONNECTORS=aws\nAWS_OPERATIONS_PROFILE=ops-ro\n`);
  assert.equal(cli(['config', '--file', f, '--yes']).status, 0);
  const text = readFileSync(path.join(d, '.mcp.json'), 'utf8');
  assert.ok(text.includes('${AWS_OPERATIONS_PROFILE}') && !text.includes('ops-ro'));
});

test('env prints quoted exports and no ONEXOPS_ settings', () => {
  const f = path.join(tmp(), '.env.1xops');
  writeFileSync(f, "ONEXOPS_CONNECTORS=aws\nAWS_REGION=ap-southeast-2\nAWS_OPERATIONS_PROFILE='a b'\n");
  const r = cli(['env', '--file', f]);
  assert.equal(r.status, 0);
  assert.ok(r.stdout.includes('export AWS_REGION=ap-southeast-2'));
  assert.ok(r.stdout.includes("export AWS_OPERATIONS_PROFILE='a b'"));
  assert.ok(!r.stdout.includes('ONEXOPS_'));
});

test('local scope without the host CLI writes nothing', () => {
  const project = path.join(tmp(), 'proj');
  mkdirSync(project);
  const r = cli(['config', '--scope', 'local', '--dir', project, '--connectors', 'aws', '--yes'], { PATH: path.dirname(process.execPath) });
  assert.equal(r.status, 1);
  assert.ok(!existsSync(path.join(project, '.claude')));
});

test('scrub masks every 12-digit account ID in any text', () => {
  assert.equal(scrub('arn:aws:sts::123456789012:assumed-role/Admin-123456789012/x'), 'arn:aws:sts::****9012:assumed-role/Admin-****9012/x');
  assert.equal(scrub('aws-cli/2.31.0'), 'aws-cli/2.31.0');
});

test('accessFromRole tells read-only from roles that can change things', () => {
  const arn = (role) => `arn:aws:sts::123456789012:assumed-role/${role}/me`;
  assert.equal(accessFromRole(arn('AWSReservedSSO_ReadOnlyAccess_abc')), 'read');
  assert.equal(accessFromRole(arn('SecurityAudit')), 'read');
  assert.equal(accessFromRole(arn('AWSReservedSSO_AdministratorAccess_abc')), 'write');
  assert.equal(accessFromRole('arn:aws:iam::123456789012:root'), 'write');
  assert.equal(accessFromRole(arn('ops')), 'unknown');
  assert.equal(accessFromRole(undefined), 'unknown');
});

// Real AWS CLI error text, captured on 2026-11-17 (account IDs removed).
const EXPIRED = 'aws: [ERROR]: Error when retrieving token from sso: Token has expired and refresh failed';
const NOT_FOUND = 'aws: [ERROR]: The config profile (p) could not be found';
const NO_CREDS = 'aws: [ERROR]: An error occurred (NoCredentials): Unable to locate credentials. You can configure credentials by running "aws login".';

test('awsFix names the exact command', () => {
  assert.deepEqual(awsFix(EXPIRED, 'p'), ['signed out', 'aws sso login --profile p']);
  assert.deepEqual(awsFix(NO_CREDS, 'p'), ['signed out', 'aws sso login --profile p']);
  assert.equal(awsFix(NOT_FOUND, 'p')[0], 'missing');
  assert.deepEqual(awsFix('aws: [ERROR]: other', 'p'), ['check', 'other']);
});

test('azureAccess', () => {
  assert.equal(azureAccess(['Reader', 'Cost Management Reader']), 'read');
  assert.equal(azureAccess(['Reader', 'Contributor']), 'write');
  assert.equal(azureAccess(['User Access Administrator']), 'write');
  assert.equal(azureAccess([]), 'unknown');
});

test('doctor without a settings file says run setup', () => {
  const f = path.join(tmp(), '.env.1xops');
  assert.deepEqual(checkConnectors(f), [['connectors', 'missing', `no ${f} here: run 1xops setup`]]);
});
