---
name: skill-router
description: >
  Route requests to specialized local skills under the skill library root and, when
  no loose local skill fits, the optional all-skills bundle zip. Use when a task
  involves code quality, reverse engineering, web/API vulnerabilities, injection,
  JWT/IDOR, GraphQL, OAuth, file upload, WAF, privesc, pwn/crypto CTF, smart-contract
  audit, AI/ML system security, LLM prompt injection, network traffic, proprietary
  protocols, TLS plaintext, Protobuf/gRPC,
  binary WebSocket, QUIC/HTTP/3, PCAP, forensics, Android/iOS testing, security
  research, binary analysis, language style, comments, docstrings, naming,
  commit messages, README/API docs, logging/error copy, unit testing, git/PR,
  Docker/CI, containers/K8s, Frida/firmware, smart contracts, AI/ML security,
  STRIDE threat modeling, secrets management hygiene, SBOM/supply chain,
  cloud IAM/S3, framework security checklists, resilience patterns,
  mobile RE scripting, or when the user asks to choose, combine, unpack,
  install, or audit local skills.
---

# Skill Router

## Route

1. Classify the artifact, protocol layer, vulnerability class, target platform, and requested action.
2. Read `references/skill-index.md` (English master routing tables).
3. For newly added skills, also see `references/new-skills-inventory.md` (trigger map).
4. Prefer **unpacked** skill directories. Treat adjacent `.zip` files as backups only.
5. Choose **one primary** skill. Add a helper only when it supplies a distinct phase or toolchain.
6. Read the selected `SKILL.md` completely before acting.
7. If the skill has nested phases (e.g. `binary-re/`), open the top-level skill first; load nested skills only as needed.
8. Prefer canonical nested paths over flat aliases (`binary-re/static-analysis` over `binary-re-static-analysis`).
9. Consult `references/bundle-index.md` only if the loose library has no sufficiently specific route.

## Quick Tables

### Network (earliest unresolved layer)

| Problem | Primary | Optional helper |
| --- | --- | --- |
| No HTTPS plaintext | `tls-plaintext-acquisition` | `mobile-ssl-pinning-bypass` (authorized mobile pin) |
| Unknown Protobuf/gRPC body | `protobuf-grpc-reverse-engineering` | TLS skill if still encrypted |
| Binary WebSocket messages | `websocket-binary-reverse-engineering` | protobuf skill if body is Protobuf |
| WebSocket security testing | `websocket-security` | binary WS skill for codecs |
| QUIC or HTTP/3 | `quic-http3-analysis` | TLS skill for endpoint secrets |
| Unknown TCP/UDP protocol | `protocol-reverse-engineering` | `NetworkProtocolAnalysisSkill` for PCAP/dissector |
| PCAP triage | `traffic-analysis-pcap` | `NetworkProtocolAnalysisSkill` for deep tooling |
| Protocol implemented in a binary | `binary-re` | matching network skill |

### Web / API (authorized assessment)

| Problem | Primary |
| --- | --- |
| Test plan / recon | `recon-and-methodology` |
| Injection class unknown | `injection-checking` |
| SQLi / XSS / SSRF / CMDi / SSTI / XXE / LFI / NoSQL / CRLF / JNDI / deserial / prototype / CSV formula / EL-SpEL-OGNL | matching class skill |
| PHP type juggling / loose `==` | `type-juggling` |
| Dependency / package namespace confusion | `dependency-confusion` |
| GraphQL / hidden params | `graphql-and-hidden-parameters` |
| API map missing | `api-recon-and-docs` |
| IDOR/BOLA | `idor-broken-object-authorization` |
| JWT / API auth | `api-auth-and-jwt-abuse` |
| Session fixation / SID not rotated on login | `session-fixation-management` |
| Password reset / magic-link Host or token poisoning | `password-reset-poisoning` |
| MFA / 2FA bypass (skip, backup codes, step-up) | `mfa-bypass-methodology` |
| Rate limit / anti-automation bypass research | `rate-limit-bypass-testing` |
| OAuth / OIDC | `oauth-oidc-misconfiguration` |
| SAML SSO (signature, audience, ACS) | `saml-sso-basics` |
| Multi-vector account takeover (ATO) chaining | `account-takeover-methodology` |
| Upload / WAF / takeover / host / clickjack / file access | matching skill |
| Zip slip / archive extract path escape | `zip-slip-path-safety` |
| Terraform / tfstate / public S3 / IaC IAM | `terraform-security-basics` |
| CSRF / CORS / race / logic | matching skill |
| Smuggling / open redirect / 401-403 | matching skill |
| HTTP/2 desync (H2.CL / H2.TE / H2.0) | `http2-specific-attacks` |
| CAPTCHA / bot-challenge control research (authorized) | `captcha-bypass-research` |
| LLM prompt / tool injection | `llm-prompt-injection` |
| ML/LLM product review (supply chain, poisoning, model exposure) | `ai-ml-security` |
| STRIDE / threat model workshop / 濞佽儊寤烘ā | `threat-modeling-stride` |
| Secrets in code, vault, rotation, 瀵嗛挜绠＄悊, .env | `secrets-management-hygiene` |
| nginx security headers / TLS edge / server_tokens | `nginx-security-headers` |
| Redis bind / AUTH / ACL / dangerous commands | `redis-security-misconfig` |
| Secure SDLC / SSDLC / 瀹夊叏寮€鍙戠敓鍛藉懆鏈?| `secure-sdlc-checklist` |
| SAST / DAST / 闈欐€佹壂鎻?/ scanner noise triage | `sast-dast-tooling-usage` |

