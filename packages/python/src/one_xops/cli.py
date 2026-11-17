"""1xops command line: doctor, install, config, profiles.

Nothing is changed unless you pass --yes; without it each command shows what it would do.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from one_xops import __version__
from one_xops import config_file as cf
from one_xops import settings as s
from one_xops import setup as wizard

console = Console()

INSTALL_STEPS = [
    [s.HOST, "plugin", "marketplace", "add", "anthropics/knowledge-work-plugins"],
    [s.HOST, "plugin", "marketplace", "add", "nnthanh101/1xops"],
    [s.HOST, "plugin", "install", "1xops@1xops"],
]


def _run(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return p.returncode, (p.stdout or p.stderr).strip()


def _mask(account: str) -> str:
    return f"****{account[-4:]}" if len(account) >= 4 else "****"


def scrub(text: str) -> str:
    """Any 12-digit run (an AWS account ID), masked: doctor output is pasted onto issues as evidence."""
    return re.sub(r"\d{12}", lambda m: _mask(m.group(0)), str(text))


def access_from_role(arn: str = "") -> str:
    """read: the role cannot change anything; write: it can; unknown: cannot tell from the name."""
    m = re.search(r":assumed-role/([^/]+)/", arn) or re.search(r":(user|root)\b", arn)
    role = m.group(1) if m else ""
    if re.search(r"readonly|viewonly|securityaudit|readaccess|viewer", role, re.IGNORECASE):
        return "read"
    if re.search(r"admin|poweruser|fullaccess|root", role, re.IGNORECASE):
        return "write"
    return "unknown"


ACCESS = {
    "read": "read-only",
    "write": "can change things: use a read-only role",
    "unknown": "access unknown: use a read-only role",
}


# ── doctor ──────────────────────────────────────────────────────────────────


def check_tools() -> list[tuple[str, bool, bool, str]]:
    """(name, required, ok, detail) for each prerequisite. Read-only."""
    rows = []
    for name, required in [
        ("git", True),
        (s.HOST, True),
        ("uv", False),
        ("npx", False),
        ("docker", False),
        ("gh", False),
        ("aws", False),
        ("az", False),
    ]:
        path = shutil.which(name)
        if not path:
            rows.append((name, required, False, "not found on PATH"))
            continue
        code, out = _run([name, "--version"])
        rows.append((name, required, code == 0, out.splitlines()[0] if out else path))
    return rows


def check_sign_in(aws_profile: str | None) -> list[tuple[str, bool, bool, str]]:
    """Read-only sign-in checks. Account IDs are masked, never printed in full."""
    rows = []
    if shutil.which("aws"):
        cmd = ["aws", "sts", "get-caller-identity", "--output", "json"]
        if aws_profile:
            cmd += ["--profile", aws_profile]
        code, out = _run(cmd)
        if code == 0:
            ident = json.loads(out)
            access = access_from_role(ident.get("Arn", ""))
            rows.append(
                (
                    "aws sign-in",
                    False,
                    True,
                    f"signed in, account {_mask(ident.get('Account', ''))}",
                )
            )
            rows.append(("aws access", False, access == "read", ACCESS[access]))
        else:
            rows.append(("aws sign-in", False, False, "not signed in (aws sso login)"))
    if shutil.which("az"):
        code, _ = _run(["az", "account", "show", "--output", "none"])
        rows.append(
            (
                "azure sign-in",
                False,
                code == 0,
                "signed in" if code == 0 else "not signed in (az login)",
            )
        )
    if shutil.which("gh"):
        code, _ = _run(["gh", "auth", "status"])
        rows.append(
            (
                "github sign-in",
                False,
                code == 0,
                "signed in" if code == 0 else "not signed in (gh auth login)",
            )
        )
    return rows


def aws_fix(error: str, profile: str) -> tuple[str, str]:
    """(status, fix) for a failed AWS identity call, from the AWS CLI's own error text."""
    if re.search(r"could not be found", error, re.IGNORECASE):
        return (
            "missing",
            f"profile {profile} not found: aws configure sso --profile {profile}, or set AWS_CONFIG_FILE",
        )
    if re.search(
        r"expired|refresh failed|sso.*token|nocredentials|unable to locate credentials",
        error,
        re.IGNORECASE,
    ):
        return "signed out", f"aws sso login --profile {profile}"
    first = next((line for line in error.splitlines() if line.strip()), "AWS identity call failed")
    return "check", first.removeprefix("aws: [ERROR]: ")[:120]


