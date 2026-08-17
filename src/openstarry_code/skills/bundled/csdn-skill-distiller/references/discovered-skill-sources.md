# Discovered Skill Sources

This queue records CSDN articles that led to current, verifiable Skill repositories. CSDN is discovery evidence only; GitHub source, license, and runtime behavior decide whether content may be installed or adapted.

## Explicit Request

- URL: https://blog.csdn.net/Chengbei11/article/details/161342438
  Title: 最强 AI 逆向技能！hello_js_reverse_skill 完整教程
  Topic: Web JavaScript reverse engineering
  Claim used: Links `WhiteNightShadow/hello_js_reverse_skill` as a packaged reverse-engineering workflow.
  Verification: Repository has one root `SKILL.md`; no repository license metadata. Adapted as `hello-js-reverse-skill` without copying the upstream priority or authorization directives.

## High-Confidence Sources

- URL: https://blog.csdn.net/Chengbei11/article/details/160361360
  Title: Article linking Yaklang Hack Skills
  Topic: Security and CTF workflows
  Claim used: Links `yaklang/hack-skills`, including `skills/hack/SKILL.md`.
  Verification: GitHub tree contains 102 `SKILL.md` files; repository license is MIT. Check existing local coverage before installing.

- URL: https://blog.csdn.net/Chengbei11/article/details/160890904
  Title: Article linking wxmini-security-audit
  Topic: WeChat mini-program security review
  Claim used: Links `sssmmmwww/wxmini-security-audit`.
  Verification: One root `SKILL.md`; no repository license. Keep as a research lead unless the owner supplies install permission or a license.

- URL: https://blog.csdn.net/arlionn/article/details/162438150
  Title: Agent Skill ecosystem survey
  Topic: Skill catalogs
  Claim used: Links `openai/skills`, `VoltAgent/awesome-agent-skills`, and `ComposioHQ/awesome-codex-skills`.
  Verification: `openai/skills` has per-skill license files; `VoltAgent/awesome-agent-skills` is an index without local `SKILL.md` files. Treat index repositories as catalogs, not installable skills.

- URL: https://blog.csdn.net/m0_73827294/article/details/161840641
  Title: Claude Code skill repository roundup
  Topic: General coding-agent skills
  Claim used: Links several active repositories.
  Verification: `anthropics/skills` has 18 `SKILL.md` files with per-skill licenses; `obra/superpowers` has 14 under MIT; `mattpocock/skills` has 39 under MIT; `trailofbits/skills` has 75 under CC-BY-SA-4.0; `alirezarezvani/claude-skills` is a large multi-platform tree with repeated copies and requires normalization before use.

- URL: https://blog.csdn.net/zhhhhh15/article/details/158743479
  Title: Remotion skill coverage
  Topic: Programmatic video
  Claim used: Links `remotion-dev/skills`.
  Verification: Current GitHub tree contains 15 `SKILL.md` files; no repository license was found. Use as a lead, not a copy source.

- URL: https://blog.csdn.net/qq_28806349/article/details/157186590
  Title: Vercel Agent Skills overview
  Topic: React and Vercel workflows
  Claim used: Links `vercel-labs/agent-skills`.
  Verification: Current GitHub tree contains 9 `SKILL.md` files; no repository license was found. Use as a lead, not a copy source.

## Additional Verified Repositories

These repositories were corroborated through CSDN search results and current GitHub trees:

- `muratcankoylan/Agent-Skills-for-Context-Engineering`: 23 `SKILL.md`
- `antfu/skills`: 19 `SKILL.md`
- `SimoneAvogadro/android-reverse-engineering-skill`: 1 `SKILL.md`
- `wshuyi/skill-snapshot-skill`: 1 `SKILL.md`
- `KKKKhazix/Khazix-Skills`: 5 `SKILL.md`
- `GPTomics/bioSkills`: 562 `SKILL.md`; use a router because direct registration is too large
- `nextlevelbuilder/ui-ux-pro-max-skill`: 13 `SKILL.md`, including repeated packaged copies
- `op7418/Humanizer-zh`: 1 `SKILL.md`
- `comeonzhj/Auto-Redbook-Skills`: 2 `SKILL.md`
- `Ceeon/videocut-skills`: 4 `SKILL.md`
- `alchaincyf/huashu-skills`: 21 `SKILL.md`
- `mindrally/skills`: 240 `SKILL.md`; normalize and route rather than registering all
- `forrestchang/andrej-karpathy-skills`: 1 `SKILL.md`

Recheck licenses before copying. A visible article license does not grant a license to the linked repository.

## Search Method

- Search API: `https://so.csdn.net/api/v3/search?q=<query>&t=blog&p=<page>&platform=pc`
- Read canonical article URLs without tracking query parameters.
- Extract repository links, discard examples such as `owner/repo` and `yourname/*`, then verify `SKILL.md` paths through the current GitHub tree.
- Preserve URL, title, date, claim, and verification status. Do not copy article bodies.
