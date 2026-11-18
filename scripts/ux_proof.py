"""ux_proof.py OUT - before a release, see 1xops as a first-time customer does, and fail on what tests cannot see.

Installs the local build the customer's way (uv tool install, npm install -g) in clean containers, as a non-root user
with no cloud account, so no private name can reach a screenshot. Drives every command in a real terminal (a pty):
the setup wizard from scratch then the check, doctor, connectors and a config preview. For each: the exit code, the
seconds, and these checks: output printed; no literal [markup]; no table row wrapped; nothing wider than the terminal;
piped output has no colour codes and is byte-identical between Python and Node.js. Writes OUT/report.md and one SVG
screenshot per run (rendered by rich from the captured bytes). Exit 0 only when every check passes.
Used by `task ux` (tests/Taskfile.yml); `task release` runs it before anything is pushed.
"""

from __future__ import annotations

import fcntl
import os
import pty
import struct
import termios
import re
import select
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.text import Text

WIDTH = 110
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
MARKUP = re.compile(r"\[/?(bold|dim|red|green|yellow|italic)\b[^\]]*\]")
TAG = os.environ.get("UX_TAG", "local")  # one image pair per folder (tests/Taskfile.yml)
IMAGES = {"PyPI": f"1xops-ux:py-{TAG}", "npm": f"1xops-ux:js-{TAG}"}
# Answers a first-time customer gives: a team folder, AWS and Jira, no own profile, write the file, don't apply.
WIZARD = [
    ("Scope", "team"), ("Tenant folder", "."), ("Add aws", "y"), ("AWS_REGION", "ap-southeast-2"),
    ("Add azure", "n"), ("Add itsm", "y"), ("Your own profile", ""), ("Write", "y"), ("Show every line", "n"),
    ("Apply them now", "n"), ("Connect and verify", "n"),
]
# A tenant folder with one connector that is not set up, so the session-start check has something to name.
TENANT = "printf 'ONEXOPS_SCOPE=team\\nONEXOPS_CONNECTORS=aws\\n' > .env.1xops && "
RUNS = [  # name, shell command in the container, answers, expected exit codes
    ("doctor-first-run", "1xops doctor", [], {0, 1}),
    ("setup-then-check", "1xops setup && 1xops doctor", WIZARD, {0, 1}),
    ("doctor-brief", TENANT + "1xops doctor --brief", [], {0}),
    ("connectors", "1xops connectors", [], {0}),
    ("config-preview", "1xops config --scope team --dir . --connectors aws itsm", [], {0}),
    # A hand edit drops a rule; config repairs it and keeps the edited file as .bak; a second run changes nothing.
    ("config-keeps-bak", "1xops config --scope team --dir . --yes >/dev/null && sed -i 's|config/gh|config/gx|' "
     ".claude/settings.json && 1xops config --scope team --dir . --yes && 1xops config --scope team --dir . --yes "
     "&& ls -a .claude", [], {0}),
]
# What `1xops config` writes for each scope must equal the committed template, byte for byte.
WRITES = {"team": "1xops config --scope team --dir . --yes >/dev/null && cat .claude/settings.json",
          "local": "1xops config --scope local --dir . --yes >/dev/null && cat .claude/settings.local.json",
          "org": "1xops config --scope org --out o --yes >/dev/null && cat o/managed-settings.json",
          "personal": "1xops config --scope personal --yes >/dev/null && cat ~/.claude/settings.json"}
PIPED = ["1xops doctor", TENANT + "1xops doctor --brief", TENANT + "1xops doctor --hook --within 4", "1xops connectors", "1xops config --scope team --dir . --connectors aws itsm"]


def docker(image: str, cmd: str, tty: bool, name: str = "") -> list[str]:
    """-i -t: a real terminal whose keyboard reaches the container, so the typed answers arrive."""
    return ["docker", "run", "--rm", *(["--name", name] if name else []), *(["-i", "-t"] if tty else []),
            "-e", f"COLUMNS={WIDTH}", "-e", "TERM=xterm-256color", image, "sh", "-c", cmd]