def azure_access(roles: list[str]) -> str:
    """read: Reader roles only; write: any role that can change things; unknown: no roles seen."""
    if not roles:
        return "unknown"
    if any(re.search(r"owner|contributor|administrator", r, re.IGNORECASE) for r in roles):
        return "write"
    if all(re.search(r"reader", r, re.IGNORECASE) for r in roles):
        return "read"
    return "unknown"


AZURE_ACCESS = {
    "read": "read-only",
    "write": "can change things: use a read-only (Reader) identity",
    "unknown": "access unknown: use a read-only (Reader) identity",
}


def _aws_connector(var: str, values: dict[str, str]) -> tuple[str, str, str]:
    name = f"aws {var}"
    profile = values.get(var) or os.environ.get(var, "")
    if not profile:
        return name, "missing", f"set {var} in .env.1xops or the shell (1xops setup)"
    if not shutil.which("aws"):
        return name, "missing", "install the AWS CLI"
    code, out = _run(
        ["aws", "sts", "get-caller-identity", "--output", "json", "--profile", profile]
    )
    if code != 0:
        status, fix = aws_fix(out, profile)
        return name, status, fix
    try:
        ident = json.loads(out)
    except ValueError:
        return name, "check", "AWS identity call returned no account"
    access = access_from_role(ident.get("Arn", ""))
    detail = f"profile {profile}, account {_mask(ident.get('Account', ''))}, {ACCESS[access]}"
    return name, "ready" if access == "read" else "check", detail


def _azure_connector() -> tuple[str, str, str]:
    if not shutil.which("az"):
        return "azure", "missing", "install the Azure CLI"
    fix = "az login with a read-only (Reader) identity, in its own AZURE_CONFIG_DIR"
    code, out = _run(["az", "account", "show", "--query", "user.name", "--output", "tsv"])
    if code != 0 or not out:
        return "azure", "signed out", fix
    code, roles = _run(
        [
            "az",
            "role",
            "assignment",
            "list",
            "--assignee",
            out,
            "--all",
            "--query",
            "[].roleDefinitionName",
            "--output",
            "json",
        ],
        timeout=60,
    )
    try:
        names = json.loads(roles) if code == 0 else []
    except ValueError:
        names = []
    access = azure_access(names)
    return "azure", "ready" if access == "read" else "check", AZURE_ACCESS[access]


def check_connectors(file: str) -> list[tuple[str, str, str]]:
    """(connector, status, fix) for each connector in .env.1xops. Read-only identity calls only."""
    path = Path(file)
    if not path.is_file():
        return [("connectors", "missing", f"no {file} here: run 1xops setup")]
    try:
        cfg = cf.load(path)
    except (ValueError, OSError) as exc:
        return [("connectors", "missing", str(exc))]
    if not cfg["connectors"]:
        return [
            ("connectors", "missing", f"ONEXOPS_CONNECTORS is empty in {file}: run 1xops setup")
        ]
    rows = []
    for connector in cfg["connectors"]:
        try:
            servers = s.load_profile(connector)["mcpServers"]
        except (ValueError, OSError) as exc:
            rows.append((connector, "missing", str(exc)))
            continue
        aws_vars, azure = [], False
        for server_name, server in servers.items():
            env = server.get("env", {})
            if "AWS_PROFILE" in env:
                aws_vars += cf.VAR.findall(env["AWS_PROFILE"])
            elif "AZURE_TENANT_ID" in env:
                azure = True
            elif server.get("type") == "http":
                rows.append(
                    (
                        server_name,
                        "check",
                        f"signs in inside the host: run /mcp and choose {server_name}",
                    )
                )
            else:
                rows.append((server_name, "check", "no sign-in check for this connector"))
        rows += [_aws_connector(v, cfg["values"]) for v in dict.fromkeys(aws_vars)]
        if azure:
            rows.append(_azure_connector())
    return rows


