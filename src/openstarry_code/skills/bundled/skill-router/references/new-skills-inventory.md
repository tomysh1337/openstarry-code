# New Skills Inventory (2026-07 expansion)

Write root: `E:\DESKTOP\skill/`  
Count: **49** primary skills from expansions (29 first wave + 20 continue; desktop total dirs ~67 including legacy RE/network/design)  
Authoring: multi-agent parallel batches + integration pass  
Research grounding: PortSwigger/OWASP-style web methodology, CSDN SQLi blind notes, public CTF pwn/crypto/forensics writeups, GTFOBins/privesc checklists

## Trigger map (one line each)

| Skill | Route trigger (short) |
| --- | --- |
| `injection-checking` | Unknown injection class; triage before SQLi/XSS/… |
| `sqli-sql-injection` | SQL injection, UNION, blind SQL, sqlmap |
| `xss-cross-site-scripting` | XSS reflected/stored/DOM, innerHTML, CSP |
| `ssrf-server-side-request-forgery` | SSRF, webhook fetch, 169.254.169.254 |
| `cmdi-command-injection` | OS command injection, shell metachar |
| `ssti-server-side-template-injection` | SSTI, Jinja/Twig/Freemarker |
| `csv-formula-injection` | CSV/Excel formula injection, export sanitize |
| `expression-language-injection` | EL/SpEL/OGNL expression injection (authorized) |
| `xxe-xml-external-entity` | XXE, external entity, DTD |
| `path-traversal-lfi` | Path traversal, LFI, php://filter |
| `zip-slip-path-safety` | Zip slip, archive extract path traversal |
| `idor-broken-object-authorization` | IDOR, BOLA, object ID swap |
| `api-auth-and-jwt-abuse` | JWT none/alg/kid, API auth flaws |
| `csrf-cross-site-request-forgery` | CSRF, SameSite, state-changing GET |
| `cors-cross-origin-misconfiguration` | CORS origin reflection, null origin |
| `race-condition` | Race, TOCTOU, limit overrun |
| `request-smuggling` | CL.TE, TE.CL, HTTP smuggling |
| `http2-specific-attacks` | HTTP/2 desync, H2.CL, H2.TE, H2.0, authorized |
| `captcha-bypass-research` | CAPTCHA control research, labs only, not fraud |
| `rate-limit-bypass-testing` | Rate limit keying, XFF, anti-automation |
| `open-redirect` | Open redirect, OAuth redirect abuse |
| `business-logic-vuln` | Business logic, workflow abuse |
| `api-recon-and-docs` | OpenAPI, Swagger, hidden API |
| `401-403-bypass-techniques` | 401/403 bypass path/header tricks |
| `stack-overflow-and-rop` | Stack overflow, ROP, ret2libc, pwntools |
| `heap-exploitation` | Heap UAF/tcache CTF methodology |
| `format-string-exploitation` | Format string %p / write |
| `rsa-attack-techniques` | RSA CTF, Wiener, common modulus |
| `hash-attack-techniques` | hashcat, length extension |
| `classical-cipher-analysis` | Caesar, Vigenère, substitution |
| `traffic-analysis-pcap` | PCAP triage, tshark streams |
| `memory-forensics-volatility` | Volatility 3 memory dump |
| `android-pentesting-tricks` | Android adb/jadx/frida authorized |
| `steganography-techniques` | Stego CTF, zsteg, steghide |
| `websocket-security` | WebSocket auth, origin, CSWSH |
| `prototype-pollution` | JS `__proto__` merge/clone pollution, gadgets high-level |
| `deserialization-insecure` | Java/PHP/Python insecure deserial, gadget awareness |
| `nosql-injection` | MongoDB `$ne`/`$gt`/`$where`, JSON operator injection |
| `jndi-injection` | JNDI/LDAP/RMI, Log4Shell-class OOB detection |
| `crlf-injection` | CRLF header injection, response splitting |
| `type-juggling` | PHP loose `==` / type confusion, magic hashes |
| `dependency-confusion` | Package namespace confusion, private vs public registry |
| `recon-and-methodology` | Security test planning, recon workflow |
| `upload-insecure-files` | Insecure file upload, MIME/extension/polyglot |
| `waf-bypass-techniques` | WAF bypass research (authorized) |
| `graphql-and-hidden-parameters` | GraphQL introspection, hidden fields |
| `subdomain-takeover` | Dangling DNS takeover candidates |
| `clickjacking` | UI redress, frame-ancestors |
| `http-host-header-attacks` | Host header poisoning |
| `password-reset-poisoning` | Password reset / magic-link Host or token poisoning |
| `session-fixation-management` | Session fixation; SID not regenerated on login |
| `mfa-bypass-methodology` | MFA/2FA bypass; backup codes; step-up; response manip |
| `rate-limit-bypass-testing` | Rate limit bypass; XFF/IP keying; rotation awareness |
| `oauth-oidc-misconfiguration` | OAuth/OIDC misconfiguration |
| `saml-sso-basics` | SAML SSO signature, audience, ACS (authorized) |
| `account-takeover-methodology` | Multi-vector ATO chaining (reset/session/IDOR/token) |
| `dns-rebinding-attacks` | DNS rebinding research |
| `file-access-vuln` | Arbitrary file access (broad) |
| `linux-privilege-escalation` | Linux privesc lab/CTF |
| `windows-privilege-escalation` | Windows privesc lab |
| `container-escape-techniques` | Docker/container escape misconfig (lab only) |
| `kubernetes-pentesting` | K8s RBAC/secrets authorized assessment |
| `ios-pentesting-tricks` | iOS authorized lab testing |
| `symmetric-cipher-attacks` | ECB/padding/CTR CTF |
| `llm-prompt-injection` | LLM prompt/tool injection |
| `ai-ml-security` | ML/LLM system security, supply chain, poisoning awareness, model exposure |
| `smart-contract-vulnerabilities` | Solidity reentrancy/access control/oracle audit & CTF |
| `threat-modeling-stride` | STRIDE workshop, DFD, 威胁建模, design-time threat register |
| `secrets-management-hygiene` | Secrets management, 密钥管理, vault, rotation, .env secrets |
| `secure-sdlc-checklist` | Secure SDLC, SSDLC, 安全开发生命周期, phase gates, RACI |
| `sast-dast-tooling-usage` | SAST, DAST, 静态扫描, scanner triage, CI security gates |
| `terraform-security-basics` | Terraform security, tfstate secrets, public S3, IAM least privilege |
| `nginx-security-headers` | nginx security headers, HSTS/CSP/XFO, TLS edge, server_tokens |
| `redis-security-misconfig` | Redis bind, AUTH/ACL, dangerous commands, unauthorized exposure |