### Pwn / crypto / privesc / contracts (CTF-lab)

| Problem | Primary |
| --- | --- |
| Stack overflow / ROP | `stack-overflow-and-rop` |
| Heap CTF | `heap-exploitation` |
| Format string | `format-string-exploitation` |
| RSA / hash / classical / symmetric | matching crypto skill |
| Linux / Windows privesc (lab) | matching privesc skill |
| Container escape / docker.sock / privileged (lab) | `container-escape-techniques` |
| Kubernetes RBAC / secrets / cluster misconfig (lab) | `kubernetes-pentesting` |
| iOS lab testing | `ios-pentesting-tricks` |
| Solidity / smart-contract audit or CTF | `smart-contract-vulnerabilities` |

### Development / style / docs

| Problem | Primary | Notes |
| --- | --- | --- |
| Implement / fix / refactor / review code | Domain skill if any | Always apply `code-quality-standards` as baseline |
| Code quality only (reliability/security/tests) | `code-quality-standards` | 鈥?|
| Comments / 娉ㄩ噴 | `comment-writing-standards` | repo style first |
| Naming / 鍛藉悕 | `naming-conventions-general` | + language skill |
| Python / TS / Go / Rust / Java / C# style | matching `*-style-*` skill | formatter config wins |
| Docstrings / JSDoc / OpenAPI prose | `docstring-and-typedoc` or `api-documentation-writing` | 鈥?|
| README / changelog / commits | matching docs skill | 鈥?|
| Branch strategy / git workflow / 鍒嗘敮绛栫暐 | `git-workflow-conventions` | `pr-description-writing` |
| PR title/body / 鍐?PR | `pr-description-writing` | `git-workflow-conventions` |
| Error copy / logging | `error-message-ux-writing` / `logging-message-style` | 鈥?|
| Review comment wording | `code-review-comments-style` | 鈥?|
| Unit tests / mocks | `unit-testing-style` / `mocking-and-test-doubles` | 鈥?|
| Property-based / 灞炴€ф祴璇?| `property-based-testing` | `unit-testing-style`, CQS |
| Load / perf / 鎬ц兘娴嬭瘯 | `performance-testing-basics` | `observability-metrics-tracing`, CQS |
| Git branch / PR description | `git-workflow-conventions` / `pr-description-writing` | 鈥?|
| Async concurrency design | `async-concurrency-patterns` | not HTTP race skill |
| API versioning | `api-versioning-design` | 鈥?|
| Dockerfile / CI-CD | `dockerfile-best-practices` / `ci-cd-pipeline-patterns` | 鈥?|
| Terraform security / tfstate / public bucket / IAM least privilege | `terraform-security-basics` | `secrets-management-hygiene`, `code-quality-standards` |
| Zip slip / unsafe archive extract | `zip-slip-path-safety` | `path-traversal-lfi`, `file-access-vuln` |
| STRIDE threat modeling / 濞佽儊寤烘ā | `threat-modeling-stride` | `recon-and-methodology` if inventory missing |
| Secrets / vault / rotation / 瀵嗛挜绠＄悊 | `secrets-management-hygiene` | `logging-message-style`, `code-quality-standards` |
| Secure SDLC / SSDLC / 瀹夊叏寮€鍙戠敓鍛藉懆鏈?| `secure-sdlc-checklist` | `sast-dast-tooling-usage`, `threat-modeling-stride`, `code-quality-standards` |
| SAST / DAST / 闈欐€佹壂鎻?/ triage noise | `sast-dast-tooling-usage` | `secure-sdlc-checklist`, `ci-cd-pipeline-patterns` |
| nginx headers / TLS edge / server_tokens | `nginx-security-headers` | `code-quality-standards`, `secrets-management-hygiene`, `NetworkProtocolAnalysisSkill` |
| Redis exposure / AUTH / dangerous commands | `redis-security-misconfig` | `secrets-management-hygiene`, `code-quality-standards`, `NetworkProtocolAnalysisSkill` |
| Container escape / K8s (lab) | matching platform skill | authorized only |
| Frida / firmware | `frida-hooking-playbook` / `firmware-analysis-basics` | 鈥?|
| Smart contract / AI-ML | matching skill | authorized only |
| LDAP / mass assignment / session / reset poison | matching skill | authorized only |
| CSP / postMessage | matching skill | + XSS skill |
| Threat model / secrets / SBOM / bug bounty / SSDLC / SAST-DAST | matching process skill | 鈥?|
| a11y / i18n / React / state | matching frontend skill | + CQS |
| Schema / migrations / cache / retry / OTel / flags | matching reliability skill | 鈥?|

