"""The MCP server picks up wizard edits to config.yaml and .env without a restart."""

import os

import pytest

from vmware_knight import config
from vmware_knight.mcp_server import _shared


def _write_config(path, name, tag):
    path.write_text(
        "targets:\n"
        f"  - name: {name}\n"
        f"    tag: {tag}\n"
        "    host: 10.132.32.52\n"
        "    type: esxi\n"
        "    username: root\n",
        encoding="utf-8",
    )


def _touch_later(*paths):
    """Make sure a rewrite is seen as a change even within one mtime tick."""
    for p in paths:
        st = p.stat()
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))


@pytest.fixture
def files(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    env = tmp_path / ".env"
    monkeypatch.setenv("VMWARE_KNIGHT_CONFIG", str(cfg))
    monkeypatch.setattr(config, "ENV_FILE", env)
    monkeypatch.setattr(_shared, "ENV_FILE", env)
    monkeypatch.setattr(config, "_DOTENV_KEYS", {})
    monkeypatch.setattr(_shared, "_conn_mgr", None)
    monkeypatch.setattr(_shared, "_conn_mgr_stamp", None)
    for key in ("VMWARE_ESXI_52_PASSWORD", "VMWARE_SERVERTAG52_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    return cfg, env


def _password(target):
    return _shared._ensure_conn_mgr()._config.get_target(target).password


def test_rename_in_wizard_is_seen_without_restart(files):
    cfg, env = files
    _write_config(cfg, "esxi-52", "server52")
    env.write_text("VMWARE_ESXI_52_PASSWORD=secret\n", encoding="utf-8")
    config.reload_env_file()  # what import does at server start
    assert _password("server52") == "secret"

    # The wizard renames the target and moves its password to the new key.
    _write_config(cfg, "serverTag52", "server52")
    env.write_text("VMWARE_SERVERTAG52_PASSWORD=secret\n", encoding="utf-8")
    _touch_later(cfg, env)

    assert _password("server52") == "secret"
    assert _shared._ensure_conn_mgr()._config.get_target("server52").name == "serverTag52"
    assert "VMWARE_ESXI_52_PASSWORD" not in os.environ  # the stale key is dropped


def test_env_changed_between_start_and_first_call(files):
    """The reported case: .env loaded at import, wizard edit, then the first call."""
    cfg, env = files
    _write_config(cfg, "esxi-52", "server52")
    env.write_text("VMWARE_ESXI_52_PASSWORD=secret\n", encoding="utf-8")
    config.reload_env_file()  # server starts

    _write_config(cfg, "serverTag52", "server52")
    env.write_text("VMWARE_SERVERTAG52_PASSWORD=secret\n", encoding="utf-8")

    assert _password("server52") == "secret"  # first tool call


def test_unchanged_files_reuse_the_manager(files):
    cfg, env = files
    _write_config(cfg, "esxi-52", "server52")
    env.write_text("VMWARE_ESXI_52_PASSWORD=secret\n", encoding="utf-8")
    first = _shared._ensure_conn_mgr()
    assert _shared._ensure_conn_mgr() is first


def test_real_environment_wins_over_env_file(files, monkeypatch):
    cfg, env = files
    _write_config(cfg, "esxi-52", "server52")
    monkeypatch.setenv("VMWARE_ESXI_52_PASSWORD", "from-client-env")
    env.write_text("VMWARE_ESXI_52_PASSWORD=from-dotenv\n", encoding="utf-8")
    config.reload_env_file()
    assert _password("server52") == "from-client-env"

    env.write_text("VMWARE_ESXI_52_PASSWORD=changed\n", encoding="utf-8")
    _touch_later(env)
    assert _password("server52") == "from-client-env"


def test_invalid_edit_keeps_last_good_config(files):
    cfg, env = files
    _write_config(cfg, "esxi-52", "server52")
    env.write_text("VMWARE_ESXI_52_PASSWORD=secret\n", encoding="utf-8")
    good = _shared._ensure_conn_mgr()

    cfg.write_text("targets: [ this is not yaml", encoding="utf-8")
    _touch_later(cfg)

    assert _shared._ensure_conn_mgr() is good
    assert _password("server52") == "secret"
