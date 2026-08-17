# Local Skill Index And Routing Table

Root: `E:\DESKTOP\skill`  
Fallback bundle: `E:\download\all-skills-bundle-20260710.zip` (see `bundle-index.md`)  
Zip siblings next to unpacked dirs are **backups only**.  
New-skill inventory: `references/new-skills-inventory.md`

## How To Route

1. Classify: artifact type, protocol layer, platform, vulnerability class, requested action.
2. Pick **one primary** skill from the tables below.
3. Add a **helper** only when it supplies a different phase or toolchain.
4. Read that skill’s `SKILL.md` fully before acting.
5. Prefer nested skills under a parent (e.g. `binary-re/static-analysis`) over flat aliases.
6. For unknown injection class → `injection-checking` first, then a specific class skill.
7. If nothing here fits, open `bundle-index.md`.

---

## Master Routing Table (problem → skill)

| Problem | Primary skill | Helper(s) | Do not use as primary |
| --- | --- | --- | --- |
| Production code change / review quality | `code-quality-standards` | language style skill if any | design-only skills |
| How to write comments / 写注释 | `comment-writing-standards` | `code-quality-standards` | — |
| Naming / 命名规范 | `naming-conventions-general` | language style skill | — |
| Python style / typing / 类型注解 | `python-style-and-typing` | `docstring-and-typedoc` | — |
| TypeScript / ESLint style | `typescript-style-and-eslint` | `prettier-eslint-editorconfig` | — |
| Prettier / EditorConfig / format pipeline | `prettier-eslint-editorconfig` | language style skill | — |
| Go style / gofmt | `go-style-conventions` | `code-quality-standards` | — |
| Rust style / clippy / rustfmt | `rust-style-and-clippy` | `code-quality-standards` | — |
| Java style / Javadoc | `java-style-and-javadoc` | `docstring-and-typedoc` | — |
| C# / .NET style | `csharp-style-conventions` | `code-quality-standards` | — |
| Docstrings / JSDoc / TSDoc | `docstring-and-typedoc` | language style skill | — |
| API OpenAPI prose / 写接口文档 | `api-documentation-writing` | `api-recon-and-docs` for discovery | — |
| README / CONTRIBUTING | `readme-and-contributing-docs` | `markdown-docs-style` | — |
| Commit message / 提交信息 | `commit-message-conventions` | `changelog-and-release-notes` | — |
| Git branch / workflow / 分支策略 | `git-workflow-conventions` | `pr-description-writing` | — |
| PR description / 写 PR | `pr-description-writing` | `git-workflow-conventions` | — |
| Changelog / release notes | `changelog-and-release-notes` | `commit-message-conventions` | — |
| Markdown docs style | `markdown-docs-style` | `readme-and-contributing-docs` | — |
| Code review comment tone / 评审意见 | `code-review-comments-style` | `code-quality-standards` | — |
| Shell / bash style / shellcheck | `shell-script-style` | `code-quality-standards` | — |
| SQL style / migrations | `sql-style-conventions` | `code-quality-standards` | — |
| User-facing error copy / 错误文案 | `error-message-ux-writing` | `logging-message-style` | — |
| Logging message style / 日志规范 | `logging-message-style` | `error-message-ux-writing` | — |
| Unknown binary / “what does this do” | `binary-re` | nested phase after triage | hollow tool lists alone |
| Disassemble / decompile / xrefs | `binary-re/static-analysis` | `Ghidra_IDAReverseEngineeringSkill` if Ghidra/IDA-specific | — |
| RE tools missing / misconfigured | `binary-re/tool-setup` | — | — |
| Ghidra/IDA scripts, DB, signatures | `Ghidra_IDAReverseEngineeringSkill` | `binary-re/static-analysis` | — |
| No TLS / HTTPS plaintext | `tls-plaintext-acquisition` | `mobile-ssl-pinning-bypass` (authorized mobile pin) | jump straight to bypass |
| Mobile cert / SPKI pinning | `mobile-ssl-pinning-bypass` | after TLS skill | use without authorization |
| Unknown Protobuf / gRPC / gRPC-Web | `protobuf-grpc-reverse-engineering` | TLS skill if still encrypted | treat frames as fields |
| Binary WebSocket (opcode 2) | `websocket-binary-reverse-engineering` | protobuf skill if body is PB | treat TCP segments as messages |
| WebSocket security (auth/origin/CSWSH) | `websocket-security` | `websocket-binary-reverse-engineering` for codecs | — |
| QUIC / HTTP/3 / QPACK / migration | `quic-http3-analysis` | TLS skill for endpoint secrets | assume TCP TLS methods work |
| Custom TCP/UDP protocol | `protocol-reverse-engineering` | `NetworkProtocolAnalysisSkill` for PCAP/dissector | offensive attack skills by default |
| PCAP triage / CTF traffic | `traffic-analysis-pcap` | `NetworkProtocolAnalysisSkill` for dissector/fuzz | — |
| PCAP / Lua dissector / Scapy / fuzz | `NetworkProtocolAnalysisSkill` | protocol skill after ID | — |
| Protocol logic lives in a binary | `binary-re` | matching network skill | — |
| Malware / exploit lab isolation | `security-sandbox` | binary-re or protocol skill | production host analysis |
| Anti-cheat architecture research | `anti-cheat-systems` | binary-re for drivers | unauthorized bypass work |
| Memory dump forensics | `memory-forensics-volatility` | `security-sandbox` | — |
| Android app pentest (authorized) | `android-pentesting-tricks` | `mobile-ssl-pinning-bypass`, `jadx` (agents) | — |
| iOS app pentest (authorized lab) | `ios-pentesting-tricks` | `mobile-ssl-pinning-bypass` | — |
| Security test planning / recon | `recon-and-methodology` | `api-recon-and-docs` | — |
| STRIDE / threat model workshop / 威胁建模 | `threat-modeling-stride` | `recon-and-methodology`, `code-quality-standards` | exploit class skills as primary |
| Secrets management / vault / rotation / 密钥管理 / .env secrets | `secrets-management-hygiene` | `logging-message-style`, `code-quality-standards`, `sbom-and-supply-chain` | credential abuse / stuffing |
| nginx security headers / TLS edge / server_tokens / proxy misconfig | `nginx-security-headers` | `code-quality-standards`, `secrets-management-hygiene`, `NetworkProtocolAnalysisSkill` | unauthorized third-party edge attacks |
| Redis bind / AUTH / ACL / dangerous commands / exposure | `redis-security-misconfig` | `secrets-management-hygiene`, `code-quality-standards`, `NetworkProtocolAnalysisSkill` | unauthorized Internet Redis scanning/abuse |
| Insecure file upload | `upload-insecure-files` | `path-traversal-lfi`, `xss-cross-site-scripting` | — |
| WAF bypass research (authorized) | `waf-bypass-techniques` | matching injection skill | production unauthorized bypass |
| GraphQL / hidden fields | `graphql-and-hidden-parameters` | `idor-broken-object-authorization` | — |
| Subdomain takeover candidates | `subdomain-takeover` | — | unauthorized claim of third-party assets |
| Clickjacking / UI redress | `clickjacking` | `csrf-cross-site-request-forgery` | — |
| Host header attacks | `http-host-header-attacks` | `password-reset-poisoning`, `web-cache-deception` | — |
| Password reset / magic-link Host or token poisoning | `password-reset-poisoning` | `http-host-header-attacks`, `open-redirect` | generic Host skill when email ATO is primary |
| Session fixation / SID not regenerated on login | `session-fixation-management` | `api-auth-and-jwt-abuse`, `csrf-cross-site-request-forgery` | post-login cookie theft as “fixation” |
| OAuth / OIDC misconfig | `oauth-oidc-misconfiguration` | `api-auth-and-jwt-abuse`, `open-redirect` | — |
| SAML SSO (signature, audience, ACS) | `saml-sso-basics` | `oauth-oidc-misconfiguration`, `session-fixation-management` | OAuth/OIDC-only apps |
| Multi-vector account takeover (ATO) chaining | `account-takeover-methodology` | `password-reset-poisoning`, `session-fixation-management`, `oauth-oidc-misconfiguration`, `api-auth-and-jwt-abuse`, `idor-broken-object-authorization`, `saml-sso-basics` | single-class deep dive alone |
| DNS rebinding research | `dns-rebinding-attacks` | `ssrf-server-side-request-forgery` | — |
| Arbitrary file access (broad) | `file-access-vuln` | `path-traversal-lfi`, `zip-slip-path-safety` | — |
| Zip slip / archive extract path traversal | `zip-slip-path-safety` | `path-traversal-lfi`, `file-access-vuln`, `code-quality-standards` | — |
| Terraform security / tfstate secrets / public S3 / IAM least privilege | `terraform-security-basics` | `secrets-management-hygiene`, `code-quality-standards`, `dockerfile-best-practices` | unauthorized cloud key abuse |
| Linux privilege escalation (lab) | `linux-privilege-escalation` | `security-sandbox` | unauthorized hosts |
| Windows privilege escalation (lab) | `windows-privilege-escalation` | `security-sandbox` | unauthorized hosts |
| Container escape / Docker misconfig (lab) | `container-escape-techniques` | `linux-privilege-escalation`, `security-sandbox` | unauthorized breakout |
| Kubernetes security / RBAC / secrets (lab) | `kubernetes-pentesting` | `container-escape-techniques`, `security-sandbox` | unauthorized clusters |
| Symmetric crypto CTF | `symmetric-cipher-attacks` | `rsa-attack-techniques` | production crypto breaking claims |
| LLM prompt / tool injection | `llm-prompt-injection` | `code-quality-standards`, `ai-ml-security` | — |
| ML/LLM system security (supply chain, poisoning, model exposure, MLOps) | `ai-ml-security` | `llm-prompt-injection`, `recon-and-methodology`, `code-quality-standards` | unauthorized third-party model abuse |
| Solidity / smart-contract vulns (reentrancy, access control, oracle) | `smart-contract-vulnerabilities` | `recon-and-methodology`, `code-quality-standards` | unauthorized mainnet exploitation |
| Stego CTF | `steganography-techniques` | `traffic-analysis-pcap` if network | — |
| Injection class unknown | `injection-checking` | specialized class skill after triage | random payload spam |
| SQL injection | `sqli-sql-injection` | `injection-checking` if unsure | — |
| XSS | `xss-cross-site-scripting` | — | — |
| SSRF | `ssrf-server-side-request-forgery` | `open-redirect` if chain | — |
| Command injection | `cmdi-command-injection` | — | — |
| SSTI | `ssti-server-side-template-injection` | `expression-language-injection` if JVM EL/SpEL/OGNL | — |
| CSV / spreadsheet formula injection | `csv-formula-injection` | `code-quality-standards` for export sanitize | server-side RCE claims from client formulas |
| EL / SpEL / OGNL expression injection | `expression-language-injection` | `ssti-server-side-template-injection` if template engine | mass Internet scanning |
| XXE | `xxe-xml-external-entity` | `ssrf-server-side-request-forgery` if XXE→SSRF | — |
| Path traversal / LFI | `path-traversal-lfi` | `zip-slip-path-safety` if archive extract | — |
| Zip slip / tar slip / unsafe unzip | `zip-slip-path-safety` | `path-traversal-lfi`, `file-access-vuln` | — |
| Prototype pollution (JS merge/clone) | `prototype-pollution` | `xss-cross-site-scripting` if DOM gadget | — |
| Insecure deserialization | `deserialization-insecure` | `jndi-injection` if lookup chain | weaponized chains off-scope |
| PHP type juggling / loose comparison | `type-juggling` | `injection-checking` if sink language unclear | — |
| Dependency / package namespace confusion | `dependency-confusion` | `recon-and-methodology`, `code-quality-standards` | unauthorized public squatting |
| NoSQL / Mongo operator injection | `nosql-injection` | `injection-checking` if unsure | `sqli-sql-injection` for SQL engines |
| JNDI / Log4Shell-class lookup | `jndi-injection` | `deserialization-insecure` if object stream | mass Internet scanning |
| CRLF / response splitting / header inject | `crlf-injection` | `xss-cross-site-scripting` if header→XSS | — |
| IDOR / BOLA | `idor-broken-object-authorization` | `api-recon-and-docs` | — |
| JWT / API auth abuse | `api-auth-and-jwt-abuse` | `api-recon-and-docs` | — |
| Session fixation / no regenerate-on-auth | `session-fixation-management` | `csrf-cross-site-request-forgery`, `api-auth-and-jwt-abuse` | — |
| Password reset poisoning (Host/token/email link) | `password-reset-poisoning` | `http-host-header-attacks`, `open-redirect` | — |
| MFA / 2FA bypass (skip, backup codes, response manip) | `mfa-bypass-methodology` | `rate-limit-bypass-testing`, `race-condition`, `api-auth-and-jwt-abuse` | — |
| SAML SSO misconfig | `saml-sso-basics` | `session-fixation-management`, `api-auth-and-jwt-abuse` | — |
| Account takeover methodology / ATO chain | `account-takeover-methodology` | `password-reset-poisoning`, `session-fixation-management`, `oauth-oidc-misconfiguration`, `api-auth-and-jwt-abuse`, `idor-broken-object-authorization` | — |
| CSRF | `csrf-cross-site-request-forgery` | — | — |
| CORS misconfig | `cors-cross-origin-misconfiguration` | — | — |
| Race / TOCTOU | `race-condition` | `business-logic-vuln` | — |
| Request smuggling | `request-smuggling` | `http2-specific-attacks` for H2.CL/H2.TE/H2.0 depth | — |
| HTTP/2 desync / H2.CL / H2.TE / H2.0 | `http2-specific-attacks` | `request-smuggling` | volumetric H2 DoS as “research” |
| CAPTCHA / bot-challenge control gaps (authorized) | `captcha-bypass-research` | `rate-limit-bypass-testing` | CAPTCHA farms / fraud ops |
| Rate limit bypass / anti-automation keying | `rate-limit-bypass-testing` | `mfa-bypass-methodology`, `captcha-bypass-research`, `race-condition` | unapproved proxy farms |
| Open redirect | `open-redirect` | `ssrf-server-side-request-forgery` if chained | — |
| Business logic flaws | `business-logic-vuln` | `race-condition`, `idor-broken-object-authorization` | — |
| API discovery / OpenAPI | `api-recon-and-docs` | injection or IDOR skills after map | — |
| 401/403 bypass research | `401-403-bypass-techniques` | `api-auth-and-jwt-abuse` | unauthorized target abuse |
| Stack overflow / ROP (CTF) | `stack-overflow-and-rop` | `binary-protection-bypass` (agents) | production unauthorized exploit |
| Heap CTF | `heap-exploitation` | `stack-overflow-and-rop` | — |
| Format string CTF | `format-string-exploitation` | — | — |
| RSA CTF | `rsa-attack-techniques` | — | — |
| Hash cracking / length extension | `hash-attack-techniques` | — | — |
| Classical ciphers CTF | `classical-cipher-analysis` | — | — |
| Symmetric cipher CTF (ECB/padding/CTR) | `symmetric-cipher-attacks` | — | — |
| Generic polished UI | `frontend-design` | `apple-ui-design` or `top-design` | — |
| Apple-like minimal UI | `apple-ui-design` | `frontend-design` | top-design maximalism |
| Award / immersive brand site | `top-design` | `frontend-design` | apple minimalism |
| HTTP parameter pollution (HPP) | `http-parameter-pollution` | `injection-checking` | — |
| Web cache deception | `web-cache-deception` | — | — |
| Dependency confusion | `dependency-confusion` | `recon-and-methodology` | unauthorized registry squatting |
| PHP type juggling | `type-juggling` | `injection-checking` | — |
| CSV / spreadsheet formula injection | `csv-formula-injection` | `injection-checking` | phishing third parties |
| EL / SpEL / OGNL injection | `expression-language-injection` | `ssti-server-side-template-injection` | mass Internet scan |
| Container escape research (lab) | `container-escape-techniques` | `security-sandbox`, `linux-privilege-escalation` | unauthorized hosts |
| Kubernetes pentest (authorized) | `kubernetes-pentesting` | `container-escape-techniques` | — |
| Frida hooking (owned app/lab) | `frida-hooking-playbook` | `mobile-ssl-pinning-bypass` | unauthorized targets |
| Firmware unpack / triage | `firmware-analysis-basics` | `binary-re` | — |
| Smart contract / Solidity vulns | `smart-contract-vulnerabilities` | `code-quality-standards` | unauthorized mainnet exploit |
| AI/ML system security review | `ai-ml-security` | `llm-prompt-injection` | third-party AI abuse |
| Unit testing style / 单元测试 | `unit-testing-style` | `mocking-and-test-doubles`, `code-quality-standards` | — |
| Mocks / test doubles | `mocking-and-test-doubles` | `unit-testing-style` | — |
| Property-based testing / 属性测试 | `property-based-testing` | `unit-testing-style`, `code-quality-standards` | — |
| Performance / load testing / 性能测试 | `performance-testing-basics` | `observability-metrics-tracing`, `code-quality-standards` | unauthorized prod load |
| Git branch / workflow | `git-workflow-conventions` | `commit-message-conventions`, `pr-description-writing` | — |
| PR description writing / 写 PR | `pr-description-writing` | `git-workflow-conventions` | — |
| Async / concurrency design | `async-concurrency-patterns` | `code-quality-standards` | HTTP race vuln → `race-condition` |
| API versioning design | `api-versioning-design` | `api-documentation-writing` | — |
| Dockerfile best practices | `dockerfile-best-practices` | `ci-cd-pipeline-patterns` | — |
| CI/CD pipeline patterns | `ci-cd-pipeline-patterns` | `dockerfile-best-practices` | — |
| Terraform / OpenTofu security basics | `terraform-security-basics` | `secrets-management-hygiene`, `ci-cd-pipeline-patterns` | — |
| LDAP injection | `ldap-injection` | `injection-checking` | — |
| Mass assignment / over-posting | `mass-assignment` | `idor-broken-object-authorization` | — |
| Session fixation | `session-fixation-management` | `api-auth-and-jwt-abuse` | — |
| Password-reset host/token poison | `password-reset-poisoning` | `http-host-header-attacks` | — |
| MFA / 2FA bypass methodology | `mfa-bypass-methodology` | `api-auth-and-jwt-abuse`, `race-condition` | — |
| Rate-limit bypass testing | `rate-limit-bypass-testing` | `mfa-bypass-methodology`, `password-reset-poisoning` | — |
| CSP bypass research | `content-security-policy-bypass` | `xss-cross-site-scripting` | — |
| postMessage security | `postmessage-security` | `xss-cross-site-scripting` | — |
| Threat modeling / STRIDE / 威胁建模 | `threat-modeling-stride` | `recon-and-methodology` | — |
| Secrets hygiene / 密钥管理 | `secrets-management-hygiene` | `code-quality-standards` | — |
| SBOM / supply chain | `sbom-and-supply-chain` | `dependency-confusion` | — |
| Bug bounty methodology | `bug-bounty-methodology` | `recon-and-methodology` | unauthorized targets |
| Secure SDLC / SSDLC / 安全开发生命周期 | `secure-sdlc-checklist` | `threat-modeling-stride`, `sast-dast-tooling-usage`, `code-quality-standards` | scanner-only as full SDLC |
| SAST / DAST / 静态扫描 / scanner triage | `sast-dast-tooling-usage` | `secure-sdlc-checklist`, `code-quality-standards`, `ci-cd-pipeline-patterns` | exploit class skills as primary |
| Accessibility / a11y / 无障碍 | `accessibility-a11y-checklist` | `code-quality-standards` | — |
| i18n / l10n / 国际化 | `i18n-l10n-guidelines` | `code-quality-standards` | — |
| React component patterns | `react-component-patterns` | `state-management-guidelines` | — |
| Client state management | `state-management-guidelines` | `react-component-patterns` | — |
| JSON Schema design | `json-schema-design` | `api-documentation-writing` | — |
| DB migration safety / 数据库迁移 | `database-migration-safety` | `sql-style-conventions` | — |
| Caching strategies / 缓存 | `caching-strategies` | `async-concurrency-patterns` | — |
| Retry / backoff / 重试 | `retry-backoff-patterns` | `async-concurrency-patterns` | — |
| Observability / metrics / tracing | `observability-metrics-tracing` | `logging-message-style` | — |
| Feature flags / 功能开关 | `feature-flag-patterns` | `code-quality-standards` | — |