### Binary RE

| Problem | Primary |
| --- | --- |
| Unknown binary | `binary-re` then nested triage/static |
| Disasm / decompile | `binary-re/static-analysis` |
| Tools missing | `binary-re/tool-setup` |
| Ghidra/IDA-specific | `Ghidra_IDAReverseEngineeringSkill` |


### 100-agent mega-batch (summary)

Full tables: `references/skill-index.md` section **100-agent mega-batch routes**.  
Inventory: `references/new-skills-inventory.md` section **100-agent mega-batch**.

| Cluster | Example primaries |
| --- | --- |
| Auth/session/MFA/OAuth deep | `oauth-device-code-flow`, `passkeys-webauthn-basics`, `totp-mfa-implementation`, `sso-logout-propagation` |
| Browser XSS/CORS/SRI | `html-sanitizer-selection`, `trusted-types-adoption`, `subresource-integrity-sri`, `clickjacking-frame-busting` |
| GraphQL/API surface | `graphql-batching-limits`, `graphql-query-complexity`, `api-pagination-security` |
| Cloud/K8s/IaC secrets | `aws-security-groups-review`, `kubernetes-pod-security`, `sealed-secrets-patterns`, `cert-manager-basics` |
| Injection defenses (build) | `sql-injection-defenses-orm`, `ssrf-allowlist-design`, `deserialization-safe-formats` |
| Data stores | `postgresql-security-settings`, `redis-acl-design`, `mongodb-auth-hardening` |
| Supply chain / SDLC | `container-image-signing`, `sbom-ci-enforcement`, `branch-protection-rules` |
| Frontend/mobile | `react-hooks-security`, `vue-router-auth-guards`, `pwa-security-checklist`, `flutter-security-basics` |
| CDN/assets | `cdn-cache-key-design`, `static-asset-fingerprinting` |


### 10-agent batch (post-100)

| Problem | Primary |
| --- | --- |
| OAuth DPoP / token binding | `oauth-token-binding-dpop` |
| SAML assertion encryption | `saml-assertion-encryption` |
| WebAuthn attestation policy | `webauthn-attestation-review` |
| CSP Report-Only rollout | `csp-report-only-rollout` |
| Sec-Fetch-* isolation | `fetch-metadata-sec-headers` |
| MIME sniffing / nosniff | `content-type-sniffing-defense` |
| HTTP cache poisoning triage | `http-cache-poisoning-basics` |
| AWS KMS key policies | `aws-kms-key-policy-basics` |
| Azure managed identity | `azure-managed-identity-basics` |
| GCP Workload Identity Fed | `gcp-workload-identity-federation` |

Full tables: `references/skill-index.md` section **10-agent batch routes (post-100)**.

## Library Location

Resolve the skill library root from this skill鈥檚 install path when possible (parent of `skill-router/`).  
If this library is used as a fixed workspace library, the conventional root is the parent directory of this folder.

## Evidence

Keep originals and derived artifacts separate. Require reproducible evidence before declaring a field, framing rule, key source, or state transition understood. Gate active security testing on ownership or authorization.
