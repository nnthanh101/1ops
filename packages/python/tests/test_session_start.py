"""TEST-009 (#37) for story 1XOPS-009 (#38): the session-start check (`doctor --hook --within`) names each broken
connector with its fix, says nothing when all is ready, and is never held up by a check that hangs or fails.
Fake `aws`/`az` programs stand in for the real tools; the release proof uses the published artifacts."""

import json
import time
from pathlib import Path

import pytest

from one_xops import cli

AWS_FILE = "ONEXOPS_CONNECTORS=aws\nAWS_BILLING_PROFILE=readonly\nAWS_OPERATIONS_PROFILE=readonly\n"
AWS_SHIM = """#!/bin/sh
case "$FAKE_AWS" in
  ready) echo '{"Account":"123456789012","Arn":"arn:aws:sts::123456789012:assumed-role/ReadOnlyAccess/me"}' ;;
  expired) echo "The SSO session associated with this profile has expired" >&2; exit 255 ;;
  hang) sleep 30 ;;
esac
"""


@pytest.fixture
def start(tmp_path: Path, monkeypatch, capsys):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "aws").write_text(AWS_SHIM)
    (bin_dir / "aws").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    for var in ("AWS_BILLING_PROFILE", "AWS_OPERATIONS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "host"))  # no plugins of this machine
    monkeypatch.chdir(tmp_path)

    def run(mode: str, settings: str | None = AWS_FILE, within: str = "4", hook: bool = True):
        monkeypatch.setenv("FAKE_AWS", mode)
        file = tmp_path / ".env.1xops"
        if settings is not None:
            file.write_text(settings)
        args = ["doctor", "--hook" if hook else "--brief", "--within", within, "--file", str(file)]
        code = cli.main(args)
        return code, capsys.readouterr().out

    return run


def test_a_signed_out_connector_is_named_with_its_fix_in_the_host_format(start):
    code, out = start("expired")
    assert code == 0
    message = json.loads(out)
    text = message["systemMessage"]
    assert "aws sso login --profile readonly" in text
    assert message["hookSpecificOutput"] == {
        "hookEventName": "SessionStart",
        "additionalContext": text,
    }
    assert "123456789012" not in out


def test_nothing_is_shown_when_every_connector_is_ready(start):
    assert start("ready") == (0, "")


def test_nothing_is_shown_without_a_settings_file(start):
    assert start("expired", settings=None) == (0, "")


def test_a_hung_check_ends_within_the_time_given_with_one_line_saying_so(start):
    began = time.monotonic()
    code, out = start("hang", within="1")
    assert time.monotonic() - began < 3
    assert code == 0
    assert "the check did not finish in 1 s" in json.loads(out)["systemMessage"]


def test_the_plain_brief_prints_the_same_text_without_the_host_envelope(start):
    _, plain = start("expired", hook=False)
    assert plain.strip() == json.loads(start("expired")[1])["systemMessage"]
