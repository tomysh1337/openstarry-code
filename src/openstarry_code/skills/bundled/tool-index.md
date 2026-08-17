# OpenStarry Code Tool Index

This file is the stable tool map for imported Codex skills. Skill instructions
should use the OpenStarry Code names below instead of assuming a host-specific
tool namespace.

## Core tools

| Skill-facing capability | OpenStarry Code tool |
| --- | --- |
| Run a foreground command | `exec_command` |
| Start or inspect a long-running command | `background_process`, `process` |
| Read a text or source file | `read_file`, `read_source` |
| Write or create a file | `write_file`, `create_source` |
| Apply a focused source patch | `edit_file`, `edit_source`, `apply_patch` |
| List files or find paths | `list_dir`, `glob_search` |
| Search file contents | `grep_search` |
| Inspect source symbols | `source_symbols` |
| Git status, diff, log, commit | `git_status`, `git_diff`, `git_log`, `git_commit` |
| Fetch a URL | `web_fetch`, `http_request` |
| Search the web | `web_search`, `web_discover` |
| Delegate a task | `subagents`, `sessions_spawn` |
| Inspect or invoke a Skill | `skill_list`, `skill_view`, `skill_search_community` |
| Install Skill dependencies | `install_skill_deps` |
| Generate or inspect media | `image_generate`, `pdf`, `create_pdf_report`, `create_xlsx`, `create_pptx` |

## Common compatibility names

Imported manifests may use generic names from Codex or Claude-style hosts:

| Imported name | OpenStarry Code mapping |
| --- | --- |
| `Bash` / `exec_command` | `exec_command` |
| `Read` | `read_file` or `read_source` |
| `Write` | `write_file` or `create_source` |
| `Edit` / `apply_patch` | `edit_file`, `edit_source`, or `apply_patch` |
| `Glob` | `glob_search` |
| `Grep` | `grep_search` |
| `WebFetch` | `web_fetch` |
| `WebSearch` | `web_search` |
| `Task` | `subagents` or `sessions_spawn` |

## External command dependencies

Skill scripts may additionally probe host executables such as `git`, `rg`,
`node`, `npm`, `python`, `uv`, `ffmpeg`, `pandoc`, `java`, `jadx`, `adb`, or
`docker`. These are optional command dependencies and are not silently replaced
by a different executable. A Skill should report the missing command through
its normal dependency check before invoking it.
