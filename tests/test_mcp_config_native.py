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


def test_codex_install_non_windows_has_no_env_block(tmp_path, monkeypatch):
    import tomllib

    dest = tmp_path / "config.toml"
    monkeypatch.setitem(mcp_config._AGENT_INSTALL_PATHS, "codex", dest)
    monkeypatch.setattr(mcp_config, "_IS_WINDOWS", False)

    mcp_config.mcp_config_install(
        agent="codex", install_path="/opt/test/vmware-knight", yes=True
    )

    server = tomllib.loads(dest.read_text())["mcp_servers"]["vmware-knight"]
    assert server["command"] == _resolved_test_executable()
    assert "env" not in server


def test_codex_install_windows_adds_exe_and_home_env(tmp_path, monkeypatch):
    import tomllib

    dest = tmp_path / "config.toml"
    monkeypatch.setitem(mcp_config._AGENT_INSTALL_PATHS, "codex", dest)
    monkeypatch.setattr(mcp_config, "_IS_WINDOWS", True)
    monkeypatch.setenv("USERPROFILE", r"C:\Users\tester")
    monkeypatch.setenv("SYSTEMROOT", r"C:\WINDOWS")

    for _ in range(2):  # reinstall must not duplicate the env sub-table
        mcp_config.mcp_config_install(
            agent="codex", install_path="/opt/test/vmware-knight", yes=True
        )

    text = dest.read_text()
    server = tomllib.loads(text)["mcp_servers"]["vmware-knight"]

    assert server["command"] == _resolved_test_executable() + ".exe"
    assert server["env"]["USERPROFILE"] == r"C:\Users\tester"
    assert server["env"]["SYSTEMROOT"] == r"C:\WINDOWS"
    assert server["env"]["PYTHONUTF8"] == "1"
    assert text.count("[mcp_servers.vmware-knight.env]") == 1


def test_windows_keeps_existing_exe_suffix(monkeypatch):
    monkeypatch.setattr(mcp_config, "_IS_WINDOWS", True)

    assert mcp_config._resolve_executable("/opt/test/vmware-knight.exe").endswith(
        "vmware-knight.exe"
    )
    assert not mcp_config._resolve_executable("/opt/test/vmware-knight.exe").endswith(
        ".exe.exe"
    )


def test_default_executable_per_platform(monkeypatch):
    monkeypatch.setattr(mcp_config, "_IS_WINDOWS", True)
    assert mcp_config.default_executable().endswith("vmware-knight.exe")

    monkeypatch.setattr(mcp_config, "_IS_WINDOWS", False)
    assert mcp_config.default_executable() == str(
        Path.home() / ".local" / "bin" / "vmware-knight"
    )