---

## Network Layer Order (earliest unresolved layer wins)

| Order | If still blocked… | Primary |
| ---: | --- | --- |
| 1 | Cannot see application plaintext over TLS | `tls-plaintext-acquisition` |
| 2 | Mobile pinning blocks MITM | `mobile-ssl-pinning-bypass` |
| 3 | Transport is QUIC/HTTP3 | `quic-http3-analysis` |
| 4 | Body is Protobuf/gRPC | `protobuf-grpc-reverse-engineering` |
| 5 | Body is binary WebSocket | `websocket-binary-reverse-engineering` |
| 6 | Framing is custom over TCP/UDP | `protocol-reverse-engineering` |
| 7 | Need capture tooling / dissector / authorized fuzz | `NetworkProtocolAnalysisSkill` or `traffic-analysis-pcap` |

---

## Web / API Security Order

| Order | Situation | Primary |
| ---: | --- | --- |
| 1 | Endpoints unknown | `api-recon-and-docs` |
| 2 | Injection class unclear | `injection-checking` |
| 3 | Specific injection | matching class skill (`sqli-*`, `xss-*`, …) |
| 4 | Object-level auth | `idor-broken-object-authorization` |
| 5 | Token/session/JWT | `api-auth-and-jwt-abuse` |
| 5b | Session fixation (SID reuse across login) | `session-fixation-management` |
| 5c | Password-reset / magic-link poisoning | `password-reset-poisoning` |
| 5d | MFA / 2FA enforcement gaps | `mfa-bypass-methodology` |
| 5e | Rate limit / lockout bypass | `rate-limit-bypass-testing` |
| 5f | SAML SSO misconfig | `saml-sso-basics` |
| 5g | Multi-vector ATO plan / chain | `account-takeover-methodology` |
| 6 | Cross-site state change | `csrf-cross-site-request-forgery` |
| 7 | Cross-origin config | `cors-cross-origin-misconfiguration` |
| 8 | Workflow abuse without classic vuln | `business-logic-vuln` |

