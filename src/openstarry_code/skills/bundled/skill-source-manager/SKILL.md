---
name: skill-source-manager
description: Inventory, refresh, audit, and selectively stage external Codex skill sources without bulk-registering them. Use when downloading skill repositories, updating skill-sources, checking provenance or duplicates, validating frontmatter and scripts, generating a source report, or deciding which cached skills to install. Trigger on skill source, skill cache, audit skills, sync skills, 技能来源, 技能缓存, 技能审计, 更新技能库, 去重技能, or 精选安装.
---

# Skill Source Manager

Keep source caches separate from active skills and promote only reviewed entries.

## Inventory

```powershell
py -3 scripts/source_inventory.py --json
py -3 scripts/source_inventory.py --query "scientific visualization"
```

The inventory discovers every child directory under
`$CODEX_HOME/skill-sources`, records Git provenance, and counts real `SKILL.md`
files while excluding tests and templates.

## Audit

```powershell
py -3 scripts/audit_skill.py C:\path\to\candidate --json
py -3 scripts/audit_skill.py C:\path\to\candidate --compare-root "$HOME\.codex\skills"
```

Review reported metadata, helper scripts, network references, persistence hooks,
credential handling, destructive commands, and name collisions. A report is a
triage aid; inspect decisive lines before installing.

## Refresh

```powershell
powershell -ExecutionPolicy Bypass -File scripts/sync-sources.ps1
```

Refresh uses fast-forward-only pulls for existing Git caches and snapshots the
three configured web catalogs. It never copies candidates into the active
skills directory.

## Promotion

1. Prefer an existing installed skill when capability and quality are equivalent.
2. Copy only the selected skill directory and directly required resources.
3. Normalize frontmatter to Codex fields and move long details into references.
4. Run `quick_validate.py`, compile or syntax-check helper scripts, and test routing.
5. Record source URL, commit/version, compatibility edits, and selection reason.
