"""1xops command line: doctor, install, config, profiles.

Nothing is changed unless you pass --yes; without it each command shows what it would do.
"""

from __future__ import annotations

import argparse
import difflib
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

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
            account = json.loads(out).get("Account", "")
            rows.append(("aws sign-in", False, True, f"signed in, account {_mask(account)}"))
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


def cmd_doctor(args: argparse.Namespace) -> int:
    rows = check_tools() + check_sign_in(args.aws_profile)
    table = Table(title=f"1xops {__version__} doctor")
    for col in ("check", "needed", "result", "detail"):
        table.add_column(col)
    for name, required, ok, detail in rows:
        result = (
            "[green]ok[/]" if ok else ("[red]missing[/]" if required else "[yellow]optional[/]")
        )
        table.add_row(name, "required" if required else "optional", result, detail)
    console.print(table)
    failed = [r[0] for r in rows if r[1] and not r[2]]
    if failed:
        console.print(f"[red]Required: {', '.join(failed)}[/]")
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
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(s.dumps(data))
    tmp.replace(path)


def _resolve(args: argparse.Namespace) -> tuple[str, Path, Path | None, dict[str, dict]]:
    """Scope, folder, org output and {connector: values}, from 1xops.yaml or the flags."""
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
    except (ValueError, TypeError, OSError, yaml.YAMLError) as exc:
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
    """Print `export VAR=value` lines from 1xops.yaml, for team and org scopes."""
    try:
        cfg = cf.load(Path(args.file))
    except (ValueError, TypeError, OSError, yaml.YAMLError) as exc:
        print(exc, file=sys.stderr)
        return 2
    for values in cfg["connectors"].values():
        for key, value in values.items():
            print(f"export {key}={shlex.quote(value)}")
    return 0


def cmd_profiles(_: argparse.Namespace) -> int:
    table = Table(title="Connector profiles")
    for col in ("profile", "servers", "values (1xops.yaml keys)", "description"):
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

    p = sub.add_parser("doctor", help="check prerequisites and read-only sign-in")
    p.add_argument("--aws-profile", help="AWS profile to check (default: current)")
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
    p.add_argument("--file", help="read scope, folder and connector values from 1xops.yaml")
    p.add_argument("--yes", action="store_true", help="write the changes (default: show a diff)")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("env", help="print export lines for the values in 1xops.yaml")
    p.add_argument("--file", default="1xops.yaml")
    p.set_defaults(func=cmd_env)

    p = sub.add_parser("setup", help="guided setup: asks questions, writes 1xops.yaml")
    p.add_argument("--file", default="1xops.yaml")
    p.set_defaults(func=wizard.run)

    p = sub.add_parser("profiles", help="list built-in connector profiles")
    p.set_defaults(func=cmd_profiles)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