---

## Binary RE Phase Order

| Phase | Skill path | When |
| --- | --- | --- |
| Entry | `binary-re` | Any unknown executable / bytecode |
| Triage | `binary-re/triage` | Identify format, arch, packing |
| Static | `binary-re/static-analysis` | Disasm, decompile, xrefs (canonical) |
| Dynamic | `binary-re/dynamic-analysis` | Emulate, debug, trace (authorized) |
| Synthesis | `binary-re/synthesis` | Evidence-backed report |
| Tools | `binary-re/tool-setup` | Install / fix r2, Ghidra, QEMU, Frida |

**Aliases (thin redirects only — do not edit as separate copies):**

| Alias | Canonical |
| --- | --- |
| `binary-re-static-analysis/` | `binary-re/static-analysis/` |
| `binary-re-tool-setup/` | `binary-re/tool-setup/` |

---

## Skill Catalog (local)

### Code quality

| Directory | Role |
| --- | --- |
| `code-quality-standards/` | Implementation / review baseline (reliability, security, tests) |

### Language style, comments, and docs

| Directory | Role |
| --- | --- |
| `comment-writing-standards/` | When/how to comment (why, invariants) |
| `naming-conventions-general/` | Naming across languages |
| `python-style-and-typing/` | PEP 8, typing, ruff/mypy |
| `typescript-style-and-eslint/` | TS strict + ESLint |
| `prettier-eslint-editorconfig/` | Formatter/linter ownership |
| `go-style-conventions/` | Effective Go, gofmt |
| `rust-style-and-clippy/` | rustfmt, clippy, rustdoc |
| `java-style-and-javadoc/` | Java style + Javadoc |
| `csharp-style-conventions/` | C# / .NET style |
| `docstring-and-typedoc/` | Docstrings / JSDoc / TSDoc |
| `api-documentation-writing/` | OpenAPI description quality |
| `readme-and-contributing-docs/` | README + CONTRIBUTING |
| `commit-message-conventions/` | Conventional Commits |
| `git-workflow-conventions/` | Branch naming, trunk/Git Flow, PR hygiene |
| `pr-description-writing/` | PR title/body Why/What/Test |
| `changelog-and-release-notes/` | Changelog / release notes |
| `markdown-docs-style/` | Markdown hygiene |
| `code-review-comments-style/` | Review comment craft |
| `shell-script-style/` | Bash safety + shellcheck |
| `sql-style-conventions/` | SQL formatting / naming |
| `error-message-ux-writing/` | User-facing error copy |
| `logging-message-style/` | Structured log messages |
| `unit-testing-style/` | Unit test design, AAA, naming |
| `mocking-and-test-doubles/` | Mocks/fakes/stubs discipline |
| `property-based-testing/` | Property-based / Hypothesis / fast-check |
| `performance-testing-basics/` | Load/perf tests, SLIs, tool overview |
| `git-workflow-conventions/` | Branching and PR process hygiene |
| `pr-description-writing/` | PR title/body Why/What/Test |
| `async-concurrency-patterns/` | Async/await, cancel, races in code |
| `api-versioning-design/` | API version strategy and deprecation |
| `dockerfile-best-practices/` | Secure, cache-friendly Dockerfiles |
| `ci-cd-pipeline-patterns/` | CI stages, secrets, artifacts |
| `threat-modeling-stride/` | STRIDE workshop / DFD threat modeling |
| `secrets-management-hygiene/` | Vault patterns, rotation, no secrets in code |
| `nginx-security-headers/` | nginx security headers, TLS edge, server_tokens |
| `redis-security-misconfig/` | Redis bind, AUTH/ACL, dangerous command exposure |
| `sbom-and-supply-chain/` | SBOM generation and supply-chain hygiene |
| `bug-bounty-methodology/` | Authorized bug bounty workflow |
| `secure-sdlc-checklist/` | Secure SDLC phases, gates, RACI |
| `sast-dast-tooling-usage/` | SAST/DAST run, gates, noise triage |
| `accessibility-a11y-checklist/` | WCAG-oriented a11y checklist |
| `i18n-l10n-guidelines/` | Internationalization / localization |
| `react-component-patterns/` | React structure, hooks, colocation |
| `state-management-guidelines/` | Client vs server state choices |
| `json-schema-design/` | JSON Schema / OpenAPI models |
| `database-migration-safety/` | Expand/contract safe migrations |
| `caching-strategies/` | Cache keys, TTL, invalidation |
| `retry-backoff-patterns/` | Retries, backoff, idempotency |
| `observability-metrics-tracing/` | Metrics, logs, traces |
| `feature-flag-patterns/` | Feature flags and kill switches |

