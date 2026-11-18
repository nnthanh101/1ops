// TEST-009 (#37) for story 1XOPS-009 (#38), Node.js side: the same cases as packages/python/tests/test_session_start.py.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { chmodSync, mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const AWS_FILE = 'ONEXOPS_CONNECTORS=aws\nAWS_BILLING_PROFILE=readonly\nAWS_OPERATIONS_PROFILE=readonly\n';
const AWS = `#!/bin/sh
case "$FAKE_AWS" in
  ready) echo '{"Account":"123456789012","Arn":"arn:aws:sts::123456789012:assumed-role/ReadOnlyAccess/me"}' ;;
  expired) echo "The SSO session associated with this profile has expired" >&2; exit 255 ;;
  hang) sleep 30 ;;
esac
`;
const BIN = path.resolve(import.meta.dirname, '../bin/1xops.mjs');

function start(mode, { settings = AWS_FILE, within = '4', hook = true } = {}) {
  const dir = mkdtempSync(path.join(os.tmpdir(), '1xops-start-'));
  mkdirSync(path.join(dir, 'bin'));
  writeFileSync(path.join(dir, 'bin', 'aws'), AWS);
  chmodSync(path.join(dir, 'bin', 'aws'), 0o755);
  const file = path.join(dir, '.env.1xops');
  if (settings != null) writeFileSync(file, settings);
  const env = { PATH: `${path.join(dir, 'bin')}:/usr/bin:/bin:${path.dirname(process.execPath)}`, HOME: dir, CLAUDE_CONFIG_DIR: path.join(dir, 'host'), FAKE_AWS: mode };
  const began = Date.now();
  const r = spawnSync(process.execPath, [BIN, 'doctor', hook ? '--hook' : '--brief', '--within', within, '--file', file], { env, cwd: dir, encoding: 'utf8' });
  return { code: r.status, out: r.stdout, seconds: (Date.now() - began) / 1000 };
}

test('a signed out connector is named with its fix in the host format', () => {
  const { code, out } = start('expired');
  assert.equal(code, 0);
  const message = JSON.parse(out);
  assert.match(message.systemMessage, /aws sso login --profile readonly/);
  assert.deepEqual(message.hookSpecificOutput, { hookEventName: 'SessionStart', additionalContext: message.systemMessage });
  assert.ok(!out.includes('123456789012'));
});

test('nothing is shown when every connector is ready', () => {
  const { code, out } = start('ready');
  assert.deepEqual([code, out], [0, '']);
});

test('nothing is shown without a settings file', () => {
  const { code, out } = start('expired', { settings: null });
  assert.deepEqual([code, out], [0, '']);
});

test('a hung check ends within the time given, with one line saying so', () => {
  const { code, out, seconds } = start('hang', { within: '1' });
  assert.ok(seconds < 3, `took ${seconds} s`);
  assert.equal(code, 0);
  assert.match(JSON.parse(out).systemMessage, /the check did not finish in 1 s/);
});

test('the plain brief prints the same text without the host envelope', () => {
  assert.equal(start('expired', { hook: false }).out.trim(), JSON.parse(start('expired').out).systemMessage);
});
