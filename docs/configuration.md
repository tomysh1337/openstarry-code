# Configuration

OpenStarry Code can be configured from the onboarding wizard, the Web UI setup
flow, CLI commands, environment variables, and TOML files. Use CLI commands for
routine setup and edit TOML only for advanced or scripted deployments.

## Config Load Order

OpenStarry Code reads configuration in this order:

1. `OPENSQUILLA_GATEWAY_CONFIG_PATH`
2. `./openstarry-code.toml`
3. `~/.openstarry-code/config.toml`
4. built-in defaults

Use `--config ./openstarry-code.toml` when you want to write or inspect a
project-local config file.

## Task Runtime Concurrency

Fresh installations allow up to eight cross-session turns to run at once:

```toml
[task_runtime]
max_concurrency = 8
max_pending_per_session = 64
```

Eight is the desktop default because it matches the built-in channel in-flight
budget and leaves enough capacity for interactive tasks, Goal continuations,
Cron runs, and subagents without bypassing TaskRuntime's global queue. Turns in
the same session remain serialized. Provider pressure is still handled by the
configured credential pool, provider health/fallback policy, and `Retry-After`
cooldowns; this setting does not manufacture extra credentials or disable
provider rate limiting.

This is a default change, not a migration. An existing TOML value such as
`max_concurrency = 4`, or an explicit
`OPENSQUILLA_TASK_MAX_CONCURRENCY=4`, remains authoritative after upgrade.

## Secret Handling

Prefer environment-variable references for secrets:

```sh
export OPENROUTER_API_KEY="sk-..."
openstarry-code configure provider --provider openrouter --api-key-env OPENROUTER_API_KEY
```

Avoid committing raw API keys to TOML files, shell history, examples, or issue
reports.

## First-Run Wizard

```sh
openstarry-code onboard
```

Common options:

```sh
openstarry-code onboard --if-needed
openstarry-code onboard --minimal
openstarry-code onboard --provider openrouter --api-key-env OPENROUTER_API_KEY
openstarry-code onboard --provider openai --model gpt-5.4-mini --api-key-env OPENAI_API_KEY
openstarry-code onboard --provider ollama --model llama3.1
openstarry-code onboard status
```

The router mode defaults to `recommended`. Use `--router disabled` when you want
direct single-model routing.

## Reconfigure One Section

The `configure` command edits a selected section:

```sh
openstarry-code configure provider --provider openrouter --api-key-env OPENROUTER_API_KEY
openstarry-code configure router --router recommended
openstarry-code configure router --router openrouter-mix
openstarry-code configure router --router disabled
openstarry-code configure search --search-provider duckduckgo
openstarry-code configure search --search-provider tavily --api-key-env TAVILY_API_KEY
openstarry-code configure channels
openstarry-code configure image-generation
openstarry-code configure memory-embedding
```

Supported sections:

- `provider`
- `router`
- `channels`
- `search`
- `image-generation`
- `memory-embedding`

## Configuration Decision Table

| Need | Preferred command |
| --- | --- |
| First setup | `openstarry-code onboard` |
| CI or install scripts | `openstarry-code onboard --if-needed` |
| Change provider | `openstarry-code configure provider ...` |
| Enable or disable routing | `openstarry-code configure router ...` |
| Configure web search | `openstarry-code configure search ...` |
| Configure messaging platforms | `openstarry-code configure channels` |
| Inspect current values | `openstarry-code config get` |
| Persist an advanced key | `openstarry-code config set <key> <value> --config <path>` |

## Tool Policy

Advanced scripted runs can narrow the model-visible tool surface with `[tools]`.
To compare tool surfaces across otherwise identical runs, keep the calling
harness unchanged and express the tool difference in config:

```toml
[tools]
profile = "coding"
also_allow = ["retrieve_tool_result"]
deny = ["execute_code", "background_process", "process"]
file_edit_requires_fresh_read = true
file_edit_flexible_recovery = true
```

`profile = "coding"` keeps filesystem, search, shell, session, and memory tools
available, and enables fresh `read_file` context before existing workspace file
edits. The `deny` list above removes the extra Python/background process
surfaces for a narrowed run; omit it for the default coding surface.
`file_edit_flexible_recovery` defaults to `true`: after an exact `old_text`
miss, `edit_file` may apply a unique whitespace/indentation recovery and records
used or rejected recovery events for diagnostics.

## Provider Configuration

Inspect provider support:

```sh
openstarry-code providers list
openstarry-code providers configure openrouter
openstarry-code providers status
```

