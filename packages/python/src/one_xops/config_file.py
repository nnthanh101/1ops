""".env.1xops: the end-user configuration file. Non-secret values only.

    # 1xops: non-secret values only. Secrets stay in AWS SSO, az login or the Atlassian sign-in.
    ONEXOPS_SCOPE=team                 # org | team | local | personal
    ONEXOPS_DIR=.                      # project or tenant folder (team, local)
    ONEXOPS_CONNECTORS=aws,itsm        # built-in profiles, or paths to your own .json profiles
    AWS_OPERATIONS_PROFILE=ops-readonly
    AWS_REGION=ap-southeast-2
    AWS_OPERATIONS_ACCOUNT=123456789012   # optional: the account this tenant expects, else doctor names a wrong one
    ONEXOPS_IGNORE=gmail,google calendar  # optional: connectors the session start never names

Every other KEY=value line is a value for the ${KEY} references in the connector profiles
(see `1xops profiles`). Plain KEY=value, so the shell, Python and Node.js all read it natively.
"""

from __future__ import annotations

import re
from pathlib import Path

from one_xops import settings as s

DEFAULT_FILE = ".env.1xops"
VAR = re.compile(r"\$\{([A-Z0-9_]+)(?::-[^}]*)?\}")
KEY = re.compile(r"^[A-Z_][A-Z0-9_]*$")
SECRET_HINTS = ("TOKEN", "SECRET", "PASSWORD", "API_KEY")
OWN = {"ONEXOPS_SCOPE", "ONEXOPS_DIR", "ONEXOPS_OUT", "ONEXOPS_CONNECTORS"}
KNOWN = OWN | {"ONEXOPS_IGNORE"}  # IGNORE stays among the values: doctor reads it


def variables(profile: dict) -> list[str]:
    """Every ${VAR} a profile's servers read, in order of first use."""
    return list(dict.fromkeys(VAR.findall(s.dumps(profile["mcpServers"]))))


def substitute(value, values: dict[str, str]):
    """Replace ${VAR} / ${VAR:-default} with known values; leave unknown ones as they are."""
    if isinstance(value, str):
        return VAR.sub(lambda m: values.get(m.group(1), m.group(0)), value)
    if isinstance(value, list):
        return [substitute(v, values) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v, values) for k, v in value.items()}
    return value


def parse(text: str, where: str = ".env") -> dict[str, str]:
    """KEY=value lines; '#' comments and blank lines ignored; one pair of surrounding quotes removed."""
    pairs: dict[str, str] = {}
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = line.removeprefix("export ").lstrip()
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not KEY.match(key):
            raise ValueError(f"{where}:{n}: expected KEY=value with an upper-case KEY")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].rstrip()
        pairs[key] = value
    return pairs


def load(path: Path) -> dict:
    """Read and check .env.1xops. Returns {scope, dir, out, connectors: {name: values}, values}."""
    pairs = parse(path.read_text(), str(path))
    for key in pairs:
        if key.startswith("ONEXOPS_") and key not in KNOWN:
            raise ValueError(
                f"{path}: unknown setting {key}; use one of {', '.join(sorted(KNOWN))}"
            )
        if any(h in key for h in SECRET_HINTS):
            raise ValueError(
                f"{path}: {key} looks like a secret; keep it in your keychain or sign-in, "
                "not in this file"
            )
    scope = pairs.get("ONEXOPS_SCOPE", "team")
    if scope not in s.SCOPES:
        raise ValueError(f"{path}: ONEXOPS_SCOPE must be one of {', '.join(s.SCOPES)}")
    values = {k: v for k, v in pairs.items() if k not in OWN}
    names = [c.strip() for c in pairs.get("ONEXOPS_CONNECTORS", "").split(",") if c.strip()]
    return {
        "scope": scope,
        "dir": pairs.get("ONEXOPS_DIR", "."),
        "out": pairs.get("ONEXOPS_OUT") or None,
        "connectors": {name: values for name in names},
        "values": values,
    }


def dump(config: dict) -> str:
    """The .env.1xops text for a config made by `1xops setup`."""
    lines = [
        "# 1xops: non-secret values only. Secrets stay in AWS SSO, az login or the Atlassian sign-in.",
        f"ONEXOPS_SCOPE={config['scope']}",
    ]
    if config.get("dir"):
        lines.append(f"ONEXOPS_DIR={config['dir']}")
    if config.get("out"):
        lines.append(f"ONEXOPS_OUT={config['out']}")
    lines.append(f"ONEXOPS_CONNECTORS={','.join(config.get('connectors', {}))}")
    seen: dict[str, str] = {}
    for values in config.get("connectors", {}).values():
        seen.update(values)
    lines += [f"{k}={v}" for k, v in seen.items()]
    return "\n".join(lines) + "\n"
