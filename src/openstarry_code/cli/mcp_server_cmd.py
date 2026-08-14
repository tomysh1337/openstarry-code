"""CLI commands for running OpenStarry Code as an inbound MCP server."""

from __future__ import annotations

import typer

from openstarry_code.cli.url_utils import normalize_gateway_url

app = typer.Typer(help="Run the OpenStarry Code MCP server bridge.")


@app.command("run")
def run_mcp_server(
    gateway_url: str = typer.Option(
        "ws://localhost:18791/ws",
        "--gateway",
        envvar="OPENSTARRY_CODE_GATEWAY_URL",
        help="OpenStarry Code gateway URL to bridge to.",
    ),
) -> None:
    """Run a stdio MCP server exposing OpenStarry Code session workflows."""

    from openstarry_code.mcp_server.bridge import OpenSquillaMCPBridge
    from openstarry_code.mcp_server.server import create_mcp_server

    bridge = OpenSquillaMCPBridge(gateway_url=normalize_gateway_url(gateway_url))
    try:
        mcp = create_mcp_server(bridge)
    except RuntimeError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    mcp.run(transport="stdio")