### Reverse engineering

| Directory | Role |
| --- | --- |
| `binary-re/` | Binary RE hub + nested phases |
| `binary-re/triage/` | Fast fingerprint |
| `binary-re/static-analysis/` | r2 / Ghidra static deep dive |
| `binary-re/dynamic-analysis/` | QEMU / GDB / Frida |
| `binary-re/synthesis/` | Structured findings |
| `binary-re/tool-setup/` | Toolchain install |
| `Ghidra_IDAReverseEngineeringSkill/` | Ghidra/IDA-focused workflow |

### Protocol and network

| Directory | Role |
| --- | --- |
| `tls-plaintext-acquisition/` | Least-invasive TLS plaintext |
| `protobuf-grpc-reverse-engineering/` | Schema recovery; wire probe script |
| `websocket-binary-reverse-engineering/` | WS framing + app state machine |
| `websocket-security/` | WS auth, origin, CSWSH (authorized) |
| `quic-http3-analysis/` | QUIC/HTTP3 evidence |
| `mobile-ssl-pinning-bypass/` | Authorized mobile pinning helper |
| `protocol-reverse-engineering/` | Proprietary protocol recovery |
| `NetworkProtocolAnalysisSkill/` | PCAP, Wireshark Lua, Scapy, authorized fuzz |
| `traffic-analysis-pcap/` | PCAP triage / stream export / CTF traffic |

### Web injection

| Directory | Role |
| --- | --- |
| `injection-checking/` | Injection class triage dispatcher |
| `sqli-sql-injection/` | SQL injection |
| `xss-cross-site-scripting/` | XSS reflected/stored/DOM |
| `ssrf-server-side-request-forgery/` | SSRF + metadata notes |
| `cmdi-command-injection/` | OS command injection |
| `ssti-server-side-template-injection/` | Template injection |
| `xxe-xml-external-entity/` | XXE |
| `path-traversal-lfi/` | Path traversal / LFI |
| `zip-slip-path-safety/` | Zip slip / archive extract path safety |
| `prototype-pollution/` | JS prototype pollution |
| `deserialization-insecure/` | Insecure deserialization methodology |
| `nosql-injection/` | NoSQL / Mongo operator injection |
| `jndi-injection/` | JNDI / Log4Shell-class lookup |
| `crlf-injection/` | CRLF / response splitting |
| `csv-formula-injection/` | CSV / spreadsheet formula injection |
| `expression-language-injection/` | EL / SpEL / OGNL expression injection |
| `type-juggling/` | PHP loose comparison / type confusion |
| `dependency-confusion/` | Package namespace / registry confusion |
| `http-parameter-pollution/` | HTTP parameter pollution (HPP) |
| `ldap-injection/` | LDAP filter/DN injection |
| `mass-assignment/` | Mass assignment / over-posting |

### Web / API auth and logic

