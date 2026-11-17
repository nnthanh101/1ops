import json
from pathlib import Path

import pytest

from one_ops import cli
from one_ops import settings as s


def test_merge_keeps_user_values_and_adds_missing():
    existing = {
        "model": "x",
        "permissions": {"deny": ["Read(./secrets)"]},
        "enabledPlugins": {"1ops@1ops": False},
    }
    merged = s.merge(existing, s.BASELINE)
    assert merged["model"] == "x"
    assert merged["enabledPlugins"]["1ops@1ops"] is False  # the user's choice wins
    assert merged["permissions"]["deny"][0] == "Read(./secrets)"
    assert "Read(./.env)" in merged["permissions"]["deny"]
    assert s.merge(merged, s.BASELINE) == merged  # idempotent


@pytest.mark.parametrize("name", ["aws", "azure", "itsm"])
def test_builtin_profiles_are_pinned_and_keep_secrets_out(name):
    profile = s.load_profile(name)
    for server in profile["mcpServers"].values():
        text = json.dumps(server)
        assert "@latest" not in text
        for key, value in server.get("env", {}).items():
            # secrets and account-specific values are always ${VAR} references
            if any(k in key for k in ("TOKEN", "KEY", "PROFILE", "_ID", "USERNAME", "URL")):
                assert value.startswith("${")


def test_unknown_profile_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        s.load_profile("nope")
    bad = tmp_path / "bad.json"
    bad.write_text("{}")
    with pytest.raises(ValueError):
        s.load_profile(str(bad))


def test_custom_profile_file(tmp_path: Path):
    f = tmp_path / "mine.json"
    f.write_text(
        json.dumps({"mcpServers": {"x": {"type": "http", "url": "https://example.invalid/mcp"}}})
    )
    assert "x" in s.load_profile(str(f))["mcpServers"]


def test_team_dry_run_writes_nothing(tmp_path: Path):
    assert (
        cli.main(["config", "--scope", "team", "--dir", str(tmp_path), "--connectors", "aws"]) == 0
    )
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".mcp.json").exists()


def test_team_write_then_rerun_is_noop(tmp_path: Path):
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {"mine": {"command": "x"}}}))
    args = [
        "config",
        "--scope",
        "team",
        "--dir",
        str(tmp_path),
        "--connectors",
        "aws",
        "itsm",
        "--yes",
    ]
    assert cli.main(args) == 0
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert settings["enabledPlugins"]["1ops@1ops"] is True
    mcp = json.loads((tmp_path / ".mcp.json").read_text())["mcpServers"]
    assert "mine" in mcp and "awslabs-cloudtrail" in mcp and "atlassian" in mcp
    assert "mcp__atlassian__*" in settings["permissions"]["ask"]  # every Jira/Confluence call asks
    before = (tmp_path / ".mcp.json").read_text()
    assert cli.main(args) == 0
    assert (tmp_path / ".mcp.json").read_text() == before


def test_org_scope_writes_to_out_folder_only(tmp_path: Path):
    assert (
        cli.main(
            ["config", "--scope", "org", "--out", str(tmp_path), "--connectors", "azure", "--yes"]
        )
        == 0
    )
    assert (tmp_path / "managed-settings.json").exists()
    assert "azure" in json.loads((tmp_path / "managed-mcp.json").read_text())["mcpServers"]


def test_mask_never_shows_full_account():
    assert cli._mask("123456789012") == "****9012"


# ── 1ops.yaml ────────────────────────────────────────────────────────────────

from one_ops import config_file as cf


def _yaml(tmp_path: Path, text: str) -> Path:
    f = tmp_path / "1ops.yaml"
    f.write_text(text)
    return f


def test_yaml_rejects_unquoted_non_strings_and_secrets(tmp_path: Path):
    with pytest.raises(TypeError, match="quoted string"):
        cf.load(_yaml(tmp_path, "connectors:\n  azure:\n    AZURE_TENANT_ID: 0123\n"))
    with pytest.raises(ValueError, match="secret"):
        cf.load(_yaml(tmp_path, "connectors:\n  aws:\n    GRAFANA_API_KEY: 'x'\n"))
    with pytest.raises(ValueError, match="scope"):
        cf.load(_yaml(tmp_path, "scope: everyone\n"))


def test_variables_and_substitute():
    aws = s.load_profile("aws")
    assert {"AWS_BILLING_PROFILE", "AWS_OPERATIONS_PROFILE", "AWS_REGION"} <= set(cf.variables(aws))
    spec = cf.substitute({"env": {"A": "${AWS_REGION}", "B": "${OTHER:-x}"}}, {"AWS_REGION": "r"})
    assert spec == {"env": {"A": "r", "B": "${OTHER:-x}"}}


def test_team_file_keeps_var_references_out_of_git(tmp_path: Path):
    f = _yaml(
        tmp_path,
        f"scope: team\ndir: '{tmp_path}'\nconnectors:\n  aws:\n    AWS_OPERATIONS_PROFILE: 'ops-ro'\n",
    )
    assert cli.main(["config", "--file", str(f), "--yes"]) == 0
    text = (tmp_path / ".mcp.json").read_text()
    assert "${AWS_OPERATIONS_PROFILE}" in text and "ops-ro" not in text


def test_env_prints_quoted_exports(tmp_path: Path, capsys):
    f = _yaml(
        tmp_path,
        "connectors:\n  aws:\n    AWS_REGION: 'ap-southeast-2'\n    AWS_OPERATIONS_PROFILE: 'a b'\n",
    )
    assert cli.main(["env", "--file", str(f)]) == 0
    out = capsys.readouterr().out
    assert (
        "export AWS_REGION=ap-southeast-2" in out and "export AWS_OPERATIONS_PROFILE='a b'" in out
    )