## Continue batch inventory (this goal)

See also: absolute names in continue verification list under scratch `continue-new-skills-inventory.txt` (20 skills).

## Batches

- **A** Injection (6): injection-checking, sqli, xss, ssrf, cmdi, ssti  
- **B** Auth/API (7): idor, jwt, csrf, path-lfi, xxe, cors, race  
- **C** Advanced web (5): smuggling, open-redirect, business-logic, api-recon, 401-403  
- **D** Pwn/crypto (6): stack-rop, heap, format-string, rsa, hash, classical-cipher  
- **E** Forensics/mobile (5): traffic-pcap, volatility, android, stego, websocket-security  
- **F** Recon/platform (5): recon-and-methodology, upload, waf, graphql, subdomain-takeover  
- **G** Injection expansion (5): prototype-pollution, deserialization, nosql, jndi, crlf  
- **H** Auth/host/client (5): clickjacking, host-header, oauth-oidc, dns-rebinding, file-access  
- **I** Privesc/mobile/crypto/AI (5): linux/windows privesc, ios, symmetric, llm-prompt  


## Related agents-tree skills (not duplicated here)

See `C:\Users\18857\.agents\skills\` for `deobf-all`, `ctf-reverse`, `deep-analysis`, `jadx`, `yara-rule-authoring`, etc.

## Style / comments / docs batch (10 agents × 2 = 20)

| Skill | Route trigger (short) |
| --- | --- |
| `comment-writing-standards` | Comments, 写注释, comment style |
| `naming-conventions-general` | Naming, 命名规范 |
| `python-style-and-typing` | Python style, typing, 类型注解 |
| `docstring-and-typedoc` | Docstring, JSDoc, TSDoc, 文档字符串 |
| `typescript-style-and-eslint` | TypeScript style, ESLint |
| `prettier-eslint-editorconfig` | Prettier, EditorConfig, 格式化 |
| `go-style-conventions` | Go style, gofmt |
| `rust-style-and-clippy` | Rust style, clippy, rustfmt |
| `java-style-and-javadoc` | Java style, Javadoc |
| `csharp-style-conventions` | C# style, .NET naming |
| `api-documentation-writing` | API docs, OpenAPI prose, 写接口文档 |
| `readme-and-contributing-docs` | README, CONTRIBUTING |
| `commit-message-conventions` | Commit message, Conventional Commits, 提交信息 |
| `git-workflow-conventions` | Git branch, workflow, 分支策略 |
| `pr-description-writing` | PR description, 写 PR, Why/What/Test |
| `changelog-and-release-notes` | Changelog, release notes, 更新日志 |
| `markdown-docs-style` | Markdown docs style |
| `code-review-comments-style` | Review comments, 评审意见 |
| `shell-script-style` | Bash style, shellcheck |
| `sql-style-conventions` | SQL style, SQL 规范 |
| `error-message-ux-writing` | Error messages, 错误文案 |
| `logging-message-style` | Logging style, 日志规范 |

Batch **J** style/docs (20) via 10 parallel agents.

## Continue-next batch (10 agents × 2 = 20)

| Skill | Trigger |
| --- | --- |
| `http-parameter-pollution` | HPP, duplicate query params |
| `web-cache-deception` | Cache deception, path confusion |
| `dependency-confusion` | Dependency confusion, namespace hijack |
| `type-juggling` | PHP type juggling, loose == |
| `csv-formula-injection` | CSV/Excel formula injection |
| `expression-language-injection` | SpEL, OGNL, Java EL |
| `container-escape-techniques` | Container escape lab |
| `kubernetes-pentesting` | K8s authorized pentest |
| `frida-hooking-playbook` | Frida hooks, owned apps |
| `firmware-analysis-basics` | Firmware binwalk triage |
| `smart-contract-vulnerabilities` | Solidity reentrancy, access control |
| `ai-ml-security` | ML/LLM system security |
| `unit-testing-style` | Unit tests, 单元测试 |
| `mocking-and-test-doubles` | Mocks, fakes, stubs |
| `property-based-testing` | Property-based testing, 属性测试, hypothesis, fast-check |
| `performance-testing-basics` | Performance testing, 性能测试, load test |
| `git-workflow-conventions` | Git branch, 分支策略 |
| `pr-description-writing` | PR description, 写 PR |
| `async-concurrency-patterns` | Async concurrency design |
| `api-versioning-design` | API versioning, 接口版本 |
| `dockerfile-best-practices` | Dockerfile best practices |
| `ci-cd-pipeline-patterns` | CI/CD pipelines, 持续集成 |

Batch **K** continue-next via 10 parallel agents.

## Continue-again batch (10 agents × 2 = 20)

| Skill | Trigger |
| --- | --- |
| `ldap-injection` | LDAP injection |
| `mass-assignment` | Mass assignment, over-posting |
| `session-fixation-management` | Session fixation |
| `password-reset-poisoning` | Password reset poisoning |
| `content-security-policy-bypass` | CSP bypass research |
| `postmessage-security` | postMessage origin |
| `threat-modeling-stride` | STRIDE, 威胁建模 |
| `secrets-management-hygiene` | Secrets, 密钥管理 |
| `sbom-and-supply-chain` | SBOM, supply chain |
| `bug-bounty-methodology` | Bug bounty methodology |
| `secure-sdlc-checklist` | Secure SDLC, 安全开发生命周期 |
| `sast-dast-tooling-usage` | SAST, DAST, 静态扫描 |
| `accessibility-a11y-checklist` | a11y, 无障碍 |
| `i18n-l10n-guidelines` | i18n, 国际化 |
| `react-component-patterns` | React components |
| `state-management-guidelines` | State management |
| `json-schema-design` | JSON Schema |
| `database-migration-safety` | DB migrations |
| `caching-strategies` | Caching, 缓存 |
| `retry-backoff-patterns` | Retry, backoff |
| `observability-metrics-tracing` | Observability, 可观测性 |
| `feature-flag-patterns` | Feature flags, 功能开关 |

Batch **L** continue-again via 10 parallel agents.

## 30-agent mega-batch (60 skills)
| `android-exported-components` | mega-batch 30-agent wave |
| `android-webview-security` | mega-batch 30-agent wave |
| `api-rate-limit-design` | mega-batch 30-agent wave |
| `apk-signing-and-integrity` | mega-batch 30-agent wave |
| `aws-iam-least-privilege` | mega-batch 30-agent wave |
| `aws-s3-bucket-hardening` | mega-batch 30-agent wave |
| `azure-blob-misconfig` | mega-batch 30-agent wave |
| `backpressure-patterns` | mega-batch 30-agent wave |
| `browser-extension-security` | mega-batch 30-agent wave |
| `bulkhead-isolation` | mega-batch 30-agent wave |
| `chaos-engineering-basics` | mega-batch 30-agent wave |
| `circuit-breaker-patterns` | mega-batch 30-agent wave |
| `clickjacking-ui-redress-deep` | mega-batch 30-agent wave |
| `cloud-metadata-ssrf-defenses` | mega-batch 30-agent wave |
| `contract-testing-pact` | mega-batch 30-agent wave |
| `cookie-security-flags` | mega-batch 30-agent wave |
| `cors-credentialed-requests` | mega-batch 30-agent wave |
| `django-security-settings` | mega-batch 30-agent wave |
| `docker-compose-security` | mega-batch 30-agent wave |
| `e2e-testing-playwright` | mega-batch 30-agent wave |
| `electron-app-security` | mega-batch 30-agent wave |
| `express-middleware-security` | mega-batch 30-agent wave |
| `fastapi-security-patterns` | mega-batch 30-agent wave |
| `file-upload-polyglot-detection` | mega-batch 30-agent wave |
| `firewall-rule-review` | mega-batch 30-agent wave |
| `gcp-iam-basics` | mega-batch 30-agent wave |
| `ghidra-scripting-basics` | mega-batch 30-agent wave |
| `graphql-schema-design-style` | mega-batch 30-agent wave |
| `grpc-security-testing` | mega-batch 30-agent wave |
| `host-header-cache-poison` | mega-batch 30-agent wave |
| `ida-python-basics` | mega-batch 30-agent wave |
| `idor-graphql-nodes` | mega-batch 30-agent wave |
| `ios-keychain-hygiene` | mega-batch 30-agent wave |
| `jwt-refresh-token-patterns` | mega-batch 30-agent wave |
| `kubernetes-network-policy` | mega-batch 30-agent wave |
| `laravel-security-basics` | mega-batch 30-agent wave |
| `linux-hardening-checklist` | mega-batch 30-agent wave |
| `load-shedding-patterns` | mega-batch 30-agent wave |
| `mfa-enrollment-flaws` | mega-batch 30-agent wave |
| `mutation-testing-basics` | mega-batch 30-agent wave |
| `nextjs-security-checklist` | mega-batch 30-agent wave |
| `nodejs-security-checklist` | mega-batch 30-agent wave |
| `oauth-pkce-checklist` | mega-batch 30-agent wave |
| `openapi-contract-testing` | mega-batch 30-agent wave |
| `open-redirect-advanced` | mega-batch 30-agent wave |
| `protobuf-api-design` | mega-batch 30-agent wave |
| `rails-security-checklist` | mega-batch 30-agent wave |
| `same-site-cookie-pitfalls` | mega-batch 30-agent wave |
| `saml-signature-wrapping-awareness` | mega-batch 30-agent wave |
| `secrets-in-ci-pipelines` | mega-batch 30-agent wave |
| `service-worker-security` | mega-batch 30-agent wave |
| `spring-security-checklist` | mega-batch 30-agent wave |
| `ssh-key-hygiene` | mega-batch 30-agent wave |
| `ssrf-filter-bypass-catalog` | mega-batch 30-agent wave |
| `strings-and-ioc-triage` | mega-batch 30-agent wave |
| `websocket-authz-deep` | mega-batch 30-agent wave |
| `websocket-client-patterns` | mega-batch 30-agent wave |
| `windows-hardening-basics` | mega-batch 30-agent wave |
| `xxe-billion-laughs-defenses` | mega-batch 30-agent wave |
| `yara-hunting-workflow` | mega-batch 30-agent wave |

Batch **M** via 30 parallel agents.


## 100-agent mega-batch (100 skills)
| `oauth-device-code-flow` | mega-batch 100-agent wave |
| `oauth-implicit-flow-risks` | mega-batch 100-agent wave |
| `oidc-id-token-validation` | mega-batch 100-agent wave |
| `session-cookie-theft-defense` | mega-batch 100-agent wave |
| `remember-me-token-security` | mega-batch 100-agent wave |
| `password-policy-design` | mega-batch 100-agent wave |
| `account-lockout-design` | mega-batch 100-agent wave |
| `login-csrf-defense` | mega-batch 100-agent wave |
| `sso-logout-propagation` | mega-batch 100-agent wave |
| `saml-metadata-hygiene` | mega-batch 100-agent wave |
| `jwt-audience-issuer-checks` | mega-batch 100-agent wave |
| `api-key-lifecycle` | mega-batch 100-agent wave |
| `mtls-client-auth-basics` | mega-batch 100-agent wave |
| `device-binding-tokens` | mega-batch 100-agent wave |
| `step-up-auth-patterns` | mega-batch 100-agent wave |
| `magic-link-auth-security` | mega-batch 100-agent wave |
| `passkeys-webauthn-basics` | mega-batch 100-agent wave |
| `totp-mfa-implementation` | mega-batch 100-agent wave |
| `backup-code-storage` | mega-batch 100-agent wave |
| `session-timeout-design` | mega-batch 100-agent wave |
| `dom-clobbering-awareness` | mega-batch 100-agent wave |
| `prototype-pollution-defenses` | mega-batch 100-agent wave |
| `css-injection-exfiltration` | mega-batch 100-agent wave |
| `svg-xss-hardening` | mega-batch 100-agent wave |
| `markdown-xss-sanitization` | mega-batch 100-agent wave |
| `html-sanitizer-selection` | mega-batch 100-agent wave |
| `trusted-types-adoption` | mega-batch 100-agent wave |
| `subresource-integrity-sri` | mega-batch 100-agent wave |
| `mixed-content-hardening` | mega-batch 100-agent wave |
| `clickjacking-frame-busting` | mega-batch 100-agent wave |
| `tabnabbing-noopener` | mega-batch 100-agent wave |
| `download-attribute-security` | mega-batch 100-agent wave |
| `cors-preflight-cache` | mega-batch 100-agent wave |
| `jsonp-legacy-risks` | mega-batch 100-agent wave |
| `flash-crossdomain-legacy` | mega-batch 100-agent wave |
| `websocket-origin-validation` | mega-batch 100-agent wave |
| `graphql-batching-limits` | mega-batch 100-agent wave |
| `graphql-query-complexity` | mega-batch 100-agent wave |
| `api-pagination-security` | mega-batch 100-agent wave |
| `http-method-override-risks` | mega-batch 100-agent wave |
| `aws-security-groups-review` | mega-batch 100-agent wave |
| `aws-lambda-least-privilege` | mega-batch 100-agent wave |
| `aws-ecs-task-security` | mega-batch 100-agent wave |
| `aws-rds-public-access` | mega-batch 100-agent wave |
| `azure-keyvault-basics` | mega-batch 100-agent wave |
| `azure-nsg-review` | mega-batch 100-agent wave |
| `gcp-firewall-rules` | mega-batch 100-agent wave |
| `gcp-storage-public-access` | mega-batch 100-agent wave |
| `helm-chart-security` | mega-batch 100-agent wave |
| `kubernetes-pod-security` | mega-batch 100-agent wave |
| `kubernetes-secrets-handling` | mega-batch 100-agent wave |
| `istio-authz-basics` | mega-batch 100-agent wave |
| `terraform-state-locking` | mega-batch 100-agent wave |
| `ansible-vault-usage` | mega-batch 100-agent wave |
| `pulumi-secrets-basics` | mega-batch 100-agent wave |
| `cloudformation-iam-guardrails` | mega-batch 100-agent wave |
| `vault-agent-injection` | mega-batch 100-agent wave |
| `sealed-secrets-patterns` | mega-batch 100-agent wave |
| `external-secrets-operator` | mega-batch 100-agent wave |
| `cert-manager-basics` | mega-batch 100-agent wave |
| `sql-injection-defenses-orm` | mega-batch 100-agent wave |
| `nosql-injection-defenses` | mega-batch 100-agent wave |
| `command-injection-defenses` | mega-batch 100-agent wave |
| `path-traversal-defenses` | mega-batch 100-agent wave |
| `ssrf-allowlist-design` | mega-batch 100-agent wave |
| `xxe-parser-hardening` | mega-batch 100-agent wave |
| `deserialization-safe-formats` | mega-batch 100-agent wave |
| `file-upload-secure-storage` | mega-batch 100-agent wave |
| `postgresql-security-settings` | mega-batch 100-agent wave |
| `mysql-security-hardening` | mega-batch 100-agent wave |
| `elasticsearch-security-basics` | mega-batch 100-agent wave |
| `kafka-acl-basics` | mega-batch 100-agent wave |
| `rabbitmq-security-basics` | mega-batch 100-agent wave |
| `redis-acl-design` | mega-batch 100-agent wave |
| `mongodb-auth-hardening` | mega-batch 100-agent wave |
| `typescript-strict-migration` | mega-batch 100-agent wave |
| `python-packaging-modern` | mega-batch 100-agent wave |
| `go-module-hygiene` | mega-batch 100-agent wave |
| `rust-unsafe-guidelines` | mega-batch 100-agent wave |
| `java-module-system-basics` | mega-batch 100-agent wave |
| `dependency-pinning-strategies` | mega-batch 100-agent wave |
| `license-compliance-scan` | mega-batch 100-agent wave |
| `codeowners-review-routing` | mega-batch 100-agent wave |
| `branch-protection-rules` | mega-batch 100-agent wave |
| `signed-commits-basics` | mega-batch 100-agent wave |
| `reproducible-builds-basics` | mega-batch 100-agent wave |
| `container-image-signing` | mega-batch 100-agent wave |
| `sbom-ci-enforcement` | mega-batch 100-agent wave |
| `vulnerability-sla-process` | mega-batch 100-agent wave |
| `security-champion-program` | mega-batch 100-agent wave |
| `react-hooks-security` | mega-batch 100-agent wave |
| `vue-router-auth-guards` | mega-batch 100-agent wave |
| `angular-security-basics` | mega-batch 100-agent wave |
| `svelte-security-notes` | mega-batch 100-agent wave |
| `react-native-security-basics` | mega-batch 100-agent wave |
| `flutter-security-basics` | mega-batch 100-agent wave |
| `cordova-webview-risks` | mega-batch 100-agent wave |
| `pwa-security-checklist` | mega-batch 100-agent wave |
| `cdn-cache-key-design` | mega-batch 100-agent wave |
| `static-asset-fingerprinting` | mega-batch 100-agent wave |

Batch **N** via 100 parallel agents (4 waves of 25).


## 10-agent batch (post-100)
| `oauth-token-binding-dpop` | 10-agent wave post-100 |
| `saml-assertion-encryption` | 10-agent wave post-100 |
| `webauthn-attestation-review` | 10-agent wave post-100 |
| `csp-report-only-rollout` | 10-agent wave post-100 |
| `fetch-metadata-sec-headers` | 10-agent wave post-100 |
| `content-type-sniffing-defense` | 10-agent wave post-100 |
| `http-cache-poisoning-basics` | 10-agent wave post-100 |
| `aws-kms-key-policy-basics` | 10-agent wave post-100 |
| `azure-managed-identity-basics` | 10-agent wave post-100 |
| `gcp-workload-identity-federation` | 10-agent wave post-100 |

Batch **O** via 10 parallel agents.