| Directory | Role |
| --- | --- |
| `recon-and-methodology/` | Test planning, recon workflow |
| `threat-modeling-stride/` | STRIDE / design-time threat modeling |
| `secrets-management-hygiene/` | Secrets lifecycle hygiene (vault, rotation) |
| `nginx-security-headers/` | nginx headers, TLS edge, server_tokens, proxy misconfig |
| `redis-security-misconfig/` | Redis bind, AUTH/ACL, dangerous command exposure |
| `api-recon-and-docs/` | OpenAPI/Swagger/endpoint discovery |
| `api-auth-and-jwt-abuse/` | JWT and API auth flaws |
| `session-fixation-management/` | Session fixation detect/prevent |
| `password-reset-poisoning/` | Reset/magic-link Host and token poisoning |
| `mfa-bypass-methodology/` | MFA/2FA skip, backup codes, step-up gaps |
| `rate-limit-bypass-testing/` | Rate limit keying, header/IP trust, rotation |
| `oauth-oidc-misconfiguration/` | OAuth/OIDC misconfiguration |
| `saml-sso-basics/` | SAML SSO signature/audience/ACS basics |
| `account-takeover-methodology/` | Multi-vector ATO chaining (authorized) |
| `idor-broken-object-authorization/` | BOLA/IDOR |
| `csrf-cross-site-request-forgery/` | CSRF |
| `cors-cross-origin-misconfiguration/` | CORS |
| `clickjacking/` | UI redress / framing |
| `http-host-header-attacks/` | Host header poisoning |
| `dns-rebinding-attacks/` | DNS rebinding research |
| `race-condition/` | TOCTOU / limit overrun |
| `business-logic-vuln/` | Business logic abuse cases |
| `request-smuggling/` | HTTP request smuggling |
| `http2-specific-attacks/` | HTTP/2 desync (H2.CL / H2.TE / H2.0) |
| `captcha-bypass-research/` | CAPTCHA control research (authorized, not fraud) |
| `open-redirect/` | Open redirect |
| `401-403-bypass-techniques/` | Forbidden endpoint bypass research |
| `upload-insecure-files/` | Insecure file upload |
| `waf-bypass-techniques/` | WAF bypass methodology (authorized) |
| `graphql-and-hidden-parameters/` | GraphQL + hidden parameters |
| `subdomain-takeover/` | Dangling DNS takeover candidates |
| `file-access-vuln/` | Arbitrary file access (broad) |
| `zip-slip-path-safety/` | Zip/tar slip on extract (entry path escape) |
| `web-cache-deception/` | Cache deception path confusion |
| `dependency-confusion/` | Package namespace confusion |
| `session-fixation-management/` | Session fixation detection/prevention |
| `password-reset-poisoning/` | Password-reset host/token poisoning |
| `content-security-policy-bypass/` | CSP bypass research (authorized) |
| `postmessage-security/` | window.postMessage origin safety |
| `threat-modeling-stride/` | STRIDE threat modeling workshops |
| `secrets-management-hygiene/` | Secrets storage, rotation, leak hygiene |
| `sbom-and-supply-chain/` | SBOM generation and supply-chain hygiene |
| `bug-bounty-methodology/` | Authorized bug bounty workflow |
| `secure-sdlc-checklist/` | Secure SDLC phases / release security gates |
| `sast-dast-tooling-usage/` | SAST/DAST tooling, CI gates, triage |

### Platform / cloud / runtime

| Directory | Role |
| --- | --- |
| `container-escape-techniques/` | Container escape lab methodology |
| `kubernetes-pentesting/` | K8s authorized security assessment |
| `terraform-security-basics/` | Terraform/OpenTofu state, IAM, public S3 |
| `frida-hooking-playbook/` | Frida instrumentation playbook |
| `firmware-analysis-basics/` | Firmware unpack and triage |

### Pwn / crypto CTF

| Directory | Role |
| --- | --- |
| `stack-overflow-and-rop/` | Stack overflow, ROP, ret2libc |
| `heap-exploitation/` | Educational heap CTF methodology |
| `format-string-exploitation/` | Format string CTF |
| `rsa-attack-techniques/` | RSA CTF attacks |
| `hash-attack-techniques/` | Hash cracking / length extension |
| `classical-cipher-analysis/` | Classical ciphers |
| `symmetric-cipher-attacks/` | ECB/padding/CTR CTF symmetric |

### Privilege escalation (lab)

| Directory | Role |
| --- | --- |
| `linux-privilege-escalation/` | Linux privesc checklist (lab/CTF) |
| `windows-privilege-escalation/` | Windows privesc checklist (lab) |
| `container-escape-techniques/` | Docker/container escape research (authorized lab) |
| `kubernetes-pentesting/` | K8s RBAC/secrets/misconfig assessment (authorized) |

### Forensics / mobile / stego / AI / contracts

| Directory | Role |
| --- | --- |
| `memory-forensics-volatility/` | Volatility 3 memory forensics |
| `android-pentesting-tricks/` | Authorized Android app testing |
| `ios-pentesting-tricks/` | Authorized iOS app testing (lab) |
| `steganography-techniques/` | Stego CTF tooling |
| `llm-prompt-injection/` | LLM prompt/tool injection testing |
| `ai-ml-security/` | ML/LLM system security (app, supply chain, poisoning awareness) |
| `smart-contract-vulnerabilities/` | Solidity/EVM audit & CTF vulnerability methodology |

### Security environment

| Directory | Role |
| --- | --- |
| `security-sandbox/` | Isolated VM/container lab |
| `anti-cheat-systems/` | Anti-cheat research (architecture first) |

### Frontend and design

| Directory | Role |
| --- | --- |
| `frontend-design/` | Production UI, avoid generic AI look |
| `apple-ui-design/` | Clean / premium Apple-like |
| `top-design/` | Immersive award-level sites |

### Router

| Directory | Role |
| --- | --- |
| `skill-router/` | This index + bundle fallback |

---

## Common Combinations

| Scenario | Route |
| --- | --- |
| Unknown executable | `binary-re` → triage → static |
| Ghidra-only task | `Ghidra_IDAReverseEngineeringSkill` + `binary-re/static-analysis` |
| Protocol in binary | `binary-re` + `protocol-reverse-engineering` |
| PCAP + protocol recovery | `traffic-analysis-pcap` or `NetworkProtocolAnalysisSkill` + protocol skill |
| Encrypted mobile Protobuf | TLS → (optional) mobile pin → protobuf |
| Binary WebSocket over TLS | TLS → websocket binary (→ protobuf if needed) |
| HTTP/3 API | quic → body codec skill |
| Malware dynamic lab | `security-sandbox` + binary-re |
| Polished web UI | `frontend-design` + apple or top-design |
| Web app black-box | `api-recon-and-docs` → `injection-checking` / `idor-*` / `api-auth-and-jwt-abuse` |
| CTF pwn stack | `ctf-reverse` (agents) or `stack-overflow-and-rop` |
| CTF crypto RSA | `rsa-attack-techniques` |
| Android app HTTPS | `android-pentesting-tricks` → pinning → TLS |
| LLM app injection only | `llm-prompt-injection` (+ `code-quality-standards` for fixes) |
| Full AI product / MLOps review | `ai-ml-security` → `llm-prompt-injection` for injection deep-dive |
| Solidity audit / DVDeFi-style CTF | `smart-contract-vulnerabilities` (+ `recon-and-methodology` for multi-contract inventory) |

---

## Bundle Fallback

If the loose library has no specific skill, read `bundle-index.md` and extract:

```powershell
tar -xOf "E:\download\all-skills-bundle-20260710.zip" "agents-skills/<name>/SKILL.md"
```

Inspect a local zip backup:

```powershell
tar -tf "E:\DESKTOP\skill\<name>.zip"
```

---

## Evidence Rules (RE / network / security skills)

- Prefer captures, runtime behavior, and reproducible artifacts over comments.
- Gate replay, mutation, fuzzing, interception, and live capture on ownership or authorization.
- Keep originals immutable; store derived artifacts separately.
- Redact credentials, cookies, tokens, device IDs, and personal data.
- Validate each protocol hypothesis with multiple samples and at least one controlled input change.
- Web/vuln skills: authorized targets only; proportionate proof of impact.

## Mega-batch routes (30-agent wave)

