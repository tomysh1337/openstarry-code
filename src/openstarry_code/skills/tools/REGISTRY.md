# OpenStarry Code Skill Tool Registry

This registry describes the tool surface available to imported Skills. It is
kept beside the Skill tree so references such as `../../tools/REGISTRY.md`
remain valid after packaging.

## Built-in tool groups

- **Shell and process:** `exec_command`, `background_process`, `process`
- **Files and source:** `read_file`, `read_source`, `write_file`,
  `create_source`, `edit_file`, `edit_source`, `list_dir`, `glob_search`,
  `grep_search`, `source_symbols`, `apply_patch`
- **Git:** `git_status`, `git_diff`, `git_log`, `git_commit`
- **Web:** `web_fetch`, `http_request`, `web_search`, `web_discover`
- **Skills:** `skill_list`, `skill_view`, `skill_search_community`,
  `skill_install_community`, `install_skill_deps`, `skill_create`,
  `skill_edit`, `skill_delete`
- **Artifacts and documents:** `publish_artifact`, `create_csv`, `create_xlsx`,
  `create_pptx`, `create_pdf_report`, `pdf`
- **Media:** `image`, `image_generate`, `voice_clone`, `voice_convert`,
  `tts`, `music_generate`, `song_generate`
- **Agents and sessions:** `agents_list`, `subagents`, `sessions_spawn`,
  `sessions_send`, `sessions_list`, `sessions_history`

## Adapter policy

Skill manifests can mention host-specific names such as `Bash`, `Read`,
`Write`, `Edit`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, and `Task`. The
runtime maps those names to the built-in tools in `tool-index.md`; the Skill
does not need to ship a second copy of the runtime tool implementation.

Commands listed under a Skill's dependency metadata remain explicit host
dependencies. They are checked by the Skill dependency flow and are not
pretended to be built-in tools.

## Reverse-analysis helpers

- `reverse-toolchain.md` maps Recaf, enigma-mcp, IDA, Ghidra, Frida, JDWP,
  dynamic sandboxes, and Android tooling to the OpenStarry tool surface.
- `scripts/artifact_triage.py TARGET...` performs extension/magic-byte
  classification and emits JSON workflow stages plus suggested tools.
- `scripts/native_residue_scan.py TARGET...` scans bytes for `-3######` and
  `0x######` residues, reporting zero-based offsets as JSON for IDA/Ghidra.