RESULT_STYLE = {
    "ok": "green",
    "ready": "green",
    "missing": "red",
    "signed out": "yellow",
    "check": "yellow",
}


def cmd_doctor(args: argparse.Namespace) -> int:
    # The identity calls take seconds; a spinner on a terminal, nothing when piped.
    with console.status("Checking tools, sign-ins and connectors (read-only)…"):
        rows = check_tools() + check_sign_in(args.aws_profile)
        connectors = check_connectors(args.file)
    shown = [
        (
            name,
            "required" if required else "optional",
            "ok" if ok else ("missing" if required else "check"),
            detail,
        )
        for name, required, ok, detail in rows
    ]
    shown += [(name, "connector", status, fix) for name, status, fix in connectors]
    table = Table(title=f"1xops {__version__} doctor", title_style="bold")
    for col in ("check", "needed", "result", "detail"):
        table.add_column(col, overflow="fold")
    for name, needed, result, detail in shown:
        style = RESULT_STYLE[result]
        table.add_row(name, needed, Text(result, style=style), Text(scrub(detail)))
    console.print(table)
    failed = [r[0] for r in rows if r[1] and not r[2]]
    if failed:
        console.print(Text(f"Required: {', '.join(failed)}", style="red"))
        return 1
    return 0


# ── install ─────────────────────────────────────────────────────────────────


def cmd_install(args: argparse.Namespace) -> int:
    if not shutil.which(s.HOST):
        console.print(f"[red]'{s.HOST}' CLI not found; run '1xops doctor'.[/]")
        return 1
    for step in INSTALL_STEPS:
        step = [*step, "--scope", args.scope]
        console.print(f"[bold]$ {' '.join(step)}[/]")
        if not args.yes:
            continue
        code, out = _run(step, timeout=180)
        console.print(out)
        if code != 0:
            return code
    if not args.yes:
        console.print("Dry run. Re-run with --yes to install.")
    return 0


# ── config ──────────────────────────────────────────────────────────────────


def _show_change(path: Path, before: dict, after: dict) -> bool:
    if before == after:
        console.print(f"[dim]{path}: already up to date[/]")
        return False
    diff = difflib.unified_diff(
        s.dumps(before).splitlines(),
        s.dumps(after).splitlines(),
        fromfile=str(path),
        tofile=str(path),
        lineterm="",
    )
    console.print("\n".join(diff), markup=False, highlight=False)
    return True


def _write(path: Path, data: dict) -> None:
    s.write(path, s.dumps(data))


def _resolve(args: argparse.Namespace) -> tuple[str, Path, Path | None, dict[str, dict]]:
    """Scope, folder, org output and {connector: values}, from .env.1xops or the flags."""
    if args.file:
        cfg = cf.load(Path(args.file))
        out = Path(cfg["out"]).resolve() if cfg["out"] else None
        return cfg["scope"], Path(cfg["dir"]).resolve(), out, cfg["connectors"]
    out = Path(args.out).resolve() if args.out else None
    return args.scope, Path(args.dir).resolve(), out, {c: {} for c in args.connectors}


