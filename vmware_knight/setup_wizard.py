"""Interactive VMware Knight management wizard."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from vmware_knight.config import CONFIG_FILE, load_config
from vmware_knight.init_wizard import _delete_env, _prompt_target, _write_env

console = Console()


def _list_targets() -> None:
    """Display all configured VMware targets."""
    try:
        config = load_config()
    except (OSError, ValueError) as exc:
        console.print(f"[red]Unable to load configuration:[/] {exc}")
        return

    table = Table(title="Configured VMware Targets")
    table.add_column("Name")
    table.add_column("Tag")
    table.add_column("Type")
    table.add_column("Host")
    table.add_column("Username")
    table.add_column("Port")

    for target in config.targets:
        table.add_row(
            target.name,
            target.tag or "-",
            target.type,
            target.host,
            target.username,
            str(target.port),
        )

    console.print(table)


def _add_target() -> None:
    """Add a new vCenter or ESXi target interactively."""
    import yaml

    target = _prompt_target()
    password = typer.prompt("Password", hide_input=True)

    if CONFIG_FILE.exists():
        raw = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    else:
        raw = {}

    raw.setdefault("targets", [])
    raw.setdefault(
        "scanner",
        {
            "enabled": True,
            "interval_minutes": 15,
            "severity_threshold": "warning",
        },
    )
    raw.setdefault("notify", {"webhook_url": ""})

    original = CONFIG_FILE.read_text(encoding="utf-8") if CONFIG_FILE.exists() else None

    raw["targets"].append(target)
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        yaml.safe_dump(raw, sort_keys=False),
        encoding="utf-8",
    )

    try:
        load_config(CONFIG_FILE)
    except Exception as exc:
        if original is None:
            CONFIG_FILE.unlink(missing_ok=True)
        else:
            CONFIG_FILE.write_text(original, encoding="utf-8")
        console.print(f"[red]Target not added:[/] {exc}")
        return

    _write_env(target["name"], password)

    console.print(
        f"[green]✓[/] Added {target['type']} target "
        f"[cyan]{target['name']}[/] with tag [cyan]{target['tag']}[/]."
    )


def _edit_target() -> None:
    """Edit an existing VMware target interactively."""
    import yaml

    if not CONFIG_FILE.exists():
        console.print("[yellow]No configuration file exists yet.[/]")
        return

    raw = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    targets = raw.get("targets", [])

    if not targets:
        console.print("[yellow]No VMware targets are configured.[/]")
        return

    console.print("\n[bold]Configured targets:[/]")
    for idx, target in enumerate(targets, start=1):
        label = target.get("tag") or target.get("name")
        console.print(
            f"{idx}. {target.get('name')} "
            f"[{label}] — {target.get('host')}"
        )

    selection = typer.prompt("Select target number", type=int)

    if selection < 1 or selection > len(targets):
        console.print("[red]Invalid target selection.[/]")
        return

    index = selection - 1
    current = targets[index]

    name = typer.prompt("Target name", default=current.get("name", ""))
    existing_tag = current.get("tag") or ""
    tag = typer.prompt(
        "Friendly tag/alias",
        default=existing_tag,
        show_default=bool(existing_tag),
    )
    host = typer.prompt("vCenter/ESXi host", default=current.get("host", ""))

    current_type = current.get("type", "vcenter")

    console.print("\nTarget type:")
    console.print("1. vCenter")
    console.print("2. ESXi")

    default_type_choice = "1" if current_type == "vcenter" else "2"
    type_choice = typer.prompt(
        "Select target type",
        default=default_type_choice,
    )

    while type_choice not in ("1", "2"):
        console.print("[yellow]Select 1 or 2.[/]")
        type_choice = typer.prompt(
            "Select target type",
            default=default_type_choice,
        )

    ttype = "vcenter" if type_choice == "1" else "esxi"

    default_user = (
        current.get("username")
        or ("administrator@vsphere.local" if ttype == "vcenter" else "root")
    )
    username = typer.prompt("Username", default=default_user)
    port = typer.prompt("Port", default=current.get("port", 443), type=int)
    verify_ssl = typer.confirm(
        "Verify TLS certificate?",
        default=current.get("verify_ssl", True),
    )

    updated = {
        "name": name,
        "tag": tag,
        "host": host,
        "type": ttype,
        "username": username,
        "port": port,
        "verify_ssl": verify_ssl,
    }

    original = CONFIG_FILE.read_text(encoding="utf-8")
    old_name = current.get("name")

    old_password = None
    try:
        current_config = load_config(CONFIG_FILE)
        old_password = current_config.get_target(old_name).password
    except Exception:
        pass

    targets[index] = updated
    raw["targets"] = targets

    CONFIG_FILE.write_text(
        yaml.safe_dump(raw, sort_keys=False),
        encoding="utf-8",
    )

    try:
        load_config(CONFIG_FILE)
    except Exception as exc:
        CONFIG_FILE.write_text(original, encoding="utf-8")
        console.print(f"[red]Target not updated:[/] {exc}")
        return

    password_changed = False

    if typer.confirm("Change password for this target?", default=False):
        password = typer.prompt("New password", hide_input=True)
        _write_env(name, password)
        password_changed = True

    if old_name != name:
        if not password_changed and old_password:
            _write_env(name, old_password)

        _delete_env(old_name)

        console.print(
            f"[green]✓[/] Migrated credentials from "
            f"[cyan]{old_name}[/] to [cyan]{name}[/]."
        )

    console.print(
        f"[green]✓[/] Updated target [cyan]{name}[/] "
        f"with tag [cyan]{tag}[/]."
    )


def _remove_target() -> None:
    """Remove an existing VMware target interactively."""
    import yaml

    if not CONFIG_FILE.exists():
        console.print("[yellow]No configuration file exists yet.[/]")
        return

    raw = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    targets = raw.get("targets", [])

    if not targets:
        console.print("[yellow]No VMware targets are configured.[/]")
        return

    console.print("\n[bold]Configured targets:[/]")
    for idx, target in enumerate(targets, start=1):
        label = target.get("tag") or target.get("name")
        console.print(
            f"{idx}. {target.get('name')} "
            f"[{label}] — {target.get('host')}"
        )

    selection = typer.prompt("Select target number to remove", type=int)

    if selection < 1 or selection > len(targets):
        console.print("[red]Invalid target selection.[/]")
        return

    index = selection - 1
    target = targets[index]

    if not typer.confirm(
        f"Remove target '{target.get('name')}'?",
        default=False,
    ):
        console.print("[yellow]Removal cancelled.[/]")
        return

    removed = targets.pop(index)
    raw["targets"] = targets

    CONFIG_FILE.write_text(
        yaml.safe_dump(raw, sort_keys=False),
        encoding="utf-8",
    )

    _delete_env(removed.get("name", ""))

    console.print(
        f"[green]✓[/] Removed target [cyan]{removed.get('name')}[/]."
    )
    console.print("[green]✓[/] Removed its stored password entry.")


def _set_target_tag() -> None:
    """Set or change only the friendly tag/alias of an existing target."""
    import yaml

    if not CONFIG_FILE.exists():
        console.print("[yellow]No configuration file exists yet.[/]")
        return

    raw = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    targets = raw.get("targets", [])

    if not targets:
        console.print("[yellow]No VMware targets are configured.[/]")
        return

    console.print("\n[bold]Configured targets:[/]")
    for idx, target in enumerate(targets, start=1):
        current_tag = target.get("tag") or "-"
        console.print(
            f"{idx}. {target.get('name')} "
            f"[tag: {current_tag}] — {target.get('host')}"
        )

    selection = typer.prompt("Select target number", type=int)

    if selection < 1 or selection > len(targets):
        console.print("[red]Invalid target selection.[/]")
        return

    index = selection - 1
    current = targets[index]

    tag = typer.prompt(
        "Friendly tag/alias",
        default=current.get("tag") or "",
        show_default=bool(current.get("tag")),
    ).strip()

    original = CONFIG_FILE.read_text(encoding="utf-8")

    current["tag"] = tag
    targets[index] = current
    raw["targets"] = targets

    CONFIG_FILE.write_text(
        yaml.safe_dump(raw, sort_keys=False),
        encoding="utf-8",
    )

    try:
        load_config(CONFIG_FILE)
    except Exception as exc:
        CONFIG_FILE.write_text(original, encoding="utf-8")
        console.print(f"[red]Tag not updated:[/] {exc}")
        return

    if tag:
        console.print(
            f"[green]✓[/] Target [cyan]{current.get('name')}[/] "
            f"tag set to [cyan]{tag}[/]."
        )
    else:
        console.print(
            f"[green]✓[/] Tag removed from target "
            f"[cyan]{current.get('name')}[/]."
        )


def _test_connections() -> None:
    """Run the existing VMware Knight doctor checks."""
    from vmware_knight.doctor import run_doctor

    console.print("\n[bold cyan]Running VMware connection checks...[/]\n")
    run_doctor()


def _configure_mcp_client() -> None:
    """Configure VMware Knight for Claude Desktop or Codex."""

    from vmware_knight.cli.mcp_config import mcp_config_install

    console.print("\n[bold]MCP Clients[/]")
    console.print("1. Claude Desktop")
    console.print("2. Codex")
    console.print("3. Back")

    choice = typer.prompt("Select a client", default="1")

    if choice == "1":
        agent = "claude"
    elif choice == "2":
        agent = "codex"
    elif choice == "3":
        return
    else:
        console.print("[yellow]Select 1, 2, or 3.[/]")
        return

    executable = typer.prompt(
        "VMware Knight executable path",
        default=str(
            __import__("pathlib").Path.home()
            / ".local"
            / "bin"
            / "vmware-knight"
        ),
    )

    if not typer.confirm(
        f"Install VMware Knight MCP configuration for {agent}?",
        default=True,
    ):
        console.print("[yellow]Cancelled.[/]")
        return

    mcp_config_install(
        agent=agent,
        install_path=executable,
        yes=True,
    )


def run_wizard() -> int:
    """Run the interactive VMware Knight management wizard."""

    while True:
        console.print("\n[bold cyan]VMware Knight Management Wizard[/]")
        console.print(f"[dim]Config: {CONFIG_FILE}[/]\n")

        console.print("1. List VMware targets")
        console.print("2. Add VMware target")
        console.print("3. Edit VMware target")
        console.print("4. Remove VMware target")
        console.print("5. Set/Change target tag")
        console.print("6. Test connections")
        console.print("7. Configure MCP clients")
        console.print("8. Exit")

        choice = typer.prompt("Select an option", default="1")

        if choice == "1":
            _list_targets()
        elif choice == "2":
            _add_target()
        elif choice == "3":
            _edit_target()
        elif choice == "4":
            _remove_target()
        elif choice == "5":
            _set_target_tag()
        elif choice == "6":
            _test_connections()
        elif choice == "7":
            _configure_mcp_client()
        elif choice == "8":
            console.print("[green]Exiting wizard.[/]")
            return 0
        else:
            console.print("[yellow]Select a number from 1 to 8.[/]")
