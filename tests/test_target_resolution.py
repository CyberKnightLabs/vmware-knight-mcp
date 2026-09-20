from vmware_knight.config import AppConfig, TargetConfig


def make_config():
    return AppConfig(
        targets=(
            TargetConfig(
                name="esxi-56",
                host="10.132.32.56",
                config_username="root",
                type="esxi",
                tag="lab-esxi1",
            ),
            TargetConfig(
                name="vcenter",
                host="vc.networkingwithehsan.local",
                config_username="administrator@vsphere.local",
                type="vcenter",
                tag="lab-vcenter",
            ),
        )
    )


def test_resolve_target_by_name():
    cfg = make_config()
    assert cfg.get_target("esxi-56").host == "10.132.32.56"


def test_resolve_target_by_tag():
    cfg = make_config()
    assert cfg.get_target("lab-esxi1").name == "esxi-56"


def test_resolve_target_by_host():
    cfg = make_config()
    assert cfg.get_target("10.132.32.56").name == "esxi-56"


def test_resolution_is_case_insensitive():
    cfg = make_config()
    assert cfg.get_target("LAB-VCENTER").name == "vcenter"


def test_duplicate_identifier_rejected(tmp_path):
    from vmware_knight.config import ConfigError, load_config

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
targets:
  - name: esxi-56
    host: 10.132.32.56
    username: root
    type: esxi
    tag: lab-host

  - name: esxi-64
    host: 10.132.32.64
    username: root
    type: esxi
    tag: lab-host
"""
    )

    try:
        load_config(config_file)
    except ConfigError as exc:
        assert "Duplicate or ambiguous target identifier" in str(exc)
    else:
        raise AssertionError("Expected ConfigError for duplicate tag")
