"""Brand normalization for user-facing data returned by shared dependencies."""

from __future__ import annotations

from typing import Any


_REPLACEMENTS = (
    ("vmware-aiops", "vmware-knight"),
    ("VMware-AIops", "VMware Knight"),
    ("VMware AIops", "VMware Knight"),
)


def normalize_branding(value: Any) -> Any:
    """Recursively normalize legacy product branding in user-facing data.

    Mutable containers are updated in place so callers retain object identity.
    """
    if isinstance(value, str):
        for old, new in _REPLACEMENTS:
            value = value.replace(old, new)
        return value

    if isinstance(value, dict):
        for key, item in value.items():
            value[key] = normalize_branding(item)
        return value

    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = normalize_branding(item)
        return value

    if isinstance(value, tuple):
        return tuple(normalize_branding(item) for item in value)

    return value


def knight_cli_drilldown(issue: dict) -> str:
    """Return VMware Knight-branded CLI next-step guidance for a summary issue."""
    from vmware_monitor.ops.cluster_summary import cli_drilldown

    return normalize_branding(cli_drilldown(issue))
