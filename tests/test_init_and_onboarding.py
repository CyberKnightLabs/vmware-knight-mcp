"""Regression tests for onboarding: the `vmware-knight init` wizard, the doctor
init reference (no false promise —  #2), and teaching SOAP auth/TLS errors.
"""

from __future__ import annotations

from vmware_policy.fsperms import assert_owner_only

import os
from pathlib import Path

import pytest
import typer

from vmware_knight import init_wizard


# ── init wizard ──────────────────────────────────────────────────────────────


@pytest.fixture
def _wizard_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cfg_dir = tmp_path / ".vmware-knight"
    monkeypatch.setattr(init_wizard, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(init_wizard, "CONFIG_FILE", cfg_dir / "config.yaml")
    monkeypatch.setattr(init_wizard, "ENV_FILE", cfg_dir / ".env")
    return cfg_dir


def _feed(monkeypatch: pytest.MonkeyPatch, answers: list[object], confirms: list[bool]) -> None:
    a = iter(answers)
    c = iter(confirms)
    monkeypatch.setattr(init_wizard.typer, "prompt", lambda *args, **kwargs: next(a))
    monkeypatch.setattr(init_wizard.typer, "confirm", lambda *args, **kwargs: next(c))


def test_init_writes_grep_safe_env(_wizard_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from vmware_knight.config import _decode_secret

    _feed(
        monkeypatch,
        answers=["lab-vc", "lab-vcenter", "10.1.2.3", "1", "administrator@vsphere.local", 443, "S3cr3t!pw"],
        confirms=[True],
    )
    assert init_wizard.run_init(skip_test=True) == 0

    env_text = (_wizard_env / ".env").read_text(encoding="utf-8")
    assert "VMWARE_LAB_VC_PASSWORD=b64:" in env_text
    assert "S3cr3t!pw" not in env_text  # never plaintext on disk
    assert_owner_only(_wizard_env / ".env")
    line = next(ln for ln in env_text.splitlines() if ln.startswith("VMWARE_LAB_VC_PASSWORD="))
    assert _decode_secret(line.split("=", 1)[1]) == "S3cr3t!pw"


# ── doctor references a real init command (no false promise) ──────────────────


def _init_registered() -> bool:
    from vmware_knight.cli import app

    return any(c.name == "init" for c in app.registered_commands)


def test_doctor_init_reference_is_backed_by_real_command():
    from vmware_knight import doctor

    src = Path(doctor.__file__).read_text(encoding="utf-8")
    if "vmware-knight init" in src:
        assert _init_registered(), "doctor recommends init but no such command is registered"


# ── SOAP errors teach where to fix the problem ───────────────────────────────


def test_invalid_login_error_is_teaching(capsys):
    from pyVmomi import vim

    from vmware_knight.cli._common import cli_errors

    @cli_errors
    def boom():
        raise vim.fault.InvalidLogin()

    with pytest.raises(typer.Exit):
        boom()
    out = capsys.readouterr().out
    assert ".vmware-knight/.env" in out
    assert "VMWARE_<TARGET>_PASSWORD" in out


def test_tls_error_is_teaching(capsys):
    import ssl

    from vmware_knight.cli._common import cli_errors

    @cli_errors
    def boom():
        raise ssl.SSLError("certificate verify failed")

    with pytest.raises(typer.Exit):
        boom()
    out = capsys.readouterr().out
    assert "verify_ssl" in out


def test_setup_wizard_add_target(tmp_path, monkeypatch):
    import yaml
    from vmware_knight import setup_wizard

    cfg_dir = tmp_path / ".vmware-knight"
    cfg_file = cfg_dir / "config.yaml"

    monkeypatch.setattr(setup_wizard, "CONFIG_FILE", cfg_file)

    answers = iter(
        [
            "esxi-99",          # name
            "lab-esxi99",       # tag
            "10.10.10.99",      # host
            "2",                # type
            "root",             # username
            443,                # port
            "Secret123!",       # password
        ]
    )
    confirms = iter([False])

    monkeypatch.setattr(
        setup_wizard.typer,
        "prompt",
        lambda *args, **kwargs: next(answers),
    )
    monkeypatch.setattr(
        setup_wizard.typer,
        "confirm",
        lambda *args, **kwargs: next(confirms),
    )

    monkeypatch.setattr(
        setup_wizard,
        "_write_env",
        lambda name, password: "VMWARE_ESXI_99_PASSWORD",
    )

    setup_wizard._add_target()

    data = yaml.safe_load(cfg_file.read_text())

    assert len(data["targets"]) == 1
    assert data["targets"][0]["name"] == "esxi-99"
    assert data["targets"][0]["tag"] == "lab-esxi99"
    assert data["targets"][0]["host"] == "10.10.10.99"
    assert data["targets"][0]["type"] == "esxi"


def test_setup_wizard_edit_target(tmp_path, monkeypatch):
    import yaml
    from vmware_knight import setup_wizard

    cfg_dir = tmp_path / ".vmware-knight"
    cfg_file = cfg_dir / "config.yaml"
    cfg_dir.mkdir(parents=True)

    cfg_file.write_text(
        """
targets:
  - name: esxi-99
    tag: lab-esxi99
    host: 10.10.10.99
    type: esxi
    username: root
    port: 443
    verify_ssl: false
scanner:
  enabled: true
notify:
  webhook_url: ''
"""
    )

    monkeypatch.setattr(setup_wizard, "CONFIG_FILE", cfg_file)

    answers = iter(
        [
            1,                  # select target
            "esxi-99",          # name
            "lab-esxi-renamed", # tag
            "10.10.10.100",     # host
            "2",                # type
            "root",             # username
            443,                # port
        ]
    )
    confirms = iter(
        [
            False,  # verify SSL
            False,  # change password
        ]
    )

    monkeypatch.setattr(
        setup_wizard.typer,
        "prompt",
        lambda *args, **kwargs: next(answers),
    )
    monkeypatch.setattr(
        setup_wizard.typer,
        "confirm",
        lambda *args, **kwargs: next(confirms),
    )

    setup_wizard._edit_target()

    data = yaml.safe_load(cfg_file.read_text())

    target = data["targets"][0]
    assert target["name"] == "esxi-99"
    assert target["tag"] == "lab-esxi-renamed"
    assert target["host"] == "10.10.10.100"
    assert target["type"] == "esxi"
    assert target["username"] == "root"
    assert target["port"] == 443
    assert target["verify_ssl"] is False


def test_setup_wizard_remove_target(tmp_path, monkeypatch):
    import yaml
    from vmware_knight import setup_wizard

    cfg_dir = tmp_path / ".vmware-knight"
    cfg_file = cfg_dir / "config.yaml"
    cfg_dir.mkdir(parents=True)

    cfg_file.write_text(
        """
targets:
  - name: esxi-99
    tag: lab-esxi99
    host: 10.10.10.99
    type: esxi
    username: root
    port: 443
    verify_ssl: false

  - name: vcenter
    tag: lab-vcenter
    host: vc.lab.local
    type: vcenter
    username: administrator@vsphere.local
    port: 443
    verify_ssl: false

scanner:
  enabled: true

notify:
  webhook_url: ''
"""
    )

    monkeypatch.setattr(setup_wizard, "CONFIG_FILE", cfg_file)

    answers = iter([1])
    confirms = iter([True])

    monkeypatch.setattr(
        setup_wizard.typer,
        "prompt",
        lambda *args, **kwargs: next(answers),
    )
    monkeypatch.setattr(
        setup_wizard.typer,
        "confirm",
        lambda *args, **kwargs: next(confirms),
    )

    setup_wizard._remove_target()

    data = yaml.safe_load(cfg_file.read_text())

    assert len(data["targets"]) == 1
    assert data["targets"][0]["name"] == "vcenter"
    assert data["targets"][0]["tag"] == "lab-vcenter"


def test_setup_wizard_configure_codex(tmp_path, monkeypatch):
    from vmware_knight import setup_wizard

    calls = []

    answers = iter(
        [
            "2",  # Codex
            "/opt/test/vmware-knight",
        ]
    )
    confirms = iter([True])

    monkeypatch.setattr(
        setup_wizard.typer,
        "prompt",
        lambda *args, **kwargs: next(answers),
    )
    monkeypatch.setattr(
        setup_wizard.typer,
        "confirm",
        lambda *args, **kwargs: next(confirms),
    )

    import vmware_knight.cli.mcp_config as mcp_config

    monkeypatch.setattr(
        mcp_config,
        "mcp_config_install",
        lambda agent, install_path=None, yes=False: calls.append(
            (agent, install_path, yes)
        ),
    )

    setup_wizard._configure_mcp_client()

    assert calls == [
        ("codex", "/opt/test/vmware-knight", True)
    ]


def test_setup_wizard_rename_migrates_credentials(tmp_path, monkeypatch):
    import yaml
    from vmware_knight import setup_wizard

    cfg_dir = tmp_path / ".vmware-knight"
    cfg_file = cfg_dir / "config.yaml"
    cfg_dir.mkdir(parents=True)

    cfg_file.write_text(
        """
targets:
  - name: esxi-old
    tag: lab-esxi
    host: 10.10.10.99
    type: esxi
    username: root
    port: 443
    verify_ssl: false
scanner:
  enabled: true
notify:
  webhook_url: ''
"""
    )

    monkeypatch.setattr(setup_wizard, "CONFIG_FILE", cfg_file)

    writes = []
    deletes = []

    answers = iter(
        [
            1,              # select target
            "esxi-new",     # new name
            "lab-esxi",     # tag
            "10.10.10.99",  # host
            "2",            # type
            "root",         # username
            443,            # port
        ]
    )

    confirms = iter(
        [
            False,  # verify SSL
            False,  # change password
        ]
    )

    monkeypatch.setattr(
        setup_wizard.typer,
        "prompt",
        lambda *args, **kwargs: next(answers),
    )
    monkeypatch.setattr(
        setup_wizard.typer,
        "confirm",
        lambda *args, **kwargs: next(confirms),
    )

    class FakeTarget:
        password = "OldSecret123!"

    class FakeConfig:
        def get_target(self, name):
            assert name == "esxi-old"
            return FakeTarget()

    real_load_config = setup_wizard.load_config

    def fake_load_config(path=None):
        if path == cfg_file:
            data = yaml.safe_load(cfg_file.read_text())
            if data["targets"][0]["name"] == "esxi-old":
                return FakeConfig()
        return real_load_config(path)

    monkeypatch.setattr(setup_wizard, "load_config", fake_load_config)

    monkeypatch.setattr(
        setup_wizard,
        "_write_env",
        lambda name, password: writes.append((name, password)),
    )
    monkeypatch.setattr(
        setup_wizard,
        "_delete_env",
        lambda name: deletes.append(name),
    )

    setup_wizard._edit_target()

    data = yaml.safe_load(cfg_file.read_text())

    assert data["targets"][0]["name"] == "esxi-new"
    assert writes == [("esxi-new", "OldSecret123!")]
    assert deletes == ["esxi-old"]


def test_setup_wizard_remove_target_cleans_credentials(tmp_path, monkeypatch):
    import yaml
    from vmware_knight import setup_wizard

    cfg_dir = tmp_path / ".vmware-knight"
    cfg_file = cfg_dir / "config.yaml"
    cfg_dir.mkdir(parents=True)

    cfg_file.write_text(
        """
targets:
  - name: esxi-99
    tag: lab-esxi99
    host: 10.10.10.99
    type: esxi
    username: root
    port: 443
    verify_ssl: false

  - name: vcenter
    tag: lab-vcenter
    host: vc.lab.local
    type: vcenter
    username: administrator@vsphere.local
    port: 443
    verify_ssl: false

scanner:
  enabled: true

notify:
  webhook_url: ''
"""
    )

    monkeypatch.setattr(setup_wizard, "CONFIG_FILE", cfg_file)

    deleted = []

    monkeypatch.setattr(
        setup_wizard.typer,
        "prompt",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        setup_wizard.typer,
        "confirm",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        setup_wizard,
        "_delete_env",
        lambda name: deleted.append(name),
    )

    setup_wizard._remove_target()

    data = yaml.safe_load(cfg_file.read_text())

    assert len(data["targets"]) == 1
    assert data["targets"][0]["name"] == "vcenter"
    assert deleted == ["esxi-99"]


def test_setup_wizard_set_target_tag(tmp_path, monkeypatch):
    import yaml
    from vmware_knight import setup_wizard

    cfg_dir = tmp_path / ".vmware-knight"
    cfg_file = cfg_dir / "config.yaml"
    cfg_dir.mkdir(parents=True)

    cfg_file.write_text(
        """
targets:
  - name: vcenter
    host: vc.lab.local
    type: vcenter
    username: administrator@vsphere.local
    port: 443
    verify_ssl: false

scanner:
  enabled: true

notify:
  webhook_url: ''
"""
    )

    monkeypatch.setattr(setup_wizard, "CONFIG_FILE", cfg_file)

    answers = iter(
        [
            1,              # select target
            "lab-vcenter",  # new tag
        ]
    )

    monkeypatch.setattr(
        setup_wizard.typer,
        "prompt",
        lambda *args, **kwargs: next(answers),
    )

    setup_wizard._set_target_tag()

    data = yaml.safe_load(cfg_file.read_text())

    assert data["targets"][0]["name"] == "vcenter"
    assert data["targets"][0]["tag"] == "lab-vcenter"