def cmd_config(args: argparse.Namespace) -> int:
    try:
        scope, project, out, connectors = _resolve(args)
        profiles = [(s.load_profile(name), values) for name, values in connectors.items()]
    except (ValueError, OSError) as exc:
        console.print(f"[red]{exc}[/]")
        return 2
    personal = scope in ("local", "personal")
    servers: dict = {}
    wanted = s.BASELINE
    for profile, values in profiles:
        # Shared files keep ${VAR}; private host config gets the person's values.
        servers.update(
            cf.substitute(profile["mcpServers"], values) if personal else profile["mcpServers"]
        )
        wanted = s.merge(wanted, {"permissions": profile.get("permissions", {})})

    planned: list[tuple[Path, dict]] = []
    target = s.settings_path(scope, project, out)
    before = s.read_json(target)
    after = s.merge(before, wanted)
    if _show_change(target, before, after):
        planned.append((target, after))

    host_cmds: list[list[str]] = []
    if servers:
        mcp_file = s.mcp_path(scope, project, out)
        if mcp_file:
            before = s.read_json(mcp_file)
            after = s.merge(before, {"mcpServers": servers})
            if _show_change(mcp_file, before, after):
                planned.append((mcp_file, after))
        else:
            host_scope = "user" if scope == "personal" else "local"
            for name, spec in servers.items():
                host_cmds.append(
                    [s.HOST, "mcp", "add-json", "-s", host_scope, name, json.dumps(spec)]
                )
                console.print(f"[bold]$ {s.HOST} mcp add-json -s {host_scope} {name} '…'[/]")

    if not args.yes:
        console.print("Dry run. Re-run with --yes to write these changes.")
        return 0
    if host_cmds and not shutil.which(s.HOST):
        console.print(
            f"[red]{scope} scope adds connectors through the '{s.HOST}' CLI, which is not installed. "
            "Nothing was written. Install it, or use --scope team.[/]"
        )
        return 1
    for path, data in planned:
        _write(path, data)
        console.print(f"[green]wrote {path}[/]")
    for cmd in host_cmds:
        code, msg = _run(cmd)
        console.print(msg)
        if code != 0:
            return code
    if scope == "org":
        console.print(f"Give these files to IT to install in: {s.managed_dir()}")
    if not personal and any(values for _, values in profiles):
        console.print('Shared files use ${VAR}. Load your values with: eval "$(1xops env)"')
    return 0


def cmd_env(args: argparse.Namespace) -> int:
    """Print `export VAR=value` lines from .env.1xops, for team and org scopes."""
    try:
        cfg = cf.load(Path(args.file))
    except (ValueError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2
    for key, value in cfg["values"].items():
        print(f"export {key}={shlex.quote(value)}")
    return 0


def cmd_profiles(_: argparse.Namespace) -> int:
    table = Table(title="Connector profiles")
    for col in ("profile", "servers", "values (.env.1xops keys)", "description"):
        table.add_column(col)
    for name in s.builtin_profiles():
        p = s.load_profile(name)
        table.add_row(
            name,
            ", ".join(p["mcpServers"]),
            ", ".join(cf.variables(p)) or "—",
            p.get("description", ""),
        )
    console.print(table)
    console.print("Use your own: a .json file with an 'mcpServers' object, as a connector name.")
    return 0


# ── entry point ─────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="1xops", description="1xops by OceanSoft.io")
    parser.add_argument("--version", action="version", version=f"1xops {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="check prerequisites, sign-in and connectors")
    p.add_argument("--aws-profile", help="AWS profile to check (default: current)")
    p.add_argument(
        "--file", default=cf.DEFAULT_FILE, help="connectors to check (default: .env.1xops)"
    )
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("install", help="add the marketplaces and install the plugin")
    p.add_argument(
        "--scope",
        choices=("user", "project", "local"),
        default="user",
        help="host install scope: user (default), project (shared), local",
    )
    p.add_argument("--yes", action="store_true", help="run the commands (default: show them)")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("config", help="write settings and connectors for a scope")
    p.add_argument(
        "--scope",
        choices=s.SCOPES,
        default="team",
        help="org: managed files for IT · team: shared project settings (use --dir "
        "for a tenant folder) · local: you, this project · personal: you, every project",
    )
    p.add_argument("--dir", default=".", help="project or tenant folder (team/local scopes)")
    p.add_argument("--out", help="output folder for org scope (default: current folder)")
    p.add_argument(
        "--connectors",
        nargs="*",
        default=[],
        metavar="PROFILE",
        help="built-in profile names (see '1xops profiles') or .json files",
    )
    p.add_argument("--file", help="read scope, folder and connector values from .env.1xops")
    p.add_argument("--yes", action="store_true", help="write the changes (default: show a diff)")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("env", help="print export lines for the values in .env.1xops")
    p.add_argument("--file", default=cf.DEFAULT_FILE)
    p.set_defaults(func=cmd_env)

    p = sub.add_parser("setup", help="guided setup: asks questions, writes .env.1xops")
    p.add_argument("--file", default=cf.DEFAULT_FILE)
    p.set_defaults(func=wizard.run)

    p = sub.add_parser("profiles", help="list built-in connector profiles")
    p.set_defaults(func=cmd_profiles)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