| Problem | Primary skill | Helper(s) | Do not use as primary |
| --- | --- | --- | --- |
| android-exported-components | `android-exported-components` | related domain skills | — |
| android-webview-security | `android-webview-security` | related domain skills | — |
| api-rate-limit-design | `api-rate-limit-design` | related domain skills | — |
| apk-signing-and-integrity | `apk-signing-and-integrity` | related domain skills | — |
| aws-iam-least-privilege | `aws-iam-least-privilege` | related domain skills | — |
| aws-s3-bucket-hardening | `aws-s3-bucket-hardening` | related domain skills | — |
| azure-blob-misconfig | `azure-blob-misconfig` | related domain skills | — |
| backpressure-patterns | `backpressure-patterns` | related domain skills | — |
| browser-extension-security | `browser-extension-security` | related domain skills | — |
| bulkhead-isolation | `bulkhead-isolation` | related domain skills | — |
| chaos-engineering-basics | `chaos-engineering-basics` | related domain skills | — |
| circuit-breaker-patterns | `circuit-breaker-patterns` | related domain skills | — |
| clickjacking-ui-redress-deep | `clickjacking-ui-redress-deep` | related domain skills | — |
| cloud-metadata-ssrf-defenses | `cloud-metadata-ssrf-defenses` | related domain skills | — |
| contract-testing-pact | `contract-testing-pact` | related domain skills | — |
| cookie-security-flags | `cookie-security-flags` | related domain skills | — |
| cors-credentialed-requests | `cors-credentialed-requests` | related domain skills | — |
| django-security-settings | `django-security-settings` | related domain skills | — |
| docker-compose-security | `docker-compose-security` | related domain skills | — |
| e2e-testing-playwright | `e2e-testing-playwright` | related domain skills | — |
| electron-app-security | `electron-app-security` | related domain skills | — |
| express-middleware-security | `express-middleware-security` | related domain skills | — |
| fastapi-security-patterns | `fastapi-security-patterns` | related domain skills | — |
| file-upload-polyglot-detection | `file-upload-polyglot-detection` | related domain skills | — |
| firewall-rule-review | `firewall-rule-review` | related domain skills | — |
| gcp-iam-basics | `gcp-iam-basics` | related domain skills | — |
| ghidra-scripting-basics | `ghidra-scripting-basics` | related domain skills | — |
| graphql-schema-design-style | `graphql-schema-design-style` | related domain skills | — |
| grpc-security-testing | `grpc-security-testing` | related domain skills | — |
| host-header-cache-poison | `host-header-cache-poison` | related domain skills | — |
| ida-python-basics | `ida-python-basics` | related domain skills | — |
| idor-graphql-nodes | `idor-graphql-nodes` | related domain skills | — |
| ios-keychain-hygiene | `ios-keychain-hygiene` | related domain skills | — |
| jwt-refresh-token-patterns | `jwt-refresh-token-patterns` | related domain skills | — |
| kubernetes-network-policy | `kubernetes-network-policy` | related domain skills | — |
| laravel-security-basics | `laravel-security-basics` | related domain skills | — |
| linux-hardening-checklist | `linux-hardening-checklist` | related domain skills | — |
| load-shedding-patterns | `load-shedding-patterns` | related domain skills | — |
| mfa-enrollment-flaws | `mfa-enrollment-flaws` | related domain skills | — |
| mutation-testing-basics | `mutation-testing-basics` | related domain skills | — |
| nextjs-security-checklist | `nextjs-security-checklist` | related domain skills | — |
| nodejs-security-checklist | `nodejs-security-checklist` | related domain skills | — |
| oauth-pkce-checklist | `oauth-pkce-checklist` | related domain skills | — |
| openapi-contract-testing | `openapi-contract-testing` | related domain skills | — |
| open-redirect-advanced | `open-redirect-advanced` | related domain skills | — |
| protobuf-api-design | `protobuf-api-design` | related domain skills | — |
| rails-security-checklist | `rails-security-checklist` | related domain skills | — |
| same-site-cookie-pitfalls | `same-site-cookie-pitfalls` | related domain skills | — |
| saml-signature-wrapping-awareness | `saml-signature-wrapping-awareness` | related domain skills | — |
| secrets-in-ci-pipelines | `secrets-in-ci-pipelines` | related domain skills | — |
| service-worker-security | `service-worker-security` | related domain skills | — |
| spring-security-checklist | `spring-security-checklist` | related domain skills | — |
| ssh-key-hygiene | `ssh-key-hygiene` | related domain skills | — |
| ssrf-filter-bypass-catalog | `ssrf-filter-bypass-catalog` | related domain skills | — |
| strings-and-ioc-triage | `strings-and-ioc-triage` | related domain skills | — |
| websocket-authz-deep | `websocket-authz-deep` | related domain skills | — |
| websocket-client-patterns | `websocket-client-patterns` | related domain skills | — |
| windows-hardening-basics | `windows-hardening-basics` | related domain skills | — |
| xxe-billion-laughs-defenses | `xxe-billion-laughs-defenses` | related domain skills | — |
| yara-hunting-workflow | `yara-hunting-workflow` | related domain skills | — |

### Mega-batch catalog

| Directory | Role |
| --- | --- |
| `android-exported-components/` | See SKILL.md Use when |
| `android-webview-security/` | See SKILL.md Use when |
| `api-rate-limit-design/` | See SKILL.md Use when |
| `apk-signing-and-integrity/` | See SKILL.md Use when |
| `aws-iam-least-privilege/` | See SKILL.md Use when |
| `aws-s3-bucket-hardening/` | See SKILL.md Use when |
| `azure-blob-misconfig/` | See SKILL.md Use when |
| `backpressure-patterns/` | See SKILL.md Use when |
| `browser-extension-security/` | See SKILL.md Use when |
| `bulkhead-isolation/` | See SKILL.md Use when |
| `chaos-engineering-basics/` | See SKILL.md Use when |
| `circuit-breaker-patterns/` | See SKILL.md Use when |
| `clickjacking-ui-redress-deep/` | See SKILL.md Use when |
| `cloud-metadata-ssrf-defenses/` | See SKILL.md Use when |
| `contract-testing-pact/` | See SKILL.md Use when |
| `cookie-security-flags/` | See SKILL.md Use when |
| `cors-credentialed-requests/` | See SKILL.md Use when |
| `django-security-settings/` | See SKILL.md Use when |
| `docker-compose-security/` | See SKILL.md Use when |
| `e2e-testing-playwright/` | See SKILL.md Use when |
| `electron-app-security/` | See SKILL.md Use when |
| `express-middleware-security/` | See SKILL.md Use when |
| `fastapi-security-patterns/` | See SKILL.md Use when |
| `file-upload-polyglot-detection/` | See SKILL.md Use when |
| `firewall-rule-review/` | See SKILL.md Use when |
| `gcp-iam-basics/` | See SKILL.md Use when |
| `ghidra-scripting-basics/` | See SKILL.md Use when |
| `graphql-schema-design-style/` | See SKILL.md Use when |
| `grpc-security-testing/` | See SKILL.md Use when |
| `host-header-cache-poison/` | See SKILL.md Use when |
| `ida-python-basics/` | See SKILL.md Use when |
| `idor-graphql-nodes/` | See SKILL.md Use when |
| `ios-keychain-hygiene/` | See SKILL.md Use when |
| `jwt-refresh-token-patterns/` | See SKILL.md Use when |
| `kubernetes-network-policy/` | See SKILL.md Use when |
| `laravel-security-basics/` | See SKILL.md Use when |
| `linux-hardening-checklist/` | See SKILL.md Use when |
| `load-shedding-patterns/` | See SKILL.md Use when |
| `mfa-enrollment-flaws/` | See SKILL.md Use when |
| `mutation-testing-basics/` | See SKILL.md Use when |
| `nextjs-security-checklist/` | See SKILL.md Use when |
| `nodejs-security-checklist/` | See SKILL.md Use when |
| `oauth-pkce-checklist/` | See SKILL.md Use when |
| `openapi-contract-testing/` | See SKILL.md Use when |
| `open-redirect-advanced/` | See SKILL.md Use when |
| `protobuf-api-design/` | See SKILL.md Use when |
| `rails-security-checklist/` | See SKILL.md Use when |
| `same-site-cookie-pitfalls/` | See SKILL.md Use when |
| `saml-signature-wrapping-awareness/` | See SKILL.md Use when |
| `secrets-in-ci-pipelines/` | See SKILL.md Use when |
| `service-worker-security/` | See SKILL.md Use when |
| `spring-security-checklist/` | See SKILL.md Use when |
| `ssh-key-hygiene/` | See SKILL.md Use when |
| `ssrf-filter-bypass-catalog/` | See SKILL.md Use when |
| `strings-and-ioc-triage/` | See SKILL.md Use when |
| `websocket-authz-deep/` | See SKILL.md Use when |
| `websocket-client-patterns/` | See SKILL.md Use when |
| `windows-hardening-basics/` | See SKILL.md Use when |
| `xxe-billion-laughs-defenses/` | See SKILL.md Use when |
| `yara-hunting-workflow/` | See SKILL.md Use when |

## 100-agent mega-batch routes

