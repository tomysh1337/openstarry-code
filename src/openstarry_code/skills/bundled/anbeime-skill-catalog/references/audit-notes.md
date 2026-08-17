# Audit Notes

## Provenance

- Repository: https://github.com/anbeime/skill
- Audited commit: `438b54b18b132e78b8e38dc6d169c6ebabb64712`
- Cached source: `<codex-home>/skill-sources/anbeime-skill`
- Repository root license: not found; some nested skills have their own licenses

## Inventory

- Git tree entries: 838
- `SKILL.md` entries: 70
- Entries with frontmatter: 67
- Unique frontmatter names: 63
- Existing local overlap at audit time: `frontend-design` only; keep the more complete local copy
- Entries passing basic Codex validation: 37
- Unique, directory-matched, non-conflicting format-ready candidates: 31

## Format-Ready Paths

```text
skills/agent-team/agent-team
skills/article-illustrator/article-illustrator
skills/content-creation-publisher/baoyu-format-markdown
skills/content-creation-publisher/baoyu-post-to-wechat
skills/content-creation-publisher/baoyu-post-to-x
skills/content-creation-publisher/baoyu-url-to-markdown
skills/bedtime-story/bedtime-story
skills/chrome-automation/chrome-automation
skills/content-research-writer
skills/legal-assistant-skills-main/contract-review
skills/data-storytelling/data-storytelling
skills/digital-avatar-shopping-video/digital-avatar-shopping-video
skills/dream-video-prompt-generator/dream-video-prompt-generator
skills/ecommerce-copywriter/ecommerce-copywriter
skills/ecommerce-video-marketing/ecommerce-video-marketing
skills/historical-interview-scripts/historical-interview-scripts
skills/infinitetalk-shopping-avatar/infinitetalk-shopping-avatar
skills/obsidian-skills-integrated/json-canvas
skills/legal-assistant-skills-main/law-to-markdown
skills/multi-agent-meeting/multi-agent-meeting
skills/obsidian-skills-integrated/obsidian-bases
skills/obsidian-skills-integrated/obsidian-markdown
skills/poetry-music-visual/poetry-music-visual
skills/pop-up-book-illustration/pop-up-book-illustration
skills/product-manager-toolkit/product-manager-toolkit
skills/product-marketing-copywriter/product-marketing-copywriter
skills/tailored-resume-generator/tailored-resume-generator
skills/video-transcript-downloader/video-transcript-downloader
skills/wechat-hotspot-publisher/wechat-hotspot-publisher
skills/wechatsync-publisher/wechatsync-publisher
skills/xiaohongshu-makeup/xiaohongshu-makeup
```

`baoyu-post-to-wechat` still references an unavailable sibling `baoyu-markdown-to-html`. `product-manager-toolkit` expects `agent-team` and `multi-agent-meeting`.

## Known Problems

- 28 entries use unsupported `dependency`; one uses unsupported `homepage`.
- One name is `PDF Processing Pro`, which is not hyphen-case.
- Three entries have no usable frontmatter.
- Four duplicate-name groups exist; three are identical copies, while the two `x-article-publisher` variants differ in behavior.
- Five gitlinks have no `.gitmodules` entry.
- About 26 internal resource references are missing.
- `video-recreation/scripts/coze_bot_client.py` has a Python syntax error.
- Four `.json` animation files under `remotion-video-enhancer` contain fenced Markdown rather than valid JSON.
- Eighteen AppleDouble or `__MACOSX` files are packaging debris.

Use invalid entries as research leads until their metadata, resources, and license are resolved.
