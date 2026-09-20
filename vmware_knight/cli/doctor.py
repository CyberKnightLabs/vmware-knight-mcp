"""Doctor top-level command: environment and connectivity check."""

from __future__ import annotations

from typing import Annotated

import typer

from vmware_knight.cli._common import cli_errors
from vmware_policy import audited


@cli_errors
@audited("doctor")
def doctor_cmd(
    skip_auth: Annotated[
        bool,
        typer.Option("--skip-auth", help="Skip vSphere authentication check (faster)"),
    ] = False,
) -> None:
    """Check environment, config, connectivity, and daemon status."""
    from vmware_knight.doctor import run_doctor

    exit_code = run_doctor(skip_auth=skip_auth)
    raise typer.Exit(exit_code)
