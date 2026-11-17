// TEST-001 (#22) for story #5, Node.js side: the same shim scenarios as packages/python/tests/test_first_result.py.
// Fake `aws` and `az` programs on PATH; offline; temporary folders only.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { checkConnectors } from '../src/commands.mjs';

const AWS = `#!/bin/sh
echo "aws $*" >> "$SHIM_LOG"
role() { echo '{"Account":"123456789012","Arn":"arn:aws:sts::123456789012:assumed-role/'"$1"'/me"}'; }
case "$FAKE_AWS" in
  ready) role ReadOnlyAccess ;;
  admin) role AdministratorAccess ;;
  expired) echo "The SSO session associated with this profile has expired" >&2; exit 255 ;;
  notfound) echo "The config profile (readonly) could not be found" >&2; exit 255 ;;
esac
`;
const AZ = `#!/bin/sh
echo "az $*" >> "$SHIM_LOG"
case "$1 $2" in
  "account show") [ "$FAKE_AZ" = signedout ] && exit 1; echo reader@example.invalid ;;
  "role assignment")
    case "$FAKE_AZ" in
      reader) echo '["Reader","Cost Management Reader"]' ;;
      contributor) echo '["Reader","Contributor"]' ;;
    esac ;;
esac
`;
const AWS_FILE = 'ONEXOPS_CONNECTORS=aws\nAWS_BILLING_PROFILE=readonly\nAWS_OPERATIONS_PROFILE=readonly\n';

function scenario(settings, { aws = '', az = '' } = {}, fn) {
  const dir = mkdtempSync(path.join(os.tmpdir(), '1xops-shim-'));
  const bin = path.join(dir, 'bin');
  mkdirSync(bin);
  for (const [name, text] of [['aws', AWS], ['az', AZ]]) { writeFileSync(path.join(bin, name), text); chmodSync(path.join(bin, name), 0o755); }
  const log = path.join(dir, 'calls.log');
  writeFileSync(log, '');
  const file = path.join(dir, '.env.1xops');
  writeFileSync(file, settings);
  const saved = { ...process.env };
  Object.assign(process.env, { PATH: `${bin}${path.delimiter}${process.env.PATH}`, SHIM_LOG: log, FAKE_AWS: aws, FAKE_AZ: az });
  delete process.env.AWS_BILLING_PROFILE;
  delete process.env.AWS_OPERATIONS_PROFILE;
  try { return fn(file, () => readFileSync(log, 'utf8').split('\n').filter(Boolean)); } finally {
    for (const k of Object.keys(process.env)) if (!(k in saved)) delete process.env[k];
    Object.assign(process.env, saved);
  }
}

const AWS_STATES = {
  ready: ['ready', 'profile readonly, account ****9012, read-only'],
  admin: ['check', 'profile readonly, account ****9012, can change things: use a read-only role'],
  expired: ['signed out', 'aws sso login --profile readonly'],
  notfound: ['missing', 'profile readonly not found: aws configure sso --profile readonly, or set AWS_CONFIG_FILE'],
};
for (const [mode, [status, fix]] of Object.entries(AWS_STATES)) {
  test(`aws connector ${mode} is ${status}`, () => scenario(AWS_FILE, { aws: mode }, (file) => {
    const rows = checkConnectors(file).filter((r) => r[0].startsWith('aws '));
    assert.deepEqual(rows.map((r) => r[0]), ['aws AWS_BILLING_PROFILE', 'aws AWS_OPERATIONS_PROFILE']);
    for (const r of rows) assert.deepEqual(r.slice(1), [status, fix]);
  }));
}

test('aws profile not set says where to set it, and makes no call', () => scenario('ONEXOPS_CONNECTORS=aws\n', {}, (file, calls) => {
  const rows = checkConnectors(file);
  assert.deepEqual(rows[0], ['aws AWS_BILLING_PROFILE', 'missing', 'set AWS_BILLING_PROFILE in .env.1xops or the shell (1xops setup)']);
  assert.deepEqual(calls(), []);
}));

const AZURE_STATES = {
  signedout: ['signed out', 'az login with a read-only (Reader) identity, in its own AZURE_CONFIG_DIR'],
  contributor: ['check', 'can change things: use a read-only (Reader) identity'],
  reader: ['ready', 'read-only'],
};
for (const [mode, [status, fix]] of Object.entries(AZURE_STATES)) {
  test(`azure connector ${mode} is ${status}`, () => scenario('ONEXOPS_CONNECTORS=azure\n', { az: mode }, (file) => {
    assert.deepEqual(checkConnectors(file), [['azure', status, fix]]);
  }));
}

test('http connectors say where to sign in', () => scenario('ONEXOPS_CONNECTORS=itsm\n', {}, (file) => {
  assert.deepEqual(checkConnectors(file), [['atlassian', 'check', 'signs in inside the host: run /mcp and choose atlassian']]);
}));

test('the check only reads identity: three known calls, nothing else', () => {
  for (const [aws, az] of [['ready', 'reader'], ['admin', 'contributor'], ['expired', 'signedout'], ['notfound', 'reader']]) {
    scenario(`ONEXOPS_CONNECTORS=aws,azure,itsm\nAWS_BILLING_PROFILE=readonly\nAWS_OPERATIONS_PROFILE=readonly\n`, { aws, az }, (file, calls) => {
      const before = readFileSync(file, 'utf8');
      checkConnectors(file);
      assert.ok(calls().length > 0, 'the shims were never reached');
      for (const c of calls()) assert.ok(/^(aws sts get-caller-identity |az account show |az role assignment list )/.test(c), c);
      assert.equal(readFileSync(file, 'utf8'), before);
    });
  }
});
