"""1ops.yaml: the end-user configuration file. Non-secret values only.

    scope: team                      # org | team | local | personal
    dir: .                           # project or tenant folder (team, local)
    connectors:
      aws:
        AWS_OPERATIONS_PROFILE: "ops-readonly"
        AWS_REGION: "ap-southeast-2"
      itsm: {}
      ./my-profile.json: {}          # your own profile file

Keys under each connector are the ${VAR} names its servers use (see `1ops profiles`).
Secrets stay in SSO, `az login` or OAuth and never go in this file.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from one_ops import settings as s

VAR = re.compile(r"\$\{([A-Z0-9_]+)(?::-[^}]*)?\}")
SECRET_HINTS = ("TOKEN", "SECRET", "PASSWORD", "API_KEY")


def variables(profile: dict) -> list[str]:
    """Every ${VAR} a profile's servers read, in order of first use."""
    found = VAR.findall(s.dumps(profile["mcpServers"]))
    return list(dict.fromkeys(found))


def substitute(value, values: dict[str, str]):
    """Replace ${VAR} / ${VAR:-default} with known values; leave unknown ones as they are."""
    if isinstance(value, str):
        return VAR.sub(lambda m: values.get(m.group(1), m.group(0)), value)
    if isinstance(value, list):
        return [substitute(v, values) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v, values) for k, v in value.items()}
    return value


def load(path: Path) -> dict:
    """Read and check 1ops.yaml. Returns {scope, dir, out, connectors: {name: {VAR: value}}}."""
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise TypeError(f"{path}: expected a mapping at the top level")
    scope = data.get("scope", "team")
    if scope not in s.SCOPES:
        raise ValueError(f"{path}: scope must be one of {', '.join(s.SCOPES)}")
    connectors = data.get("connectors") or {}
    if not isinstance(connectors, dict):
        raise TypeError(f"{path}: 'connectors' must be a mapping of profile → values")
    for name, values in connectors.items():
        values = values or {}
        connectors[name] = values
        for key, value in values.items():
            if not isinstance(value, str):
                raise TypeError(
                    f"{path}: {name}.{key} must be a quoted string (YAML read {value!r})"
                )
            if any(h in key for h in SECRET_HINTS):
                raise ValueError(
                    f"{path}: {name}.{key} looks like a secret; keep it in your keychain or "
                    "sign-in, not in 1ops.yaml"
                )
    return {
        "scope": scope,
        "dir": str(data.get("dir", ".")),
        "out": data.get("out"),
        "connectors": connectors,
    }


def dump(config: dict) -> str:
    header = "# 1ops.yaml — non-secret values only. Do not commit if it holds personal values.\n"
    return header + yaml.safe_dump(config, sort_keys=False, default_flow_style=False)