def drive(argv: list[str], answers: list[tuple[str, str]], name: str) -> tuple[int | str, bytes, float]:
    """Run argv in a pty; type each answer once its prompt appears, as a person would. Returns code, bytes, seconds.
    Stuck for 120 s (a prompt that never came, or one nobody answered): the container is stopped, the code says where."""
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)  # left by an interrupted run
    start, buf, pos, i = time.time(), b"", 0, 0
    pid, fd = pty.fork()
    if pid == 0:  # a real terminal tells programs its size; Node reads it from here, rich from COLUMNS
        fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", 50, WIDTH, 0, 0))
        os.environ["DOCKER_CLI_HINTS"] = "false"  # docker's own "What's next" tip is not 1xops output
        os.execvp(argv[0], argv)
    while time.time() - start < 120:
        ready, _, _ = select.select([fd], [], [], 0.2)
        if ready:
            try:
                chunk = os.read(fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
        if i < len(answers) and answers[i][0].encode() in buf[pos:]:
            time.sleep(0.2)
            os.write(fd, (answers[i][1] + "\n").encode())
            i, pos = i + 1, len(buf)
    stuck = time.time() - start >= 120  # the loop ran out of time; otherwise the program closed its terminal
    done, status = os.waitpid(pid, os.WNOHANG) if stuck else os.waitpid(pid, 0)
    if stuck and not done:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
        os.waitpid(pid, 0)
        last = ANSI.sub("", buf.decode("utf-8", "replace")).strip().splitlines()[-1:] or ["nothing"]
        return f"stuck at: {last[0][:60]!r}", buf, time.time() - start
    return os.waitstatus_to_exitcode(status), buf, time.time() - start


def screen(raw: bytes) -> str:
    """What stays on screen, as a terminal shows it: each line keeps what follows its last carriage return
    (spinner frames overwrite each other), and a cursor-up (ESC[nA) erases the n lines above (rich's spinner end)."""
    shown: list[str] = []
    for line in raw.decode("utf-8", "replace").replace("\r\n", "\n").split("\n"):
        for up in re.findall(r"\x1b\[(\d*)A", line):
            del shown[len(shown) - min(int(up or 1), len(shown)) :]
        shown.append(re.sub(r"\x1b\[(\d*A|2K|K|\?25[hl])", "", line).split("\r")[-1])
    return "\n".join(shown)


def checks(shown: str) -> list[str]:
    plain = ANSI.sub("", shown)
    problems = []
    if not plain.strip():
        problems.append("printed nothing")
    if m := MARKUP.search(plain):
        problems.append(f"literal markup {m.group(0)!r}")
    if any(line.startswith(("│", "┃")) and not line.rstrip().endswith(("│", "┃")) for line in plain.splitlines()):
        problems.append("a table row broke out of its borders")
    if wide := [line for line in plain.splitlines() if len(line) > WIDTH]:
        problems.append(f"{len(wide)} line(s) wider than {WIDTH} columns")
    return problems


def svg(shown: str, path: Path, title: str) -> None:
    console = Console(record=True, width=WIDTH, force_terminal=True, color_system="truecolor", file=open(os.devnull, "w"))
    console.print(Text.from_ansi(shown.rstrip() + "\n"))
    console.save_svg(str(path), title=title)


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    rows, failures = [], 0
    for channel, image in IMAGES.items():
        for name, cmd, answers, ok_codes in RUNS:
            container = f"1xops-ux-{TAG}-{channel.lower()}-{name}"
            code, raw, secs = drive(docker(image, cmd, tty=True, name=container), answers, container)
            shown = screen(raw)
            problems = checks(shown) + ([] if code in ok_codes else [f"exit {code}"])
            shot = out / f"{channel.lower()}-{name}.svg"
            svg(f"$ {cmd}\n{shown}", shot, f"{channel}: {cmd}")
            failures += bool(problems)
            rows.append(f"| {channel} | `{cmd}` | {code} | {secs:.1f} | {'; '.join(problems) or 'pass'} | {shot.name} |")
    piped = {}
    for channel, image in IMAGES.items():
        for cmd in PIPED:
            p = subprocess.run(docker(image, cmd, tty=False), capture_output=True, check=False)
            piped[(channel, cmd)] = p.stdout
    for cmd in PIPED:
        py, js = piped[("PyPI", cmd)], piped[("npm", cmd)]
        problems = [f"{c} printed nothing" for c, b in (("PyPI", py), ("npm", js)) if not b.strip()]
        problems += [f"{c} has colour codes" for c, b in (("PyPI", py), ("npm", js)) if b"\x1b[" in b]
        if cmd == "1xops doctor":  # tool rows differ by container (uv vs npx), so compare the connector rows
            py, js = (re.sub(rb" +", b" ", b"\n".join(x for x in b.splitlines() if b" connector " in x)) for b in (py, js))
            problems += [] if py and py == js else ["connector rows differ or are empty"]
        else:
            problems += [] if py == js else ["PyPI and npm differ"]
        if cmd == "1xops connectors" and re.search(rb"^\xe2\x94\x82 +\xe2\x94\x82", py, re.M):
            problems.append("piped table wrapped a row")
        failures += bool(problems)
        rows.append(f"| both, piped | `{cmd}` | | | {'; '.join(problems) or ('pass: same connector rows' if cmd == '1xops doctor' else 'pass: byte-identical') + ', no colour codes'} | |")
    for channel, image in IMAGES.items():
        for scope, cmd in WRITES.items():
            p = subprocess.run(docker(image, cmd, tty=False), capture_output=True, check=False)
            same = p.stdout == Path(f"templates/settings/{scope}.json").read_bytes()
            failures += not same
            rows.append(f"| {channel}, piped | `{cmd}` | {p.returncode} | | {'pass: equals the template' if same else 'differs from the template'} | |")
    report = [
        f"**1xops UX proof, {time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime())}**: local build installed the customer's way "
        f"in clean containers, non-root, no cloud account; a {WIDTH}-column terminal.",
        "",
        "| Channel | Command | Exit | Seconds | Checks | Screenshot |",
        "|---|---|---|---|---|---|",
        *rows,
        "",
        "All checks pass." if not failures else f"{failures} run(s) failed.",
    ]
    (out / "report.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "tmp/ux")))