Onboarding-verified providers include:

- TokenRhythm
- OpenRouter
- OpenAI
- Anthropic
- Ollama
- DeepSeek
- Gemini
- DashScope / Qwen
- Moonshot AI
- Zhipu / Z.AI
- Baidu Qianfan
- Volcengine Ark

OpenStarry Code also carries provider registry entries for additional
OpenAI-compatible or self-hosted backends. Use `openstarry-code providers list` on
your install to see the current catalog.

Read: [`providers-and-models.md`](providers-and-models.md)

## Router Configuration

Router modes:

| Mode | Use when |
| --- | --- |
| `recommended` | You want the selected provider's default routing profile. |
| `openrouter-mix` | You want OpenRouter mixed-model defaults. |
| `disabled` | You want one configured provider/model for every turn. |

Commands:

```sh
openstarry-code configure router --router recommended
openstarry-code configure router --router openrouter-mix
openstarry-code configure router --router disabled
```

Router-supported provider profiles depend on the installed build and configured
provider. Read [`features/squilla-router.md`](features/squilla-router.md) before
using direct model runs for evaluation.

## Search Configuration

Inspect search providers:

```sh
openstarry-code search list
openstarry-code search status
openstarry-code search query "OpenStarry Code release notes"
```

Configure search:

```sh
openstarry-code configure search --search-provider duckduckgo
openstarry-code configure search --search-provider bing_cn
openstarry-code configure search --search-provider baidu
openstarry-code configure search --search-provider sogou
openstarry-code configure search --search-provider bocha --api-key-env BOCHA_SEARCH_API_KEY
openstarry-code configure search --search-provider brave --api-key-env BRAVE_SEARCH_API_KEY
openstarry-code configure search --search-provider tavily --api-key-env TAVILY_API_KEY
openstarry-code configure search --search-provider exa --api-key-env EXA_API_KEY
openstarry-code configure search --search-provider iqs --api-key-env IQS_SEARCH_API_KEY
```

Runtime-supported search providers in this build include DuckDuckGo, Bing China,
Baidu, Sogou, Bocha, Brave Search, Alibaba Cloud IQS, Tavily, and Exa.
DuckDuckGo, Bing China, Baidu, and Sogou are no-key paths.
A partial-key setup can configure only one keyed provider; an all-key setup can
expose `BOCHA_SEARCH_API_KEY`, `BRAVE_SEARCH_API_KEY`, `IQS_SEARCH_API_KEY`,
`TAVILY_API_KEY`, and `EXA_API_KEY` so runtime provider selection can choose by
mode and capability unless a request names an explicit provider.
`search_provider` is the credential
anchor for `search_api_key` and `search_api_key_env`; it is not a hard routing
promise for automatic searches.
Additional provider metadata may be present for future or
not-yet-runtime-supported integrations.

Read: [`search.md`](search.md)

## Channel Configuration

List supported channel types:

```sh
openstarry-code channels types --json
openstarry-code channels describe feishu
openstarry-code channels add telegram --name personal
openstarry-code channels status
```

Channel saves update configuration. Restart the gateway after edits:

```sh
openstarry-code gateway restart
openstarry-code channels status <name> --json
```

See [`channels.md`](channels.md) for details.

## Attachments

Attachment ingestion accepts **any file type**. Rendered families (images,
PDF, text, Office documents, email) are extracted or inlined for the model;
everything else is an *opaque* attachment: the bytes are staged into the agent
workspace for tool access and are never parsed, decompressed, or inlined into
a provider prompt.

```toml
[attachments]
# Admit opaque (non-rendered) attachment types: archives, binaries,
# audio/video, unknown formats. false restores the legacy fail-closed
# rendered-types-only admission gate on every surface.
accept_opaque = true
# Per-file ceiling for opaque attachments (bytes).
opaque_max_bytes = 31457280            # 30 MiB
# Aggregate RAM ceiling for the in-memory staged-upload store. When reached,
# new uploads get HTTP 507 UPLOAD_STORE_FULL (retryable; staged entries
# expire within the 10-minute TTL); a payload larger than the cap itself is a
# permanent 413. Non-positive or invalid values fall back to the default —
# this cap can be raised but not disabled. Requires a gateway restart.
upload_store_max_total_bytes = 314572800    # 300 MiB
# Disk budget for attachment copies materialized into an agent workspace
# (<workspace>/.openstarry-code/attachments). When exceeded, new materializations
# degrade to an unavailable marker; existing files are never evicted. Set to
# 0 (or any non-positive value) to disable the budget entirely.
workspace_attachment_disk_budget_bytes = 1073741824  # 1 GiB
# Persist attachment bytes with session transcripts.
persist_transcripts = true
# media_root = ""                      # default: resolved from the cache dir
transcript_disk_budget_bytes = 2147483648   # 2 GiB
artifact_max_bytes = 31457280               # 30 MiB
artifact_disk_budget_bytes = 536870912      # 512 MiB
```

