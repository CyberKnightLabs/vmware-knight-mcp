from types import SimpleNamespace

import pytest

from vmware_knight.ops import inventory
from vmware_knight.ops.inventory import HostNameNotFoundError, resolve_host_name


def _vnic(ip):
    return SimpleNamespace(spec=SimpleNamespace(ip=SimpleNamespace(ipAddress=ip, ipV6Config=None)))


def _inventory(monkeypatch, hosts):
    """hosts: {name: [ip, ...]}"""
    rows = [(object(), {"name": n, "config.network.vnic": [_vnic(ip) for ip in ips]})
            for n, ips in hosts.items()]
    monkeypatch.setattr(inventory, "_collect", lambda si, t, paths: rows)


VCENTER = {
    "esx01.lab.local": ["10.0.0.11"],
    "esx02.lab.local": ["10.0.0.12", "192.168.50.12"],
    "10.0.0.13": ["10.0.0.13"],
}


@pytest.mark.parametrize(
    "requested, expected",
    [
        ("esx01.lab.local", "esx01.lab.local"),  # exact
        ("ESX01.LAB.LOCAL", "esx01.lab.local"),  # any case
        ("esx02", "esx02.lab.local"),  # short name
        ("192.168.50.12", "esx02.lab.local"),  # any VMkernel IP
        ("10.0.0.13", "10.0.0.13"),  # registered by IP
        (" esx01.lab.local ", "esx01.lab.local"),  # surrounding spaces
    ],
)
def test_resolves(monkeypatch, requested, expected):
    _inventory(monkeypatch, VCENTER)
    assert resolve_host_name(None, requested) == expected


def test_unknown_lists_available_hosts(monkeypatch):
    _inventory(monkeypatch, VCENTER)
    with pytest.raises(HostNameNotFoundError) as exc:
        resolve_host_name(None, "10.0.0.99")
    msg = str(exc.value)
    assert "10.0.0.99" in msg
    for name in VCENTER:
        assert name in msg


def test_aliases_only_apply_to_single_host_targets(monkeypatch):
    _inventory(monkeypatch, VCENTER)
    with pytest.raises(HostNameNotFoundError):
        resolve_host_name(None, "lab-vcenter", aliases=("vcenter", "lab-vcenter", "vc.lab"))


def test_standalone_esxi_accepts_target_tag_and_address(monkeypatch):
    _inventory(monkeypatch, {"ESXi-56": ["10.132.32.99"]})
    aliases = ("esxi-56", "server56", "esxi56.lab.local")
    assert resolve_host_name(None, "server56", aliases=aliases) == "ESXi-56"
    assert resolve_host_name(None, "SERVER56", aliases=aliases) == "ESXi-56"
    assert resolve_host_name(None, "esxi56.lab.local", aliases=aliases) == "ESXi-56"


def test_ambiguous_short_name_refuses_to_guess(monkeypatch):
    _inventory(monkeypatch, {"esx01.a.local": [], "esx01.b.local": []})
    with pytest.raises(HostNameNotFoundError, match="matches several hosts"):
        resolve_host_name(None, "esx01")


def test_long_host_list_is_capped(monkeypatch):
    _inventory(monkeypatch, {f"esx{i:02}.lab": [] for i in range(30)})
    with pytest.raises(HostNameNotFoundError, match=r"\(and 10 more\)"):
        resolve_host_name(None, "nope")


def test_library_not_found_errors_keep_their_message():
    from vmware_monitor.ops.investigate_host import HostNotFoundError
    from vmware_monitor.ops.vm_info import VMNotFoundError

    from vmware_knight.mcp_server import _shared

    host_msg = _shared._safe_error(HostNotFoundError("Host not found: x"), "t")
    vm_msg = _shared._safe_error(VMNotFoundError("VM not found: y"), "t")
    assert host_msg == "Host not found: x"
    assert vm_msg == "VM not found: y"
