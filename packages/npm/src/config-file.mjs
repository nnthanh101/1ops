// .env.1xops: the end-user configuration file. Non-secret values only. Same rules as the Python
// package (packages/python/src/one_xops/config_file.py):
//   ONEXOPS_SCOPE=team            org | team | local | personal
//   ONEXOPS_DIR=.                 project or tenant folder (team, local)
//   ONEXOPS_CONNECTORS=aws,itsm   built-in profiles, or paths to your own .json profiles
//   AWS_REGION=ap-southeast-2     every other KEY=value fills a ${KEY} in the profiles
import { readFileSync } from 'node:fs';
import { SCOPES, dumps } from './settings.mjs';

export const DEFAULT_FILE = '.env.1xops';
const VAR = /\$\{([A-Z0-9_]+)(?::-[^}]*)?\}/g;
const KEY = /^[A-Z_][A-Z0-9_]*$/;
const SECRET_HINTS = ['TOKEN', 'SECRET', 'PASSWORD', 'API_KEY'];
const OWN = new Set(['ONEXOPS_SCOPE', 'ONEXOPS_DIR', 'ONEXOPS_OUT', 'ONEXOPS_CONNECTORS']);

// Every ${VAR} a profile's servers read, in order of first use.
export function variables(profile) {
  return [...new Set([...dumps(profile.mcpServers).matchAll(VAR)].map((m) => m[1]))];
}

// Replace ${VAR} / ${VAR:-default} with known values; leave unknown ones as they are.
export function substitute(value, values) {
  if (typeof value === 'string') return value.replace(VAR, (whole, name) => values[name] ?? whole);
  if (Array.isArray(value)) return value.map((v) => substitute(v, values));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, substitute(v, values)]));
  }
  return value;
}

// KEY=value lines; '#' comments and blank lines ignored; one pair of surrounding quotes removed.
export function parse(text, where = '.env') {
  const pairs = {};
  text.split(/\r?\n/).forEach((raw, i) => {
    let line = raw.trim();
    if (!line || line.startsWith('#')) return;
    if (line.startsWith('export ')) line = line.slice(7).trimStart();
    const eq = line.indexOf('=');
    const key = eq === -1 ? line : line.slice(0, eq).trim();
    let value = eq === -1 ? '' : line.slice(eq + 1).trim();
    if (eq === -1 || !KEY.test(key)) throw new Error(`${where}:${i + 1}: expected KEY=value with an upper-case KEY`);
    if (value.length >= 2 && value[0] === value.at(-1) && `'"`.includes(value[0])) value = value.slice(1, -1);
    else value = value.split(' #')[0].trimEnd();
    pairs[key] = value;
  });
  return pairs;
}

// Read and check .env.1xops. Returns {scope, dir, out, connectors: {name: values}, values}.
export function load(file) {
  const pairs = parse(readFileSync(file, 'utf8'), file);
  for (const key of Object.keys(pairs)) {
    if (key.startsWith('ONEXOPS_') && !OWN.has(key)) {
      throw new Error(`${file}: unknown setting ${key}; use one of ${[...OWN].sort().join(', ')}`);
    }
    if (SECRET_HINTS.some((h) => key.includes(h))) {
      throw new Error(`${file}: ${key} looks like a secret; keep it in your keychain or sign-in, not in this file`);
    }
  }
  const scope = pairs.ONEXOPS_SCOPE ?? 'team';
  if (!SCOPES.includes(scope)) throw new Error(`${file}: ONEXOPS_SCOPE must be one of ${SCOPES.join(', ')}`);
  const values = Object.fromEntries(Object.entries(pairs).filter(([k]) => !OWN.has(k)));
  const names = (pairs.ONEXOPS_CONNECTORS ?? '').split(',').map((c) => c.trim()).filter(Boolean);
  return {
    scope,
    dir: pairs.ONEXOPS_DIR ?? '.',
    out: pairs.ONEXOPS_OUT || null,
    connectors: Object.fromEntries(names.map((n) => [n, values])),
    values,
  };
}

// The .env.1xops text for a config made by `1xops setup`.
export function dump(config) {
  const lines = [
    '# 1xops: non-secret values only. Secrets stay in AWS SSO, az login or the Atlassian sign-in.',
    `ONEXOPS_SCOPE=${config.scope}`,
  ];
  if (config.dir) lines.push(`ONEXOPS_DIR=${config.dir}`);
  if (config.out) lines.push(`ONEXOPS_OUT=${config.out}`);
  const connectors = config.connectors ?? {};
  lines.push(`ONEXOPS_CONNECTORS=${Object.keys(connectors).join(',')}`);
  const seen = Object.assign({}, ...Object.values(connectors));
  for (const [k, v] of Object.entries(seen)) lines.push(`${k}=${v}`);
  return `${lines.join('\n')}\n`;
}
