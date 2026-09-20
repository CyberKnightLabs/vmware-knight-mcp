"""Cluster-health summary command (read-only) — delegates to vmware-monitor.

VMware Knight is the family's conversational entry point, so it re-exposes the same
one-glance triage the vmware-monitor CLI offers. The aggregation and both
renderers (terminal + offline HTML) live in the vmware-monitor library, so this
command is a thin adapter over VMware Knight's own vCenter connection — no logic or
rendering is duplicated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from vmware_knight.branding import knight_cli_drilldown, normalize_branding

from vmware_knight.cli._common import (
    ConfigOption,
    TargetOption,
    _audit,
    _get_connection,
    cli_errors,
)
from vmware_policy import audited



def _render_summary_console(data: dict, top: int) -> None:
    """Render VMware Knight-branded cluster summary output."""
    from rich.console import Console
    from rich.markup import escape
    from rich.table import Table

    console = Console()
    t = data["totals"]
    worst = t["worst_status"]

    status_style = {
        "ok": "green",
        "warn": "yellow",
        "critical": "red",
    }

    sev_style = {
        "info": "cyan",
        "warning": "yellow",
        "critical": "red",
    }

    console.print(
        f"[bold]Cluster health[/] — {t['clusters']} clusters, "
        f"{t['hosts_connected']}/{t['hosts_total']} hosts connected"
        + (
            f", {t.get('vms_on', 0)}/{t.get('vms_total', 0)} VMs on"
            if "vms_total" in t
            else ""
        )
        + f"  ·  overall: [{status_style.get(worst, 'white')}]{worst.upper()}[/]"
    )

    if top > 0:
        issues = data.get("top_issues", [])
        total = data.get("issues_total", 0)

        if not issues:
            console.print("[green]No issues detected — every cluster is OK.[/]\n")
        else:
            shown = len(issues)
            title = f"Top {shown} issues" + (f" (of {total})" if total > shown else "")
            table = Table(title=title)
            table.add_column("#", justify="right", style="dim")
            table.add_column("Severity")
            table.add_column("Object", max_width=28)
            table.add_column("Problem · next step")

            for n, issue in enumerate(issues, 1):
                sev = issue["severity"]
                hint = knight_cli_drilldown(issue)
                also = "".join(
                    f"\n[dim]also via {escape(str(a['vcenter']))}: "
                    f"{escape(str(a['detail']).split(' — ')[0])}[/]"
                    for a in issue.get("also_seen_via", [])
                )

                table.add_row(
                    str(n),
                    f"[{sev_style.get(sev, 'white')}]{sev.upper()}[/]",
                    f"[cyan]{escape(str(issue['object']))}[/]\n"
                    f"[dim]{escape(str(issue.get('cluster') or '—'))}[/]",
                    escape(str(issue["detail"]))
                    + also
                    + (f"\n[dim]→ {escape(hint)}[/]" if hint else ""),
                )

            console.print(table)

    table = Table(title="Cluster Health Summary")
    table.add_column("Status")
    table.add_column("Cluster", style="cyan")
    table.add_column("Hosts", justify="right")
    if "vms_total" in t:
        table.add_column("VMs on", justify="right")
    table.add_column("CPU%", justify="right")
    table.add_column("Mem%", justify="right")
    table.add_column("HA")
    table.add_column("DRS")
    table.add_column("Alarms C/W", justify="right")
    table.add_column("Attention")

    for c in data["clusters"]:
        style = status_style.get(c["status"], "white")
        row = [
            f"[{style}]{c['status'].upper()}[/]",
            c["name"],
            f"{c['hosts_connected']}/{c['hosts_total']}",
        ]

        if "vms_total" in t:
            row.append(f"{c.get('vms_on', 0)}/{c.get('vms_total', 0)}")

        row += [
            str(c["cpu_used_pct"]),
            str(c["mem_used_pct"]),
            "n/a" if c["ha_enabled"] is None else ("ON" if c["ha_enabled"] else "OFF"),
            "n/a" if c["drs_enabled"] is None else ("ON" if c["drs_enabled"] else "off"),
            f"{c['alarms']['critical']}/{c['alarms']['warning']}",
            "; ".join(c["attention"]) or "—",
        ]
        table.add_row(*row)

    console.print(table)
    console.print(f"[dim]{data['customization_hint']}[/]")


@cli_errors
@audited("cluster_health_summary")
def cluster_summary_cmd(
    cluster: Annotated[
        str | None,
        typer.Option("--cluster", help="Show only clusters matching this substring"),
    ] = None,
    no_vms: Annotated[
        bool,
        typer.Option("--no-vms", help="Skip the VM rollup pass (faster on huge fleets)"),
    ] = False,
    top: Annotated[
        int,
        typer.Option("--top", help="Size of the top-issues focus list (0 to hide)"),
    ] = 10,
    html: Annotated[
        bool,
        typer.Option(
            "--html", help="Write an offline HTML snapshot to ~/vmware-health/ (timestamped)"
        ),
    ] = False,
    html_path: Annotated[
        Path | None,
        typer.Option(
            "--html-path", help="Write the HTML snapshot to this exact path (implies --html)"
        ),
    ] = None,
    target: TargetOption = None,
    config: ConfigOption = None,
) -> None:
    """One-glance cluster health: is anything on fire?

    Leads with the top-N individual anomalies, then an opinionated per-cluster
    table. Same view as `vmware-monitor summary` — the logic is shared. Pass
    --html for an offline, timestamped snapshot file.
    """
    from vmware_monitor.cli_observability import write_html_snapshot
    from vmware_monitor.ops.cluster_summary import get_cluster_health_summary

    si, cfg = _get_connection(target, config)
    tgt = target or getattr(getattr(cfg, "default_target", None), "name", "default")
    data = normalize_branding(
        get_cluster_health_summary(
            si,
            cluster_filter=cluster,
            include_vms=not no_vms,
            top_n=top,
        )
    )
    _audit.log_query(
        target=tgt, resource="clusters", query_type="cluster_health_summary", skill="knight"
    )

    if html or html_path is not None:
        write_html_snapshot(data, tgt, html_path)
        return
    _render_summary_console(data, top)
