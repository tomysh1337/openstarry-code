---
name: humanizer
description: Edit prose to remove common AI-writing patterns while preserving every supplied fact and matching the intended voice. Use for humanize, natural rewrite, AI-sounding prose, 去除 AI 味, 降低机器感, 自然润色, or matching a provided writing sample. Do not use for code formatting or factual expansion.
metadata:
  version: "2.9.1-codex"
---

# Humanizer

Rewrite prose so it sounds like a specific person wrote it, without inventing
facts or flattening legitimate style.

## Workflow

1. Determine the mode:
   - pasted text: return a draft, a brief pattern audit, then the final rewrite;
   - file: rewrite prose in place while preserving code, frontmatter, data, and links;
   - embedded: return only the finished prose to the calling workflow.
2. If the user supplies a writing sample, match its sentence length, vocabulary,
   punctuation, paragraph rhythm, and quirks before applying generic rules.
3. Preserve every claim, name, number, date, quote, citation, and uncertainty.
   Never add plausible specifics that are absent from the source.
4. Remove clustered tells: inflated significance, promotional language, vague
   attribution, repetitive conclusions, mechanical sectioning, filler,
   over-hedging, chatbot phrases, uniform cadence, and manufactured punchlines.
5. Keep technical, legal, academic, and reference prose plain when neutrality is
   appropriate. Add personality only when the source and requested voice support it.
6. Read [references/patterns.md](references/patterns.md) only when a detailed
   pattern audit, close editing, or ambiguous false-positive review is needed.
7. Read the result aloud mentally, verify factual parity, and make a final pass
   for repeated structures and unsupported claims.

Prefer concrete verbs and varied sentence structure. Do not erase unusual detail,
mixed feelings, deliberate fragments, quotations, or era-specific language merely
because an isolated pattern resembles model-generated prose.