| Problem | Primary skill | Helper(s) | Do not use as primary |
| --- | --- | --- | --- |
| oauth-device-code-flow | `oauth-device-code-flow` | related domain skills | — |
| oauth-implicit-flow-risks | `oauth-implicit-flow-risks` | related domain skills | — |
| oidc-id-token-validation | `oidc-id-token-validation` | related domain skills | — |
| session-cookie-theft-defense | `session-cookie-theft-defense` | related domain skills | — |
| remember-me-token-security | `remember-me-token-security` | related domain skills | — |
| password-policy-design | `password-policy-design` | related domain skills | — |
| account-lockout-design | `account-lockout-design` | related domain skills | — |
| login-csrf-defense | `login-csrf-defense` | related domain skills | — |
| sso-logout-propagation | `sso-logout-propagation` | related domain skills | — |
| saml-metadata-hygiene | `saml-metadata-hygiene` | related domain skills | — |
| jwt-audience-issuer-checks | `jwt-audience-issuer-checks` | related domain skills | — |
| api-key-lifecycle | `api-key-lifecycle` | related domain skills | — |
| mtls-client-auth-basics | `mtls-client-auth-basics` | related domain skills | — |
| device-binding-tokens | `device-binding-tokens` | related domain skills | — |
| step-up-auth-patterns | `step-up-auth-patterns` | related domain skills | — |
| magic-link-auth-security | `magic-link-auth-security` | related domain skills | — |
| passkeys-webauthn-basics | `passkeys-webauthn-basics` | related domain skills | — |
| totp-mfa-implementation | `totp-mfa-implementation` | related domain skills | — |
| backup-code-storage | `backup-code-storage` | related domain skills | — |
| session-timeout-design | `session-timeout-design` | related domain skills | — |
| dom-clobbering-awareness | `dom-clobbering-awareness` | related domain skills | — |
| prototype-pollution-defenses | `prototype-pollution-defenses` | related domain skills | — |
| css-injection-exfiltration | `css-injection-exfiltration` | related domain skills | — |
| svg-xss-hardening | `svg-xss-hardening` | related domain skills | — |
| markdown-xss-sanitization | `markdown-xss-sanitization` | related domain skills | — |
| html-sanitizer-selection | `html-sanitizer-selection` | related domain skills | — |
| trusted-types-adoption | `trusted-types-adoption` | related domain skills | — |
| subresource-integrity-sri | `subresource-integrity-sri` | related domain skills | — |
| mixed-content-hardening | `mixed-content-hardening` | related domain skills | — |
| clickjacking-frame-busting | `clickjacking-frame-busting` | related domain skills | — |
| tabnabbing-noopener | `tabnabbing-noopener` | related domain skills | — |
| download-attribute-security | `download-attribute-security` | related domain skills | — |
| cors-preflight-cache | `cors-preflight-cache` | related domain skills | — |
| jsonp-legacy-risks | `jsonp-legacy-risks` | related domain skills | — |
| flash-crossdomain-legacy | `flash-crossdomain-legacy` | related domain skills | — |
| websocket-origin-validation | `websocket-origin-validation` | related domain skills | — |
| graphql-batching-limits | `graphql-batching-limits` | related domain skills | — |
| graphql-query-complexity | `graphql-query-complexity` | related domain skills | — |
| api-pagination-security | `api-pagination-security` | related domain skills | — |
| http-method-override-risks | `http-method-override-risks` | related domain skills | — |
| aws-security-groups-review | `aws-security-groups-review` | related domain skills | — |
| aws-lambda-least-privilege | `aws-lambda-least-privilege` | related domain skills | — |
| aws-ecs-task-security | `aws-ecs-task-security` | related domain skills | — |
| aws-rds-public-access | `aws-rds-public-access` | related domain skills | — |
| azure-keyvault-basics | `azure-keyvault-basics` | related domain skills | — |
| azure-nsg-review | `azure-nsg-review` | related domain skills | — |
| gcp-firewall-rules | `gcp-firewall-rules` | related domain skills | — |
| gcp-storage-public-access | `gcp-storage-public-access` | related domain skills | — |
| helm-chart-security | `helm-chart-security` | related domain skills | — |
| kubernetes-pod-security | `kubernetes-pod-security` | related domain skills | — |
| kubernetes-secrets-handling | `kubernetes-secrets-handling` | related domain skills | — |
| istio-authz-basics | `istio-authz-basics` | related domain skills | — |
| terraform-state-locking | `terraform-state-locking` | related domain skills | — |
| ansible-vault-usage | `ansible-vault-usage` | related domain skills | — |
| pulumi-secrets-basics | `pulumi-secrets-basics` | related domain skills | — |
| cloudformation-iam-guardrails | `cloudformation-iam-guardrails` | related domain skills | — |
| vault-agent-injection | `vault-agent-injection` | related domain skills | — |
| sealed-secrets-patterns | `sealed-secrets-patterns` | related domain skills | — |
| external-secrets-operator | `external-secrets-operator` | related domain skills | — |
| cert-manager-basics | `cert-manager-basics` | related domain skills | — |
| sql-injection-defenses-orm | `sql-injection-defenses-orm` | related domain skills | — |
| nosql-injection-defenses | `nosql-injection-defenses` | related domain skills | — |
| command-injection-defenses | `command-injection-defenses` | related domain skills | — |
| path-traversal-defenses | `path-traversal-defenses` | related domain skills | — |
| ssrf-allowlist-design | `ssrf-allowlist-design` | related domain skills | — |
| xxe-parser-hardening | `xxe-parser-hardening` | related domain skills | — |
| deserialization-safe-formats | `deserialization-safe-formats` | related domain skills | — |
| file-upload-secure-storage | `file-upload-secure-storage` | related domain skills | — |
| postgresql-security-settings | `postgresql-security-settings` | related domain skills | — |
| mysql-security-hardening | `mysql-security-hardening` | related domain skills | — |
| elasticsearch-security-basics | `elasticsearch-security-basics` | related domain skills | — |
| kafka-acl-basics | `kafka-acl-basics` | related domain skills | — |
| rabbitmq-security-basics | `rabbitmq-security-basics` | related domain skills | — |
| redis-acl-design | `redis-acl-design` | related domain skills | — |
| mongodb-auth-hardening | `mongodb-auth-hardening` | related domain skills | — |
| typescript-strict-migration | `typescript-strict-migration` | related domain skills | — |
| python-packaging-modern | `python-packaging-modern` | related domain skills | — |
| go-module-hygiene | `go-module-hygiene` | related domain skills | — |
| rust-unsafe-guidelines | `rust-unsafe-guidelines` | related domain skills | — |
| java-module-system-basics | `java-module-system-basics` | related domain skills | — |
| dependency-pinning-strategies | `dependency-pinning-strategies` | related domain skills | — |
| license-compliance-scan | `license-compliance-scan` | related domain skills | — |
| codeowners-review-routing | `codeowners-review-routing` | related domain skills | — |
| branch-protection-rules | `branch-protection-rules` | related domain skills | — |
| signed-commits-basics | `signed-commits-basics` | related domain skills | — |
| reproducible-builds-basics | `reproducible-builds-basics` | related domain skills | — |
| container-image-signing | `container-image-signing` | related domain skills | — |
| sbom-ci-enforcement | `sbom-ci-enforcement` | related domain skills | — |
| vulnerability-sla-process | `vulnerability-sla-process` | related domain skills | — |
| security-champion-program | `security-champion-program` | related domain skills | — |
| react-hooks-security | `react-hooks-security` | related domain skills | — |
| vue-router-auth-guards | `vue-router-auth-guards` | related domain skills | — |
| angular-security-basics | `angular-security-basics` | related domain skills | — |
| svelte-security-notes | `svelte-security-notes` | related domain skills | — |
| react-native-security-basics | `react-native-security-basics` | related domain skills | — |
| flutter-security-basics | `flutter-security-basics` | related domain skills | — |
| cordova-webview-risks | `cordova-webview-risks` | related domain skills | — |
| pwa-security-checklist | `pwa-security-checklist` | related domain skills | — |
| cdn-cache-key-design | `cdn-cache-key-design` | related domain skills | — |
| static-asset-fingerprinting | `static-asset-fingerprinting` | related domain skills | — |

