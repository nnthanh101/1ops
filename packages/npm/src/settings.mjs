// Settings and connector files for each scope. Pure functions; the commands do the writing.
// Same behaviour as the Python package (packages/python/src/one_xops/settings.py).
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const HOST = 'claude'; // host CLI binary and config folder name (technical identifier)
export const SCOPES = ['org', 'team', 'local', 'personal'];

const MARKETPLACES = {
  '1xops': { source: { source: 'github', repo: 'nnthanh101/1xops' } },
  'knowledge-work-plugins': { source: { source: 'github', repo: 'anthropics/knowledge-work-plugins' } },
};

// Baseline every scope receives: the plugin, its base dependency, no secret reads,
// and a person's yes before anything leaves the machine or rewrites history.
export const BASELINE = {
  extraKnownMarketplaces: MARKETPLACES,
  enabledPlugins: { '1xops@1xops': true, 'operations@knowledge-work-plugins': true },
  permissions: {
    deny: ['Read(./.env)', 'Read(./.env.*)', 'Read(./**/.env)', 'Read(./**/.env.*)'],
    ask: [
      'Bash(git push *)',
      'Bash(git reset --hard *)',
      'Bash(git tag *)',
      'Bash(gh pr merge *)',
      'Bash(gh release *)',
      'Bash(terraform apply *)',
      'Bash(terraform destroy *)',
    ],
  },
};

export function managedDir() {
  if (process.platform === 'darwin') return '/Library/Application Support/ClaudeCode';
  if (process.platform === 'win32') return 'C:/Program Files/ClaudeCode';
  return '/etc/claude-code';
}

export function settingsPath(scope, project, out) {
  if (scope === 'org') return path.join(out ?? process.cwd(), 'managed-settings.json');
  if (scope === 'team') return path.join(project, `.${HOST}`, 'settings.json');
  if (scope === 'local') return path.join(project, `.${HOST}`, 'settings.local.json');
  if (scope === 'personal') return path.join(os.homedir(), `.${HOST}`, 'settings.json');
  throw new Error(`unknown scope: ${scope}`);
}

// File-based connector scopes. `local` and `personal` go through the host CLI instead.
export function mcpPath(scope, project, out) {
  if (scope === 'org') return path.join(out ?? process.cwd(), 'managed-mcp.json');
  if (scope === 'team') return path.join(project, '.mcp.json');
  return null;
}

const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// Add incoming keys without overwriting anything the user already set:
// objects merge recursively, arrays gain only missing items, existing scalars win.
export function merge(existing, incoming) {
  const out = { ...existing };
  for (const [key, value] of Object.entries(incoming)) {
    if (!(key in out)) out[key] = value;
    else if (isObject(out[key]) && isObject(value)) out[key] = merge(out[key], value);
    else if (Array.isArray(out[key]) && Array.isArray(value)) {
      out[key] = [...out[key], ...value.filter((v) => !out[key].some((o) => same(o, v)))];
    }
  }
  return out;
}

// The profiles ship inside the npm package (copied in by `npm pack`); in this repository they are
// read from their one source, the Python package.
const here = path.dirname(fileURLToPath(import.meta.url));
const PROFILE_DIRS = [path.join(here, '..', 'profiles'), path.join(here, '..', '..', 'python', 'src', 'one_xops', 'profiles')];
const profileDir = () => PROFILE_DIRS.find((d) => existsSync(d));

export function builtinProfiles() {
  return readdirSync(profileDir()).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5)).sort();
}

// A built-in profile name (aws, azure, itsm) or a path to your own JSON file.
export function loadProfile(nameOrPath) {
  let data;
  if (nameOrPath.endsWith('.json') && existsSync(nameOrPath) && statSync(nameOrPath).isFile()) {
    data = JSON.parse(readFileSync(nameOrPath, 'utf8'));
  } else if (builtinProfiles().includes(nameOrPath)) {
    data = JSON.parse(readFileSync(path.join(profileDir(), `${nameOrPath}.json`), 'utf8'));
  } else {
    throw new Error(
      `unknown profile '${nameOrPath}': use one of ${builtinProfiles().join(', ')} or a path to a .json file with an 'mcpServers' object`,
    );
  }
  if (!isObject(data.mcpServers) || Object.keys(data.mcpServers).length === 0) {
    throw new Error(`profile '${nameOrPath}' has no 'mcpServers' object`);
  }
  return data;
}

export function readJson(file) {
  if (!existsSync(file)) return {};
  const text = readFileSync(file, 'utf8');
  return text.trim() ? JSON.parse(text) : {};
}

export const dumps = (data) => `${JSON.stringify(data, null, 2)}\n`;