Env overrides use the `OPENSQUILLA_ATTACHMENTS_` prefix
(`OPENSQUILLA_ATTACHMENTS_ACCEPT_OPAQUE`, `OPENSQUILLA_ATTACHMENTS_OPAQUE_MAX_BYTES`, …).

Size policy at a glance: inline attachments up to 2 MB ride the RPC message;
larger files stage through `POST /api/v1/files/upload` (10-minute TTL) up to
30 MiB per file for text (whole-payload UTF-8 proven), PDF, Office, and opaque
types. Email is always capped at the 2 MB text limit and never stages. Per
turn: at most 10 attachments and 60 MiB total.

Behavior notes:

- With `accept_opaque = true` (the default), the upload endpoint no longer
  returns HTTP 415 `UNSUPPORTED_MEDIA_TYPE` for unrendered types, and
  `sessions.send` no longer rejects them; strict deployments that disable the
  flag keep the legacy errors and codes unchanged.
- Opaque files reach the model only as an escaped metadata envelope plus a
  workspace path marker; the agent inspects or converts them with filesystem,
  shell, or code tools under the active safety tier and approval policy. On
  platforms without a sandbox backend those tool actions rely on approvals.

## Memory Configuration

Useful commands:

```sh
openstarry-code memory status
openstarry-code memory index
openstarry-code memory list
openstarry-code memory search "project preference"
openstarry-code memory show <path>
openstarry-code memory dream
openstarry-code memory flush-session <session-key>
```

Configure embedding behavior:

```sh
openstarry-code configure memory-embedding
```

Memory can combine Markdown-backed sources with SQLite keyword and semantic
indexes. The exact memory shape depends on the configured provider and local
embedding support.

Read: [`features/memory.md`](features/memory.md)

## Sandbox and Permissions

Inspect or change posture:

```sh
openstarry-code sandbox status
openstarry-code sandbox on
openstarry-code sandbox full
openstarry-code sandbox bypass
openstarry-code sandbox reset
```

Single-shot automation permissions:

```sh
openstarry-code agent --permissions restricted -m "Read the repo and summarize it"
openstarry-code agent --permissions full -m "Make a local patch and run tests"
```

For unattended automation that must stay inside a workspace:

```sh
openstarry-code agent \
  --workspace /path/to/project \
  --workspace-lockdown \
  --scratch-dir /path/to/project/.scratch \
  -m "Investigate and propose the smallest fix"
```

Read: [`tools-and-sandbox.md`](tools-and-sandbox.md)

## Outbound URL Filtering And Fake-IP DNS

URL-fetching tools validate resolved addresses through the shared SSRF guard in
`openstarry_code.tools.ssrf`. Private, loopback, link-local, and reserved ranges are
blocked by default.

Some trusted proxy or fake-IP DNS setups resolve public hostnames such as
`github.com` to addresses in the RFC 2544 benchmark range `198.18.0.0/15`.
OpenStarry Code keeps blocking those addresses unless the operator explicitly opts
in:

```toml
[tools]
trusted_fake_ip_cidrs = ["198.18.0.0/15"]
```

Only subnets of `198.18.0.0/15` are accepted in this setting. Loopback, RFC
1918 private ranges, link-local addresses, and other internal ranges remain
hard-blocked even if configured. If a public hostname resolves to one of those
hard-blocked ranges, fix the DNS or proxy setup instead of bypassing the guard.

## Gateway Binding

The desktop application always owns a loopback-only child Gateway bound to
`127.0.0.1`. Desktop settings do not change its listener address or expose it
to the LAN. The settings below apply to a separately launched standalone
Gateway.

Foreground:

```sh
openstarry-code gateway run --listen 127.0.0.1 --port 18791
```

Managed:

```sh
openstarry-code gateway start --json
openstarry-code gateway status
openstarry-code gateway stop
openstarry-code gateway restart
```

Bind precedence:

1. `--listen`
2. `--bind`
3. `OPENSQUILLA_LISTEN`
4. `OPENSQUILLA_GATEWAY_HOST`
5. config host
6. `127.0.0.1`

When listening on the LAN, OpenStarry Code accepts only loopback, RFC 1918, and
IPv6 ULA socket peers. `auth.allowed_client_cidrs` can narrow that built-in
range but cannot add public networks:

```toml
host = "0.0.0.0"

[auth]
mode = "token"
allowed_client_cidrs = ["192.168.50.0/24"]
```

Missing, malformed, and incorrect tokens receive guest-safe authority only.
A valid named token with `host.execute` may select Full Access without gaining
owner-only settings authority.

For a remote Web guest, the server ignores any client-supplied workspace and
uses the configured default workspace. All file-capable tools follow the same
non-bypassable policy:

- ordinary host files are readable;
- the built-in credential paths and OpenStarry Code authority/recovery data are
  not readable;
- writes are allowed only inside the configured default workspace;
- workspace creation, selection, and other owner-only lifecycle operations are
  unavailable.

These restrictions also apply to Shell, Python, Node.js, Git Bash, and their
child processes. Guests cannot access the global approval queue, and approvals
cannot elevate a guest past this boundary. The Gateway refuses Guest Safe
startup when the configured default workspace is inside a protected credential
or authority path.

## Safe Mode Policy

Settings -> Sandbox persists a versioned policy snapshot for each new task.
Ordinary host files are readable and writable in Safe mode, except OpenStarry Code
authority/recovery data and the built-in or custom deny-write paths. Mutating a
deny-write path requires an exact user approval.

Recursive directory deletion always requires a dedicated irreversible-action
confirmation. Backups are enabled by default with a 3 GiB quota; oldest
backups are evicted first. A target larger than the quota requires a second,
explicit confirmation to delete without a backup.

Commands run automatically unless a built-in high-risk rule or a configured
approval prefix matches. An auto-allow prefix takes precedence over approval
rules. Network access is public by default through the managed boundary, with
SSRF and local metadata protections; operators can deny domains, allow
exceptions, or block all network access.

## Goal Mode (`[goal]`)

Session-level `/goal` mode drives the agent toward a fixed goal turn after turn
until it completes, blocks, pauses, reaches a provider usage limit, or hits a
guardrail. Automatic turns use the same TaskRuntime, TurnRunner, sandbox,
approval, provider, and usage-accounting path as ordinary turns. All fields
below are optional; absent keys keep the defaults.

| Field | Default | Meaning |
| --- | --- | --- |
| `execution_enabled` | `true` | Emergency kill switch. When false, no new Goal execution is accepted and unfinished active Goals pause. |
| `max_turns` | `50` | Per-resume-window turn limit (`1`-`500`). The current turn finishes first; an otherwise active Goal then pauses with `turn_limit`. |
| `runtime_budget_seconds` | `3600` | Per-resume-window active running-time limit (`60`-`86400` seconds). Queue time, pauses, and Gateway downtime do not count. An otherwise active Goal pauses with `runtime_limit`. |

```toml
[goal]
execution_enabled = true
max_turns = 50
runtime_budget_seconds = 3600
```

`/goal resume` resets the current guardrail window while retaining lifetime
turn, active-time, and token totals. Goal mode does not replay a failed or timed
out whole turn: tools may already have produced side effects. Provider/core
request retries remain governed by their existing policies.

An execution lease belongs to the subscribed Web UI or CLI connection that
started or resumed the Goal. Losing that client connection detaches the lease:
the Goal stays active, its current accepted turn may finish, and no new
automatic continuation starts until an authorized client reattaches. A Web UI
refresh reattaches with a tab-local continuity token; an explicit takeover is
available when that token was lost. Disabling execution or restarting the
Gateway still pauses unattended work. Read the complete workflow, state model,
Plan-mode interaction, upgrade notes, and recovery guidance in
[`goal-mode.md`](goal-mode.md).

## Raw Config Editing

For advanced settings, inspect `openstarry-code.toml.example` and edit the active
config file directly. Use CLI commands for routine provider, router, search,
channel, and sandbox changes because they avoid common key-shape mistakes.

After changing files by hand, restart the gateway and run:

```sh
openstarry-code doctor
openstarry-code gateway status
```

---

[Docs index](README.md) · [Product guide](../README.product.md) · [Improve this page](contributing-docs.md) · [Report a docs issue](https://github.com/tomysh1337/openstarry-code/issues/new?template=docs_report.yml)
