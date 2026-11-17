"""`1xops setup`: a guided terminal setup that writes .env.1xops, then shows and applies the changes."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

from one_xops import config_file as cf
from one_xops import settings as s

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
    # Azure IDs are read only from a separate read-only identity (AZURE_CONFIG_DIR), never the default login.
    if os.environ.get("AZURE_CONFIG_DIR"):
        account = _out(
            ["az", "account", "show", "--query", "{t:tenantId,s:id}", "--output", "json"]
        )
        if account:
            ids = json.loads(account)
            found["AZURE_TENANT_ID"], found["AZURE_SUBSCRIPTION_ID"] = ids["t"], ids["s"]
    return found


def read_only_profiles() -> list[tuple[str, str, str]]:
    """(name, masked account, role) of AWS profiles whose configured role cannot change things.
    Read from the local AWS config only: no cloud call. Unknown and can-change profiles are left out."""
    from one_xops import cli  # imported here: cli imports this module

    cfg = Path(os.environ.get("AWS_CONFIG_FILE") or Path.home() / ".aws" / "config")
    if not cfg.is_file():
        return []
    found: list[tuple[str, str, str]] = []
    name, kv = "", {}

    def flush() -> None:
        role = kv.get("sso_role_name") or (kv.get("role_arn", "").split("/")[-1])
        if name and role and cli.access_from_role(f":assumed-role/{role}/") == "read":
            acct = (
                kv.get("sso_account_id")
                or kv.get("role_arn", "").split(":")[4:5]
                and kv["role_arn"].split(":")[4]
            )
            found.append((name, f"****{acct[-4:]}" if acct else "-", role))

    for raw in cfg.read_text().splitlines():
        line = raw.strip()
        m = re.match(r"\[(?:profile\s+)?([^\]]+)\]", line)
        if m:
            flush()
            name, kv = m.group(1).strip(), {}
        elif "=" in line and not line.startswith(("#", ";")):
            k, v = line.split("=", 1)
            kv[k.strip()] = v.strip()
    flush()
    return sorted(found, key=lambda x: (x[1], x[0]))


def ask_profile(var: str) -> str:
    """Pick a read-only AWS profile by number. No typing: a mistyped or admin profile cannot get in."""
    options = read_only_profiles()
    if not options:
        console.print(
            f"  {var}: no read-only AWS profile found in ~/.aws/config. Create one (an SSO role such as ReadOnlyAccess) "
            "with: aws configure sso. This connector will show as missing in /1xops:check until then."
        )
        return ""
    console.print(f"  {var}: read-only profiles only")
    for i, (name, acct, role) in enumerate(options, 1):
        console.print(f"    {i}) {name}  {acct}  {role}", markup=False, highlight=False)
    pick = Prompt.ask(
        "  Number (Enter to skip)",
        choices=[str(i) for i in range(1, len(options) + 1)] + [""],
        default="",
        show_default=False,
        show_choices=False,
    )
    return options[int(pick) - 1][0] if pick else ""


def ask_value(var: str, found: dict) -> str:
    if var.endswith("_PROFILE"):
        return ask_profile(var)
    default = os.environ.get(var) or found.get(var)
    return Prompt.ask(f"  {var} (blank to skip)", default=default or "", show_default=bool(default))


def run(args: argparse.Namespace) -> int:
    from one_xops import cli  # imported here: cli imports this module

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
    s.write(path, text)
    cf.load(path)  # same checks as `1xops config --file`

    console.print("\nChanges this would make:")
    if cli.main(["config", "--file", str(path)]) != 0:
        return 2
    if Confirm.ask("Apply them now?", default=False):
        return cli.main(["config", "--file", str(path), "--yes"])
    console.print(f"Apply later with: 1xops config --file {path} --yes")
    return 0
