"""The wizard's edit, remove and tag menus show each target's current tag."""

import pytest
import yaml

from vmware_knight import setup_wizard

CONFIG = {
    "targets": [
        {"name": "vcenter", "tag": "lab-vcenter", "host": "vc.lab.local", "type": "vcenter",
         "username": "administrator@vsphere.local"},
        {"name": "esxi-53", "host": "10.132.32.53", "type": "esxi", "username": "root"},
        {"name": "odd[1]", "tag": "x[y]", "host": "10.0.0.9", "type": "esxi", "username": "root"},
    ]
}


@pytest.fixture
def wizard(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump(CONFIG), encoding="utf-8")
    monkeypatch.setattr(setup_wizard, "CONFIG_FILE", cfg)
    # Pick an out-of-range number so each menu lists targets and then backs out.
    monkeypatch.setattr(setup_wizard.typer, "prompt", lambda *a, **k: 0)
    monkeypatch.setattr(setup_wizard.console, "width", 200)


@pytest.mark.parametrize("menu", ["_edit_target", "_remove_target", "_set_target_tag"])
def test_menu_shows_current_tags(wizard, capsys, menu):
    getattr(setup_wizard, menu)()
    out = capsys.readouterr().out

    assert "1. vcenter [tag: lab-vcenter] — vc.lab.local" in out
    assert "2. esxi-53 [tag: -] — 10.132.32.53" in out
    # Brackets inside names and tags are shown, not read as markup.
    assert "3. odd[1] [tag: x[y]] — 10.0.0.9" in out
