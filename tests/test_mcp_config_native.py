import json
from pathlib import Path

from vmware_knight.cli import mcp_config


def _resolved_test_executable() -> str:
    return str(Path("/opt/test/vmware-knight").expanduser().resolve())


def test_native_claude_install(tmp_path, monkeypatch):
    dest = tmp_path / "claude_desktop_config.json"

    dest.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "existing-server": {
                        "command": "/tmp/existing"
                    }
                },
                "preferences": {
                    "example": True
                }
            }
        )
    )

    monkeypatch.setitem(
        mcp_config._AGENT_INSTALL_PATHS,
        "claude",
        dest,
    )

    mcp_config.mcp_config_install(
        agent="claude",
        install_path="/opt/test/vmware-knight",
        yes=True,
    )

    data = json.loads(dest.read_text())

    assert "existing-server" in data["mcpServers"]
    assert "vmware-knight" in data["mcpServers"]
    assert data["mcpServers"]["vmware-knight"]["command"] == _resolved_test_executable()
    assert data["mcpServers"]["vmware-knight"]["args"] == ["mcp"]
    assert data["preferences"]["example"] is True


def test_native_codex_install(tmp_path, monkeypatch):
    dest = tmp_path / "config.toml"

    dest.write_text(
        """
model = "gpt-test"

[mcp_servers.existing]
command = "/tmp/existing"
enabled = true
""".lstrip()
    )

    monkeypatch.setitem(
        mcp_config._AGENT_INSTALL_PATHS,
        "codex",
        dest,
    )

    mcp_config.mcp_config_install(
        agent="codex",
        install_path="/opt/test/vmware-knight",
        yes=True,
    )

    text = dest.read_text()
    expected_command = json.dumps(_resolved_test_executable())

    assert 'model = "gpt-test"' in text
    assert "[mcp_servers.existing]" in text
    assert "[mcp_servers.vmware-knight]" in text
    assert f"command = {expected_command}" in text
    assert 'args = ["mcp"]' in text
    assert "enabled = true" in text
    assert "startup_timeout_sec = 120" in text


def test_codex_install_is_idempotent(tmp_path, monkeypatch):
    dest = tmp_path / "config.toml"

    monkeypatch.setitem(
        mcp_config._AGENT_INSTALL_PATHS,
        "codex",
        dest,
    )

    for _ in range(2):
        mcp_config.mcp_config_install(
            agent="codex",
            install_path="/opt/test/vmware-knight",
            yes=True,
        )

    text = dest.read_text()

    assert text.count("[mcp_servers.vmware-knight]") == 1
