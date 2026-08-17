# Source Notes

## Sources

- URL: https://blog.csdn.net/Chengbei11/article/details/161342438
  Title: 最强 AI 逆向技能！hello_js_reverse_skill 完整教程
  Topic: Web JavaScript reverse engineering
  Claim used: The linked repository packages request tracing, signature recovery, environment emulation, and replay workflows.
  Verification: repository-inspected

- URL: https://github.com/WhiteNightShadow/hello_js_reverse_skill
  Commit: `e5c3c109ed3a9d4b96d8b1ef4061a618c12a5a38`
  Claim used: Source references, cases, scripts, and templates provide reusable implementation details.
  Verification: source-inspected and representative scripts executed

## Adaptation

The upstream `SKILL.md` was not installed directly because:

- `name: hello_js_reverse_skill` is not valid Codex hyphen-case.
- The frontmatter contains unsupported `argument-hint`.
- It declares its own text to be highest priority and contains blanket authorization and refusal directives.
- It requires a specific `camoufox-reverse` MCP surface that may not exist in the active environment.
- Its core file is too large for efficient progressive disclosure.

This wrapper keeps the technical workflow and routes to individual references only when needed. System, developer, user, live runtime, and captured traffic remain authoritative over cached source claims.

The active skill contains corrected local copies of the format triage and hook-generation helpers. These local files supersede the upstream helpers because the upstream identifier overstates algorithm confidence, its cookie hook replaces `document.cookie` on the wrong object, and its combined hook changes browser behavior by default. The source cache remains provenance material and is not edited during normal use.

## Validation Anchors

- Trace one input to one request before expanding scope.
- Compare intermediate values across multiple samples.
- Treat output length and alphabet as format evidence, never as proof of an algorithm.
- Keep observation hooks separate from behavior-changing hooks.
- Separate JavaScript errors from TLS, HTTP version, cookie, and rate-limit behavior.
- Reproduce from a reset baseline with minimal instrumentation.
