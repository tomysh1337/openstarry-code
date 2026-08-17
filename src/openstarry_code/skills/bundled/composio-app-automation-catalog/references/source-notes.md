# Source Notes

## Provenance

- Repository: https://github.com/ComposioHQ/awesome-claude-skills
- Branch: `master`
- Audited commit: `92568c1edaff1bde5371154f036d959346c145a8`
- Cached source: `<codex-home>/skill-sources/composiohq-awesome-claude-skills`

## Inventory

- Repository `SKILL.md` files: 864
- Independent and document skills: 32
- Generated Composio app skills: 832
- Canonical app slugs after normalization: 810
- Alias groups after `_` to `-` normalization: 22

## Compatibility Findings

The 832 generated app skills are useful workflow references but are not registered directly:

- All 832 use unsupported top-level `requires` frontmatter.
- 10 also use unsupported top-level `category`.
- 92 have non-Codex names such as capitals, spaces, underscores, leading hyphens, or digit-leading names.
- Registering every generated skill would keep hundreds of descriptions in the global skill catalog on every turn.

The router preserves all workflows in the source cache and loads one matching file only when needed.

## Alias Rule

Normalize directory and frontmatter names to lowercase hyphen form. When both underscore and hyphen variants normalize to the same slug, prefer the entry with a valid hyphenated frontmatter name, then the directory containing fewer underscores. The search script applies this rule deterministically.

Known alias families include Anthropic Administrator, Capsule CRM, Docker Hub, Fillout Forms, Google Admin/Classroom/Maps/Search Console, Lemon Squeezy, ManyChat, Microsoft Clarity, Mistral AI, New Relic, OneSignal REST API, Similarweb DigitalRank API, Wave Accounting, and six Zoho toolkits.

## Runtime Rule

Cached examples are advisory. Always discover current Rube MCP schemas at runtime and trust live tool responses over source examples.
