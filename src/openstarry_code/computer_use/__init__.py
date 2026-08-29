"""Built-in computer-use MCP server package.

Exposes the local machine (screen, keyboard, mouse) to the agent through a
humanized controller and an MCP stdio server:

* :mod:`openstarry_code.computer_use.controller` — the automation controller;
* :mod:`openstarry_code.computer_use.cursor_overlay` — the on-screen visual
  layer (cursor artwork, border glow, glass banner) so a human can follow
  what the AI is doing;
* :mod:`openstarry_code.computer_use.session` — session state persistence,
  the Esc abort event and the global keyboard hook behind it;
* :mod:`openstarry_code.computer_use.mcp_server` — the MCP stdio server
  (``python -m openstarry_code.computer_use.mcp_server``).
"""
