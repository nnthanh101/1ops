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
from rich.table import Table
from rich.text import Text

from one_xops import config_file as cf
from one_xops import settings as s

console = Console()
if (
    not console.is_terminal
):  # piped (the assistant, evidence): size to content, never wrap like a terminal
    console = Console(width=400)


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


def aws_config_file() -> Path:
    """The AWS config file the CLI reads: AWS_CONFIG_FILE, else ~/.aws/config."""
    return Path(os.environ.get("AWS_CONFIG_FILE") or Path.home() / ".aws" / "config")


def azure_subscriptions() -> list[tuple[str, str, str]]:
    """(name, subscription id, tenant id) of the subscriptions the read-only identity in AZURE_CONFIG_DIR can see.
    Read from its local sign-in, no cloud call. Without AZURE_CONFIG_DIR nothing is read: the default login is never used."""
    if not os.environ.get("AZURE_CONFIG_DIR"):
        return []
    raw = _out(
        ["az", "account", "list", "--query", "[].{n:name,s:id,t:tenantId}", "--output", "json"]
    )
    try:
        return [(a["n"], a["s"], a["t"]) for a in json.loads(raw)]
    except (ValueError, KeyError, TypeError):
        return []


def read_only_profiles() -> list[tuple[str, str, str]]:
    """(name, masked account, role) of AWS profiles whose configured role cannot change things.
    Read from the local AWS config only: no cloud call. Unknown and can-change profiles are left out."""
    from one_xops import cli  # imported here: cli imports this module

    cfg = aws_config_file()
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


SCOPE_HELP = {
    "org": "managed files for IT, every person in the organisation",
    "team": "a shared project or tenant folder",
    "local": "you, in this project only",
    "personal": "you, in every project",
}
_shown: set[str] = set()  # "list" or "none": said once per run, not once per variable


def _profile_table(rows: list[tuple[int, tuple[str, str, str]]], title: str) -> Table:
    table = Table(title=title, title_style="bold")
    for col, justify in (
        ("#", "right"),
        ("profile", "left"),
        ("account", "left"),
        ("role", "left"),
    ):
        table.add_column(col, justify=justify)
    for n, (name, acct, role) in rows:
        table.add_row(str(n), name, acct, role)
    return table


def ask_profile(var: str) -> str:
    """Pick a read-only AWS profile: by number, or type part of a name to filter. A typed name that is not in
    the read-only list cannot get in. The list is shown once; later questions refer to it."""
    options = read_only_profiles()
    if not options:
        if "none" not in _shown:
            console.print(
                f"  No read-only AWS profile in {aws_config_file()} yet.", highlight=False
            )
            console.print(
                "  Create one with: aws configure sso (a role such as ReadOnlyAccess).",
                highlight=False,
            )
            console.print(
                "  Profiles in another file? Run: AWS_CONFIG_FILE=<file> 1xops setup",
                highlight=False,
            )
            console.print(
                "  Until then 1xops doctor shows this connector as missing.", highlight=False
            )
            _shown.add("none")
        return ""
    numbered = list(enumerate(options, 1))
    if "list" not in _shown:
        console.print(_profile_table(numbered, f"Read-only AWS profiles ({len(options)})"))
        _shown.add("list")
    current = os.environ.get(var, "")
    default = next((str(n) for n, (name, _, _) in numbered if name == current), "")
    hint = f"Enter keeps {default}, - skips" if default else "Enter skips"
    while True:
        pick = Prompt.ask(
            f"  {var}: number or part of a name ({hint})", default=default, show_default=False
        )
        pick = pick.strip()
        if not pick or pick == "-":
            return ""
        if pick.isdigit():
            if 1 <= int(pick) <= len(options):
                return options[int(pick) - 1][0]
            console.print(f"  No profile number {pick}: pick 1 to {len(options)}.", highlight=False)
            continue
        matches = [
            (n, o)
            for n, o in numbered
            if pick.lower() in o[0].lower() or pick.lower() in o[2].lower()
        ]
        if len(matches) == 1:
            return matches[0][1][0]
        if matches:
            console.print(_profile_table(matches, f"Matching '{pick}' ({len(matches)})"))
        else:
            console.print(
                f"  No read-only profile matches '{pick}'.", markup=False, highlight=False
            )


_picked: dict[
    str, str
] = {}  # the tenant of the picked Azure subscription, so it is not asked again
DEFAULTS = {"AWS_REGION": "ap-southeast-2"}  # Sydney; a region is not a secret


