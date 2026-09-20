"""MCP config generator commands: generate, list, install."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from vmware_knight.cli._common import cli_errors, console
from vmware_policy import cli_local

mcp_config_app = typer.Typer(help="Generate MCP server config for local AI agents.")

_AGENT_TEMPLATES = {
    "claude": "native",
    "codex": "native",
}


_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "examples" / "mcp-configs"

# Default install destinations for each agent
_AGENT_INSTALL_PATHS: dict[str, Path] = {
    "claude": Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    "codex": Path.home() / ".codex" / "config.toml",
}



@mcp_config_app.command("generate")
@cli_errors
@cli_local("writes or lists local MCP client config files")
def mcp_config_generate(
    agent: Annotated[
        str,
        typer.Option(
            "--agent",
            "-a",
            help="Target agent: claude or codex",
        ),
    ],
    install_path: Annotated[
        str | None,
        typer.Option("--path", help="Absolute path to VMware Knight executable"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write config to this file path"),
    ] = None,
) -> None:
    """Generate native MCP config for Claude or Codex."""

    agent_lower = agent.lower()

    if agent_lower not in _AGENT_TEMPLATES:
        console.print(
            f"[red]Unknown agent '{agent}'. Available: claude, codex[/]"
        )
        raise typer.Exit(1)

    executable = (
        str(Path(install_path).expanduser().resolve())
        if install_path
        else str(Path.home() / ".local" / "bin" / "vmware-knight")
    )

    if agent_lower == "claude":
        content = json.dumps(
            {
                "mcpServers": {
                    "vmware-knight": {
                        "command": executable,
                        "args": ["mcp"],
                    }
                }
            },
            indent=2,
        ) + "\n"

    else:
        content = (
            "[mcp_servers.vmware-knight]\n"
            f'command = "{executable}"\n'
            'args = ["mcp"]\n'
            "enabled = true\n"
            "startup_timeout_sec = 120\n"
        )

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        console.print(f"[green]Config written to: {output}[/]")
    else:
        console.print(content)


@mcp_config_app.command("list")
@cli_errors
@cli_local("writes or lists local MCP client config files")
def mcp_config_list() -> None:
    """List all supported agents."""
    table = Table(title="Supported Agents")
    table.add_column("Agent", style="cyan")
    table.add_column("Config Type")

    table.add_row("claude", "Claude Desktop JSON")
    table.add_row("codex", "Codex TOML")

    console.print(table)


@mcp_config_app.command("install")
@cli_errors
@cli_local("writes or lists local MCP client config files")
def mcp_config_install(
    agent: Annotated[
        str,
        typer.Option(
            "--agent",
            "-a",
            help="Target agent: claude or codex",
        ),
    ],
    install_path: Annotated[
        str | None,
        typer.Option("--path", help="Absolute path to VMware Knight executable"),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Install vmware-knight into Claude Desktop or Codex."""

    agent_lower = agent.lower()

    if agent_lower not in _AGENT_TEMPLATES:
        console.print(
            f"[red]Unknown agent '{agent}'. Available: claude, codex[/]"
        )
        raise typer.Exit(1)

    executable = (
        str(Path(install_path).expanduser().resolve())
        if install_path
        else str(Path.home() / ".local" / "bin" / "vmware-knight")
    )

    dest = _AGENT_INSTALL_PATHS[agent_lower]

    console.print(f"[bold]Agent:[/] {agent_lower}")
    console.print(f"[bold]Install path:[/] {dest}")
    console.print(f"[bold]Executable:[/] {executable}")

    if not yes:
        if not typer.confirm("Install vmware-knight MCP configuration?"):
            console.print("[yellow]Cancelled.[/]")
            raise typer.Exit(0)

    dest.parent.mkdir(parents=True, exist_ok=True)

    if agent_lower == "claude":
        if dest.exists():
            try:
                existing = json.loads(dest.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                console.print(f"[red]Claude config is invalid JSON: {exc}[/]")
                raise typer.Exit(1) from exc
        else:
            existing = {}

        existing.setdefault("mcpServers", {})["vmware-knight"] = {
            "command": executable,
            "args": ["mcp"],
        }

        dest.write_text(
            json.dumps(existing, indent=2) + "\n",
            encoding="utf-8",
        )

        console.print(
            f"[green]✓ Installed vmware-knight into Claude Desktop: {dest}[/]"
        )

    else:
        block = (
            "[mcp_servers.vmware-knight]\n"
            f'command = "{executable}"\n'
            'args = ["mcp"]\n'
            "enabled = true\n"
            "startup_timeout_sec = 120\n"
        )

        existing = dest.read_text(encoding="utf-8") if dest.exists() else ""

        header = "[mcp_servers.vmware-knight]"

        if header in existing:
            lines = existing.splitlines()
            output = []
            skipping = False

            for line in lines:
                stripped = line.strip()

                if stripped == header:
                    skipping = True
                    continue

                if skipping and stripped.startswith("[") and stripped.endswith("]"):
                    skipping = False

                if not skipping:
                    output.append(line)

            existing = "\n".join(output).rstrip() + "\n"

        content = existing.rstrip() + "\n\n" + block

        dest.write_text(content, encoding="utf-8")

        console.print(
            f"[green]✓ Installed vmware-knight into Codex: {dest}[/]"
        )

    console.print(
        "\n[dim]Restart the selected client so it reloads the MCP configuration.[/]"
    )