### 100-agent catalog

| Directory | Role |
| --- | --- |
| `oauth-device-code-flow/` | See SKILL.md Use when |
| `oauth-implicit-flow-risks/` | See SKILL.md Use when |
| `oidc-id-token-validation/` | See SKILL.md Use when |
| `session-cookie-theft-defense/` | See SKILL.md Use when |
| `remember-me-token-security/` | See SKILL.md Use when |
| `password-policy-design/` | See SKILL.md Use when |
| `account-lockout-design/` | See SKILL.md Use when |
| `login-csrf-defense/` | See SKILL.md Use when |
| `sso-logout-propagation/` | See SKILL.md Use when |
| `saml-metadata-hygiene/` | See SKILL.md Use when |
| `jwt-audience-issuer-checks/` | See SKILL.md Use when |
| `api-key-lifecycle/` | See SKILL.md Use when |
| `mtls-client-auth-basics/` | See SKILL.md Use when |
| `device-binding-tokens/` | See SKILL.md Use when |
| `step-up-auth-patterns/` | See SKILL.md Use when |
| `magic-link-auth-security/` | See SKILL.md Use when |
| `passkeys-webauthn-basics/` | See SKILL.md Use when |
| `totp-mfa-implementation/` | See SKILL.md Use when |
| `backup-code-storage/` | See SKILL.md Use when |
| `session-timeout-design/` | See SKILL.md Use when |
| `dom-clobbering-awareness/` | See SKILL.md Use when |
| `prototype-pollution-defenses/` | See SKILL.md Use when |
| `css-injection-exfiltration/` | See SKILL.md Use when |
| `svg-xss-hardening/` | See SKILL.md Use when |
| `markdown-xss-sanitization/` | See SKILL.md Use when |
| `html-sanitizer-selection/` | See SKILL.md Use when |
| `trusted-types-adoption/` | See SKILL.md Use when |
| `subresource-integrity-sri/` | See SKILL.md Use when |
| `mixed-content-hardening/` | See SKILL.md Use when |
| `clickjacking-frame-busting/` | See SKILL.md Use when |
| `tabnabbing-noopener/` | See SKILL.md Use when |
| `download-attribute-security/` | See SKILL.md Use when |
| `cors-preflight-cache/` | See SKILL.md Use when |
| `jsonp-legacy-risks/` | See SKILL.md Use when |
| `flash-crossdomain-legacy/` | See SKILL.md Use when |
| `websocket-origin-validation/` | See SKILL.md Use when |
| `graphql-batching-limits/` | See SKILL.md Use when |
| `graphql-query-complexity/` | See SKILL.md Use when |
| `api-pagination-security/` | See SKILL.md Use when |
| `http-method-override-risks/` | See SKILL.md Use when |
| `aws-security-groups-review/` | See SKILL.md Use when |
| `aws-lambda-least-privilege/` | See SKILL.md Use when |
| `aws-ecs-task-security/` | See SKILL.md Use when |
| `aws-rds-public-access/` | See SKILL.md Use when |
| `azure-keyvault-basics/` | See SKILL.md Use when |
| `azure-nsg-review/` | See SKILL.md Use when |
| `gcp-firewall-rules/` | See SKILL.md Use when |
| `gcp-storage-public-access/` | See SKILL.md Use when |
| `helm-chart-security/` | See SKILL.md Use when |
| `kubernetes-pod-security/` | See SKILL.md Use when |
| `kubernetes-secrets-handling/` | See SKILL.md Use when |
| `istio-authz-basics/` | See SKILL.md Use when |
| `terraform-state-locking/` | See SKILL.md Use when |
| `ansible-vault-usage/` | See SKILL.md Use when |
| `pulumi-secrets-basics/` | See SKILL.md Use when |
| `cloudformation-iam-guardrails/` | See SKILL.md Use when |
| `vault-agent-injection/` | See SKILL.md Use when |
| `sealed-secrets-patterns/` | See SKILL.md Use when |
| `external-secrets-operator/` | See SKILL.md Use when |
| `cert-manager-basics/` | See SKILL.md Use when |
| `sql-injection-defenses-orm/` | See SKILL.md Use when |
| `nosql-injection-defenses/` | See SKILL.md Use when |
| `command-injection-defenses/` | See SKILL.md Use when |
| `path-traversal-defenses/` | See SKILL.md Use when |
| `ssrf-allowlist-design/` | See SKILL.md Use when |
| `xxe-parser-hardening/` | See SKILL.md Use when |
| `deserialization-safe-formats/` | See SKILL.md Use when |
| `file-upload-secure-storage/` | See SKILL.md Use when |
| `postgresql-security-settings/` | See SKILL.md Use when |
| `mysql-security-hardening/` | See SKILL.md Use when |
| `elasticsearch-security-basics/` | See SKILL.md Use when |
| `kafka-acl-basics/` | See SKILL.md Use when |
| `rabbitmq-security-basics/` | See SKILL.md Use when |
| `redis-acl-design/` | See SKILL.md Use when |
| `mongodb-auth-hardening/` | See SKILL.md Use when |
| `typescript-strict-migration/` | See SKILL.md Use when |
| `python-packaging-modern/` | See SKILL.md Use when |
| `go-module-hygiene/` | See SKILL.md Use when |
| `rust-unsafe-guidelines/` | See SKILL.md Use when |
| `java-module-system-basics/` | See SKILL.md Use when |
| `dependency-pinning-strategies/` | See SKILL.md Use when |
| `license-compliance-scan/` | See SKILL.md Use when |
| `codeowners-review-routing/` | See SKILL.md Use when |
| `branch-protection-rules/` | See SKILL.md Use when |
| `signed-commits-basics/` | See SKILL.md Use when |
| `reproducible-builds-basics/` | See SKILL.md Use when |
| `container-image-signing/` | See SKILL.md Use when |
| `sbom-ci-enforcement/` | See SKILL.md Use when |
| `vulnerability-sla-process/` | See SKILL.md Use when |
| `security-champion-program/` | See SKILL.md Use when |
| `react-hooks-security/` | See SKILL.md Use when |
| `vue-router-auth-guards/` | See SKILL.md Use when |
| `angular-security-basics/` | See SKILL.md Use when |
| `svelte-security-notes/` | See SKILL.md Use when |
| `react-native-security-basics/` | See SKILL.md Use when |
| `flutter-security-basics/` | See SKILL.md Use when |
| `cordova-webview-risks/` | See SKILL.md Use when |
| `pwa-security-checklist/` | See SKILL.md Use when |
| `cdn-cache-key-design/` | See SKILL.md Use when |
| `static-asset-fingerprinting/` | See SKILL.md Use when |


## 10-agent batch routes (post-100)

| Problem | Primary skill | Helper(s) | Do not use as primary |
| --- | --- | --- | --- |
| oauth-token-binding-dpop | `oauth-token-binding-dpop` | related domain skills | — |
| saml-assertion-encryption | `saml-assertion-encryption` | related domain skills | — |
| webauthn-attestation-review | `webauthn-attestation-review` | related domain skills | — |
| csp-report-only-rollout | `csp-report-only-rollout` | related domain skills | — |
| fetch-metadata-sec-headers | `fetch-metadata-sec-headers` | related domain skills | — |
| content-type-sniffing-defense | `content-type-sniffing-defense` | related domain skills | — |
| http-cache-poisoning-basics | `http-cache-poisoning-basics` | related domain skills | — |
| aws-kms-key-policy-basics | `aws-kms-key-policy-basics` | related domain skills | — |
| azure-managed-identity-basics | `azure-managed-identity-basics` | related domain skills | — |
| gcp-workload-identity-federation | `gcp-workload-identity-federation` | related domain skills | — |