def ask_subscription(found: dict) -> str:
    """Pick an Azure subscription of the Reader identity by number or part of a name; its tenant fills in by itself."""
    rows = azure_subscriptions()
    if not rows:
        if "azure-none" not in _shown:
            console.print(
                "  No Azure Reader sign-in found. Use a Reader identity in its own folder, never your own login:",
                highlight=False,
            )
            console.print(
                "    AZURE_CONFIG_DIR=~/.azure-reader az login   then run setup again. Or type the ID now.",
                highlight=False,
            )
            _shown.add("azure-none")
        default = os.environ.get("AZURE_SUBSCRIPTION_ID") or found.get("AZURE_SUBSCRIPTION_ID")
        return Prompt.ask(
            "  AZURE_SUBSCRIPTION_ID (blank to skip)",
            default=default or "",
            show_default=bool(default),
        )
    table = Table(
        title=f"Azure subscriptions of the Reader identity ({len(rows)})", title_style="bold"
    )
    for col in ("#", "name", "subscription", "tenant"):
        table.add_column(col, justify="right" if col == "#" else "left")
    for n, (name, sub, tenant) in enumerate(rows, 1):
        table.add_row(str(n), name, f"****{sub[-4:]}", f"****{tenant[-4:]}")
    console.print(table)
    current = os.environ.get("AZURE_SUBSCRIPTION_ID") or found.get("AZURE_SUBSCRIPTION_ID", "")
    default = next((str(n) for n, r in enumerate(rows, 1) if r[1] == current), "")
    hint = f"Enter keeps {default}, - skips" if default else "Enter skips"
    while True:
        pick = Prompt.ask(
            f"  AZURE_SUBSCRIPTION_ID: number or part of a name ({hint})",
            default=default,
            show_default=False,
        ).strip()
        if not pick or pick == "-":
            return ""
        chosen = rows[int(pick) - 1] if pick.isdigit() and 1 <= int(pick) <= len(rows) else None
        if chosen is None and not pick.isdigit():
            hits = [r for r in rows if pick.lower() in r[0].lower()]
            chosen = hits[0] if len(hits) == 1 else None
        if chosen:
            _picked["AZURE_TENANT_ID"] = chosen[2]
            return chosen[1]
        console.print(
            f"  No single subscription matches '{pick}': pick 1 to {len(rows)}.", highlight=False
        )


def ask_value(var: str, found: dict) -> str:
    if var.endswith("_PROFILE"):
        return ask_profile(var)
    if var == "AZURE_SUBSCRIPTION_ID":
        return ask_subscription(found)
    if var == "AZURE_TENANT_ID" and var in _picked:
        console.print("  AZURE_TENANT_ID: taken from the subscription.", highlight=False)
        return _picked[var]
    default = os.environ.get(var) or found.get(var) or DEFAULTS.get(var)
    label = f"  {var}" if default else f"  {var} (blank to skip)"
    return Prompt.ask(label, default=default or "", show_default=bool(default))


def _verify(label: str, check, login: list[str]) -> None:
    """Show whether a connector is ready; when it is signed out, offer the provider's own sign-in and check again."""
    from one_xops import cli

    def show(row: tuple[str, str, str]) -> None:
        console.print(
            f"  {'✓' if row[1] == 'ready' else '✗'} {label}: {cli.scrub(row[2])}",
            markup=False,
            highlight=False,
        )

    row = check()
    show(row)
    if (
        row[1] == "signed out"
        and shutil.which(login[0])
        and Confirm.ask(f"  Sign in now? ({' '.join(login)}; opens your browser)", default=True)
    ):
        subprocess.run(login, check=False)
        show(check())


def connect(connectors: dict[str, dict[str, str]]) -> None:
    """Sign in with each provider's own command, then check that access is read-only."""
    from one_xops import cli

    console.print("\nConnect: sign in, then check that access is read-only.", markup=False)
    for name, values in connectors.items():
        if name == "aws":
            for var in ("AWS_BILLING_PROFILE", "AWS_OPERATIONS_PROFILE"):
                profile = values.get(var)
                if profile:
                    _verify(
                        f"aws {var}",
                        lambda var=var, profile=profile: cli._aws_connector(var, {var: profile}),
                        ["aws", "sso", "login", "--profile", profile],
                    )
        elif name == "azure":
            if not os.environ.get("AZURE_CONFIG_DIR"):
                console.print(
                    "  azure: use a Reader identity in its own folder (AZURE_CONFIG_DIR), then run setup again.",
                    markup=False,
                )
            else:
                _verify(
                    "azure", lambda values=values: cli._azure_connector(values), ["az", "login"]
                )
        elif name == "itsm":
            console.print(
                "  itsm: sign in inside the assistant: start it in this folder, run /mcp and choose atlassian.",
                markup=False,
            )


def run(args: argparse.Namespace) -> int:
    from one_xops import cli  # imported here: cli imports this module

    path = Path(args.file)
    _shown.clear()
    _picked.clear()
    console.print("[bold]1xops setup[/] — non-secret values only; secrets stay in your sign-in.\n")
    scopes = Table(title="Who the settings are for", title_style="bold")
    scopes.add_column("scope")
    scopes.add_column("for")
    for name in s.SCOPES:
        scopes.add_row(name, SCOPE_HELP[name])
    console.print(scopes)
    scope = Prompt.ask("Scope", choices=list(s.SCOPES), default="team")
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
    console.print()
    console.print(Text(str(path), style="bold"))
    console.print(text, markup=False, highlight=False, soft_wrap=True)
    if path.exists() and not Confirm.ask(f"{path} exists. Replace it?", default=False):
        return 1
    if not Confirm.ask(f"Write {path}?", default=True):
        return 1
    s.write(path, text)
    cf.load(path)  # same checks as `1xops config --file`

    console.print("\nChanges this would make:")
    if cli.main(["config", "--file", str(path), "--preview", "summary"]) != 0:
        return 2
    if Confirm.ask("Show every line first?", default=False):
        cli.main(["config", "--file", str(path), "--preview", "full"])
    code = 0
    if Confirm.ask("Apply them now?", default=False):
        code = cli.main(["config", "--file", str(path), "--yes"])
    else:
        console.print(f"Apply later with: 1xops config --file {path} --yes")
    if (
        code == 0
        and connectors
        and Confirm.ask(
            "Connect and verify now? (signs in with each provider's own command)", default=True
        )
    ):
        connect(connectors)
    return code
