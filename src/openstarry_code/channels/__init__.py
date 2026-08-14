"""openstarry_code.channels — Channel adapter layer.

Adapters: Terminal, WebSocket, Slack, Feishu, Discord, Telegram.
"""

from openstarry_code.channels.discord import DiscordChannel
from openstarry_code.channels.feishu import FeishuChannel
from openstarry_code.channels.manager import ChannelManager
from openstarry_code.channels.slack import SlackChannel
from openstarry_code.channels.telegram import TelegramChannel, TelegramChannelConfig
from openstarry_code.channels.terminal import TerminalChannel
from openstarry_code.channels.types import (
    Attachment,
    Channel,
    ChannelHealth,
    ChannelMeta,
    IncomingMessage,
    ManagedChannel,
    OutgoingMessage,
)
from openstarry_code.channels.websocket import WebSocketChannel

__all__ = [
    # Protocol + types
    "Channel",
    "ManagedChannel",
    "ChannelHealth",
    "ChannelMeta",
    "IncomingMessage",
    "OutgoingMessage",
    "Attachment",
    # Manager
    "ChannelManager",
    # Adapters
    "TerminalChannel",
    "WebSocketChannel",
    "SlackChannel",
    "FeishuChannel",
    "DiscordChannel",
    "TelegramChannel",
    "TelegramChannelConfig",
]
