"""CLI commands for starry:// protocol handling."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from openstarry_code.cli.output import emit_error, print_json
from openstarry_code.cli.ui import ACCENT, console
from openstarry_code.protocol import (
    StarryProtocolHandler,
    ProtocolStatus,
    parse_starry_url,
    validate_parsed_url,
    ProtocolParseError,
)

protocol_app = typer.Typer(help="Handle starry:// protocol URLs for configuration and installation.")


@protocol_app.command("handle")
def protocol_handle(
    url: str = typer.Argument(..., help="The starry:// protocol URL to handle"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
    config_path: Path | None = typer.Option(None, "--config", help="Path to configuration file"),
) -> None:
    """Handle a single starry:// protocol URL.
    
    Examples:
        openstarry-code protocol handle "starry://api/import?provider=openai&key=env:OPENAI_API_KEY"
        openstarry-code protocol handle "starry://skill/install?github=openstarry/deep-research"
    """
    result = asyncio.run(_handle_url(url, config_path))
    
    if json_output:
        print_json({
            "status": result.status.value,
            "message": result.message,
            "action": result.action.value,
            "data": result.data,
            "error": result.error,
            "success": result.success,
        })
        return
    
    # 终端输出
    if result.success:
        console.print(f"[green]✅ {result.message}[/]")
        if result.data:
            _print_result_data(result.data)
    elif result.requires_confirmation:
        console.print(f"[yellow]⚠️  {result.message}[/]")
        console.print(f"[yellow]Confirmation required: {result.confirmation_token}[/]")
        if result.data:
            _print_result_data(result.data)
    else:
        console.print(f"[red]❌ {result.message}[/]")
        if result.error:
            console.print(f"[red]Error: {result.error}[/]")


@protocol_app.command("batch")
def protocol_batch(
    file: Path = typer.Argument(..., help="File containing starry:// URLs (one per line)"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
    config_path: Path | None = typer.Option(None, "--config", help="Path to configuration file"),
) -> None:
    """Handle multiple starry:// protocol URLs from a file.
    
    Example:
        openstarry-code protocol batch urls.txt
    """
    if not file.exists():
        emit_error(f"File not found: {file}", json_output=json_output, code="FILE_NOT_FOUND")
        raise typer.Exit(1)
    
    # 读取 URLs
    urls = [line.strip() for line in file.read_text().splitlines() if line.strip()]
    
    if not urls:
        emit_error("No URLs found in file", json_output=json_output, code="EMPTY_FILE")
        raise typer.Exit(1)
    
    # 批量处理
    handler = StarryProtocolHandler(config_path=config_path)
    results = asyncio.run(handler.handle_batch(urls))
    
    if json_output:
        print_json({
            "total": len(results),
            "results": [
                {
                    "url": urls[i],
                    "status": result.status.value,
                    "message": result.message,
                    "action": result.action.value,
                    "data": result.data,
                    "error": result.error,
                    "success": result.success,
                }
                for i, result in enumerate(results)
            ],
        })
        return
    
    # 终端输出
    success_count = sum(1 for r in results if r.success)
    failed_count = sum(1 for r in results if r.status == ProtocolStatus.FAILED)
    pending_count = sum(1 for r in results if r.requires_confirmation)
    
    console.print(f"\n[bold]Processed {len(results)} URLs:[/]")
    console.print(f"  [green]✅ Success: {success_count}[/]")
    console.print(f"  [yellow]⚠️  Pending: {pending_count}[/]")
    console.print(f"  [red]❌ Failed: {failed_count}[/]")
    
    # 显示详细结果
    console.print()
    for i, result in enumerate(results):
        url = urls[i]
        if result.success:
            console.print(f"[green]✅ {url}[/]")
            console.print(f"   {result.message}")
        elif result.requires_confirmation:
            console.print(f"[yellow]⚠️  {url}[/]")
            console.print(f"   {result.message}")
        else:
            console.print(f"[red]❌ {url}[/]")
            console.print(f"   {result.message}")


@protocol_app.command("validate")
def protocol_validate(
    url: str = typer.Argument(..., help="The starry:// protocol URL to validate"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Validate a starry:// protocol URL without executing it.
    
    Example:
        openstarry-code protocol validate "starry://api/import?provider=openai"
    """
    try:
        parsed = parse_starry_url(url)
        validate_parsed_url(parsed)
        
        if json_output:
            print_json({
                "valid": True,
                "scheme": parsed.scheme,
                "action": parsed.action.value,
                "params": parsed.params,
            })
            return
        
        console.print(f"[green]✅ Valid protocol URL[/]")
        console.print(f"  Scheme: {parsed.scheme}://")
        console.print(f"  Action: {parsed.action.value}")
        console.print(f"  Parameters:")
        for key, value in parsed.params.items():
            # 隐藏敏感信息
            if "key" in key.lower() or "token" in key.lower():
                value = "***"
            console.print(f"    {key} = {value}")
    
    except ProtocolParseError as e:
        if json_output:
            print_json({
                "valid": False,
                "error": str(e),
            })
            raise typer.Exit(1)
        
        console.print(f"[red]❌ Invalid protocol URL[/]")
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


@protocol_app.command("info")
def protocol_info(
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Display information about the starry:// protocol.
    
    Example:
        openstarry-code protocol info
    """
    from openstarry_code.protocol.types import ProtocolAction
    
    actions = [
        {
            "action": ProtocolAction.API_IMPORT.value,
            "description": "Import API provider configuration",
            "example": "starry://api/import?provider=openai&key=env:OPENAI_API_KEY",
        },
        {
            "action": ProtocolAction.SKILL_INSTALL.value,
            "description": "Install a skill from GitHub, ClawHub, or local path",
            "example": "starry://skill/install?github=openstarry/deep-research",
        },
        {
            "action": ProtocolAction.EXTENSION_LOAD.value,
            "description": "Load a custom extension (Python/Java/Go)",
            "example": "starry://extension/load?path=file:///path/to/extension.py&type=python",
        },
        {
            "action": ProtocolAction.CONFIG_IMPORT.value,
            "description": "Import full configuration from URL",
            "example": "starry://config/import?url=https://example.com/config.toml",
        },
    ]
    
    if json_output:
        print_json({
            "protocol": "starry://",
            "version": "1.0",
            "actions": actions,
        })
        return
    
    console.print(Panel.fit(
        "[bold cyan]starry:// Protocol Information[/]\n\n"
        "The starry:// protocol provides a quick way to import configurations,\n"
        "install skills, and load extensions in OpenStarry Code.",
        title="Protocol Info",
        border_style=ACCENT,
    ))
    
    console.print("\n[bold]Supported Actions:[/]\n")
    
    for action_info in actions:
        console.print(f"[bold cyan]{action_info['action']}[/]")
        console.print(f"  {action_info['description']}")
        console.print(f"  [dim]Example:[/] {action_info['example']}")
        console.print()
    
    console.print("[bold]Documentation:[/]")
    console.print("  See docs/starry-protocol.md for full specification")


def _print_result_data(data: dict) -> None:
    """打印结果数据"""
    if not data:
        return
    
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    
    for key, value in data.items():
        # 隐藏敏感信息
        if "key" in key.lower() or "token" in key.lower():
            value = "***"
        elif isinstance(value, dict):
            value = str(value)
        elif isinstance(value, bool):
            value = "✓" if value else "✗"
        
        table.add_row(key, str(value))
    
    console.print(table)


async def _handle_url(url: str, config_path: Path | None) -> "ProtocolResult":
    """处理单个 URL（异步）"""
    handler = StarryProtocolHandler(config_path=config_path)
    return await handler.handle(url)
