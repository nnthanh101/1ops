"""Settings and connector files for each scope. Pure functions; the CLI does the writing."""

from __future__ import annotations

import json
import os
import platform
from importlib import resources
from pathlib import Path

HOST = "claude"  # host CLI binary and config folder name (technical identifier)

SCOPES = ("org", "team", "local", "personal")

# The rules each scope receives live in templates/settings/{org,team,local,personal}.json, one file per scope,
# compared on one page in templates/settings/README.md. A build copies them next to this file.


def template_dir() -> Path:
    """The scope templates: next to this file when installed, else the repository's templates/settings."""
    packaged = Path(__file__).parent / "templates" / "settings"
    return (
        packaged
        if packaged.is_dir()
        else Path(__file__).resolve().parents[4] / "templates" / "settings"
    )


def template(scope: str) -> dict:
    """The settings a scope receives: org, team, local or personal."""
    return json.loads((template_dir() / f"{scope}.json").read_text())


def __getattr__(name: str):
    """BASELINE: the team rules, for callers that read them as a constant."""
    if name == "BASELINE":
        return template("team")
    raise AttributeError(name)


def managed_dir() -> Path:
    """Where IT installs organisation-wide (managed) files on this OS."""
    if platform.system() == "Darwin":
        return Path("/Library/Application Support/ClaudeCode")
    if platform.system() == "Windows":
        return Path("C:/Program Files/ClaudeCode")
    return Path("/etc/claude-code")


def settings_path(scope: str, project: Path, out: Path | None = None) -> Path:
    """The settings file for a scope. `org` writes to `out` for IT to deploy."""
    if scope == "org":
        return (out or Path.cwd()) / "managed-settings.json"
    if scope == "team":
        return project / f".{HOST}" / "settings.json"
    if scope == "local":
        return project / f".{HOST}" / "settings.local.json"
    if scope == "personal":
        return Path.home() / f".{HOST}" / "settings.json"
    raise ValueError(f"unknown scope: {scope}")


def mcp_path(scope: str, project: Path, out: Path | None = None) -> Path | None:
    """File-based connector scopes. `local` and `personal` go through the host CLI instead."""
    if scope == "org":
        return (out or Path.cwd()) / "managed-mcp.json"
    if scope == "team":
        return project / ".mcp.json"
    return None


def _canon(value) -> str:
    """One text per value, whatever the key order: the same rule as the Node.js package."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def merge(existing: dict, incoming: dict) -> dict:
    """Add incoming keys without overwriting anything the user already set.

    Dicts merge recursively, lists gain only missing items, existing scalars win.
    """
    out = dict(existing)
    for key, value in incoming.items():
        if key not in out:
            out[key] = value
        elif isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = merge(out[key], value)
        elif isinstance(out[key], list) and isinstance(value, list):
            have = {_canon(v) for v in out[key]}
            out[key] = out[key] + [v for v in value if _canon(v) not in have]
    return out


def builtin_profiles() -> list[str]:
    files = resources.files("one_xops.profiles").iterdir()
    return sorted(f.name[:-5] for f in files if f.name.endswith(".json"))


def load_profile(name_or_path: str) -> dict:
    """A built-in profile name (aws, azure, itsm) or a path to your own JSON file."""
    path = Path(name_or_path)
    if path.suffix == ".json" and path.is_file():
        data = json.loads(path.read_text())
    elif name_or_path in builtin_profiles():
        data = json.loads(
            resources.files("one_xops.profiles").joinpath(f"{name_or_path}.json").read_text()
        )
    else:
        raise ValueError(
            f"unknown profile '{name_or_path}': use one of {', '.join(builtin_profiles())} "
            "or a path to a .json file with an 'mcpServers' object"
        )
    if not isinstance(data.get("mcpServers"), dict) or not data["mcpServers"]:
        raise ValueError(f"profile '{name_or_path}' has no 'mcpServers' object")
    return data


def read_json(path: Path) -> dict:
    if not path.exists() or not path.read_text().strip():
        return {}
    try:
        data = json.loads(path.read_text())
    except ValueError:
        data = None
    if not isinstance(data, dict):
        raise ValueError(  # noqa: TRY004 - the callers report ValueError as a plain message
            f"{path} is not a valid settings file (JSON object). "
            f"Fix it, or rename it and run again; nothing was changed"
        )
    return data


def dumps(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


def write(path: Path, text: str) -> None:
    """Write through a temp file, flushed to disk, then swap it in: never a half-written file.
    The same content writes nothing; a change keeps the previous file as <name>.bak."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        old = path.read_bytes()
        if old == text.encode():
            return
        bak = path.with_name(path.name + ".bak")
        bak.write_bytes(old)
        print(f"kept the previous file as {bak}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)
