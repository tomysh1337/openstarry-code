# Group Rules

Groups overlap only when a skill genuinely owns more than one domain. Classification uses exact names, stable prefixes, and bounded phrases. It must not use arbitrary substring matches.

## Priority

1. Exact installed skill name
2. Competition downstream constraint
3. Explicit app connection or skill discovery intent
4. Security or reverse-engineering behavior
5. Cloud, infrastructure, or operations behavior
6. Frontend, accessibility, or visual behavior
7. Scientific computing, statistics, experiments, or data analysis
8. Documents, research, or structured reporting
9. Marketing, content, SEO, or conversion work
10. Product planning, requirements, roadmap, or task tracking
11. Engineering fallback

An `automation-catalog` result moves ahead only when the request explicitly asks to find a skill, connect an app, call a SaaS integration, publish externally, or automate an action.

## Precision Rules

Do not use these bare terms to decide a group:

`ui`, `api`, `art`, `auth`, `web`, `app`, `design`, `analysis`, `research`, `workflow`, `catalog`, `automation`, `cloud`, `agent`, `builder`

They may contribute to search relevance, but grouping requires a more specific name, prefix, or phrase.

Examples:

- `aws-s3-bucket-hardening` belongs to `cloud-ops` and `security-reverse`, not frontend.
- `accessibility-a11y-checklist` belongs to `frontend-creative`, not cloud.
- `ssrf-filter-bypass-catalog` belongs to `security-reverse`, despite its suffix.
- `acme-dns01-automation` belongs to `cloud-ops`, not the SaaS catalog.
- `competition-*` entries remain in `security-reverse`.
- Composio source-cache entries remain in `automation-catalog` so they do not flood other groups.
- Scientific libraries and experiment workflows use `science-data`; prose-only reports stay in `docs-research`.
- Campaign, SEO, copy, and conversion workflows use `marketing-content`; generic writing stays in `docs-research`.
- Plans, PRDs, roadmaps, and requirements use `planning-product`; implementation stays in `engineering`.

## Source Preference

Search installed skills first. Search source caches only when the installed result is missing or materially weaker.

Source-cache entries retain capability coverage without registering hundreds of frontmatter records globally. Read them selectively and install only validated, repeatedly useful workflows.
