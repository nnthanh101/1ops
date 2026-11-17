"""`1xops setup`: a guided terminal setup that writes 1ops.yaml, then shows and applies the changes."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

from one_ops import config_file as cf
from one_ops import settings as s

console = Console()


def _out(cmd: list[str]) -> str:
    if not shutil.which(cmd[0]):
        return ""
    try:
        p = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return p.stdout.strip() if p.returncode == 0 else ""


def detect() -> dict[str, str | list[str]]:
    """Read-only lookups that make good defaults: AWS profiles and region, current Azure account."""
    found: dict[str, str | list[str]] = {}
    profiles = _out(["aws", "configure", "list-profiles"]).split()
    if profiles:
        found["aws_profiles"] = profiles
    region = os.environ.get("AWS_REGION") or _out(["aws", "configure", "get", "region"])
    if region:
        found["AWS_REGION"] = region
    account = _out(["az", "account", "show", "--query", "{t:tenantId,s:id}", "--output", "json"])
    if account:
        ids = json.loads(account)
        found["AZURE_TENANT_ID"], found["AZURE_SUBSCRIPTION_ID"] = ids["t"], ids["s"]
    return found


def ask_value(var: str, found: dict) -> str:
    default = os.environ.get(var) or found.get(var)
    if var.endswith("_PROFILE") and found.get("aws_profiles"):
        console.print(f"  AWS profiles on this machine: {', '.join(found['aws_profiles'])}")
    return Prompt.ask(f"  {var} (blank to skip)", default=default or "", show_default=bool(default))


def run(args: argparse.Namespace) -> int:
    from one_ops import cli  # imported here: cli imports this module

    path = Path(args.file)
    console.print("[bold]1xops setup[/] — non-secret values only; secrets stay in your sign-in.\n")
    scope = Prompt.ask(
        "Scope (org: managed files for IT · team: shared project or tenant folder · "
        "local: you, this project · personal: you, every project)",
        choices=list(s.SCOPES),
        default="team",
    )
    config: dict = {"scope": scope}
    if scope in ("team", "local"):
        config["dir"] = Prompt.ask("Project or tenant folder", default=".")
    if scope == "org":
        config["out"] = Prompt.ask("Folder to write the managed files to", default=".")

    found = detect()
    connectors: dict[str, dict[str, str]] = {}
    for name in s.builtin_profiles():
        profile = s.load_profile(name)
        if not Confirm.ask(f"Add {name}: {profile.get('description', '')}?", default=False):
            continue
        values = {v: ask_value(v, found) for v in cf.variables(profile)}
        connectors[name] = {k: v for k, v in values.items() if v}
    own = Prompt.ask("Your own profile .json file (blank to skip)", default="", show_default=False)
    if own:
        connectors[own] = {}
    config["connectors"] = connectors

    text = cf.dump(config)
    console.print(f"\n[bold]{path}[/]\n{text}", markup=False, highlight=False)
    if path.exists() and not Confirm.ask(f"{path} exists. Replace it?", default=False):
        return 1
    if not Confirm.ask(f"Write {path}?", default=True):
        return 1
    path.write_text(text)
    cf.load(path)  # same checks as `1xops config --file`

    console.print("\nChanges this would make:")
    if cli.main(["config", "--file", str(path)]) != 0:
        return 2
    if Confirm.ask("Apply them now?", default=False):
        return cli.main(["config", "--file", str(path), "--yes"])
    console.print(f"Apply later with: 1xops config --file {path} --yes")
    return 0
