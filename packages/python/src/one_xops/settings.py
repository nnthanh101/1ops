"""Settings and connector files for each scope. Pure functions; the CLI does the writing."""

from __future__ import annotations

import json
import os
import platform
from importlib import resources
from pathlib import Path

HOST = "claude"  # host CLI binary and config folder name (technical identifier)

SCOPES = ("org", "team", "local", "personal")

MARKETPLACES = {
    "1ops": {"source": {"source": "github", "repo": "nnthanh101/1xops"}},  # free edition
    "knowledge-work-plugins": {
        "source": {"source": "github", "repo": "anthropics/knowledge-work-plugins"}
    },
}

# Baseline every scope receives: the plugin, its base dependency, no secret reads,
# and a person's yes before anything leaves the machine, rewrites history or changes AWS or Azure
# (sessions sign in read-only; these rules ask, the read-only identity is the boundary).
BASELINE = {
    "extraKnownMarketplaces": MARKETPLACES,
    "enabledPlugins": {"1xops@1ops": True, "operations@knowledge-work-plugins": True},
    "permissions": {
        "deny": ["Read(./.env)", "Read(./.env.*)", "Read(./**/.env)", "Read(./**/.env.*)"],
        "ask": [
            "Bash(git push *)",
            "Bash(git reset --hard *)",
            "Bash(git tag *)",
            "Bash(gh pr merge *)",
            "Bash(gh release *)",
            "Bash(terraform apply *)",
            "Bash(terraform destroy *)",
            "Bash(aws * create-*)",
            "Bash(aws * delete-*)",
            "Bash(aws * put-*)",
            "Bash(aws * update-*)",
            "Bash(aws * modify-*)",
            "Bash(aws * terminate-*)",
            "Bash(aws * start-*)",
            "Bash(aws * stop-*)",
            "Bash(aws * attach-*)",
            "Bash(aws * detach-*)",
            "Bash(aws * tag-*)",
            "Bash(aws * untag-*)",
            "Bash(aws s3 cp *)",
            "Bash(aws s3 mv *)",
            "Bash(aws s3 rm *)",
            "Bash(aws s3 sync *)",
            "Bash(aws cloudformation deploy *)",
            "Bash(az * create*)",
            "Bash(az * delete*)",
            "Bash(az * update*)",
            "Bash(az * start*)",
            "Bash(az * stop*)",
            "Bash(az * restart*)",
            "Bash(az * deallocate*)",
            "Bash(az * assign*)",
            "Bash(az * add*)",
            "Bash(az * remove*)",
            "Bash(az * import*)",
            "Bash(az * invoke*)",
            "Bash(az rest *)",
        ],
    },
}


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
            out[key] = out[key] + [v for v in value if v not in out[key]]
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
    return json.loads(path.read_text())


def dumps(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


def write(path: Path, text: str) -> None:
    """Write through a temp file, flushed to disk, then swap it in: never a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)
