# Bundled Skill Index

Bundle: `E:\download\all-skills-bundle-20260710.zip`

Read bundled skills with:

```powershell
tar -xOf "E:\download\all-skills-bundle-20260710.zip" "agents-skills/<skill-name>/SKILL.md"
```

Use the selected bundled skill's own `SKILL.md` as authoritative. If it points to adjacent files, read only the required files under `agents-skills/<skill-name>/`.

## General Security Routing

- `hack` - broad security tasks when no narrower skill is obvious.
- `recon-and-methodology` - security methodology, test planning, recon workflow.
- `recon-for-sec` - recon-focused security investigation.
- `api-sec` - broad API security review or testing.
- `auth-sec` - broad authentication and session security.
- `injection-checking` - general injection triage when the exact injection class is unclear.
- `business-logic-vuln` - business logic vulnerability review.
- `business-logic-vulnerabilities` - deeper business logic scenarios, checklists, and methodology.

## Web And API Security

- `401-403-bypass-techniques` - 401/403 bypass, forbidden endpoint behavior, path/header/method tricks.
- `api-auth-and-jwt-abuse` - API auth, JWT abuse, token validation, algorithm/key confusion.
- `api-authorization-and-bola` - BOLA/IDOR-style API authorization failures.
- `api-recon-and-docs` - OpenAPI, Swagger, hidden API docs, endpoint discovery.
- `authbypass-authentication-flaws` - login bypass and authentication logic flaws.
- `clickjacking` - frame embedding and UI redress issues.
- `cors-cross-origin-misconfiguration` - CORS origin, credential, and preflight misconfigurations.
- `crlf-injection` - CRLF, header splitting, response splitting.
- `csp-bypass-advanced` - CSP bypass, script policy edge cases, nonce/hash/source expression weaknesses.
- `csrf-cross-site-request-forgery` - CSRF analysis and token/session workflow checks.
- `dangling-markup-injection` - dangling markup and HTML exfiltration patterns.
- `dependency-confusion` - package namespace confusion and dependency supply-chain checks.
- `dns-rebinding-attacks` - DNS rebinding and browser-to-internal target behavior.
- `email-header-injection` - email header injection and mail workflow abuse.
- `graphql-and-hidden-parameters` - GraphQL introspection, hidden params, field abuse.
- `http-host-header-attacks` - Host header poisoning, reset links, cache interactions.
- `http-parameter-pollution` - duplicate parameter parsing and HPP behavior.
- `http2-specific-attacks` - HTTP/2 parsing, downgrading, and protocol edge cases.
- `idor-broken-object-authorization` - object-level authorization and IDOR.
- `insecure-source-code-management` - exposed `.git`, SCM leaks, source disclosure.
- `jwt-oauth-token-attacks` - JWT, OAuth, token substitution, token replay.
- `oauth-oidc-misconfiguration` - OAuth/OIDC redirect, nonce, state, issuer, audience issues.
- `open-redirect` - redirect validation and URL parser discrepancies.
- `prototype-pollution` - JavaScript prototype pollution.
- `prototype-pollution-advanced` - prototype pollution gadget hunting and known gadgets.
- `race-condition` - race windows, TOCTOU, concurrency exploitation.
- `request-smuggling` - HTTP request smuggling including H2 variants.
- `saml-sso-assertion-attacks` - SAML assertion, signature, audience, and relay-state issues.
- `subdomain-takeover` - dangling DNS and takeover candidates.
- `type-juggling` - PHP/weak comparison and type confusion bugs.
- `upload-insecure-files` - insecure upload validation, content-type, extension, parser behavior.
- `waf-bypass-techniques` - WAF normalization and bypass research.
- `web-cache-deception` - cache deception, path confusion, and static/dynamic boundary bugs.
- `websocket-security` - WebSocket auth, origin, message parsing, and state bugs.

## Injection Classes

- `cmdi-command-injection` - command injection and shell metacharacter behavior.
- `csv-formula-injection` - spreadsheet formula injection.
- `deserialization-insecure` - insecure deserialization, Java gadget chains, object injection.
- `expression-language-injection` - EL injection in Java/JSP/Spring-style environments.
- `file-access-vuln` - arbitrary file read/write and unsafe path use.
- `jndi-injection` - JNDI/LDAP/RMI injection patterns.
- `nosql-injection` - NoSQL query injection and operator abuse.
- `path-traversal-lfi` - path traversal, LFI, include wrappers, file disclosure.
- `sqli-sql-injection` - SQL injection, SQLMap scenarios, DB-specific behavior.
- `ssrf-server-side-request-forgery` - SSRF, URL parser tricks, metadata/internal targets.
- `ssti-server-side-template-injection` - SSTI engines, payload families, template contexts.
- `xss-cross-site-scripting` - reflected, stored, DOM XSS, sinks, filters.
- `xslt-injection` - XSLT injection and XML transform abuse.
- `xxe-xml-external-entity` - XXE, external entities, DTD, parser behavior.

## Active Directory, Windows, And Enterprise

- `active-directory-acl-abuse` - AD ACLs, BloodHound paths, delegated rights abuse.
- `active-directory-certificate-services` - ADCS ESC chains and certificate template issues.
- `active-directory-kerberos-attacks` - Kerberos attack chains and ticket behavior.
- `ntlm-relay-coercion` - NTLM relay, coercion methods, relay paths.
- `windows-av-evasion` - Windows AV evasion research.
- `windows-lateral-movement` - Windows lateral movement techniques.
- `windows-privilege-escalation` - Windows privilege escalation checks.
- `unauthorized-access-common-services` - common exposed services and unauthorized access checks.

## Linux, macOS, Cloud, And Containers

- `container-escape-techniques` - Docker/container escape and host boundary analysis.
- `kubernetes-pentesting` - Kubernetes security checks and cluster attack paths.
- `linux-lateral-movement` - Linux lateral movement.
- `linux-privilege-escalation` - Linux privesc, SUID, capabilities, kernel checklist.
- `linux-security-bypass` - Linux security feature bypass analysis.
- `macos-process-injection` - macOS process injection, dylib, XPC techniques.
- `macos-security-bypass` - macOS TCC and security bypass matrix.
- `sandbox-escape-techniques` - sandbox escape, Python sandbox, seccomp bypass.
- `tunneling-and-pivoting` - tunneling, pivoting, port forwarding, proxy chains.

## Mobile Security

- `android-pentesting-tricks` - Android pentesting and Frida scripts.
- `ios-pentesting-tricks` - iOS runtime tricks and mobile app testing.
- `mobile-ssl-pinning-bypass` - SSL pinning bypass and mobile TLS inspection.

## Reverse Engineering, Deobfuscation, And Binary Analysis

- `anti-debugging-techniques` - anti-debugging detection and bypass analysis.
- `anti-reversing-techniques` - anti-reversing, anti-analysis, VM/packer awareness.
- `arbitrary-write-to-rce` - arbitrary write primitive analysis toward code execution.
- `ast-deobfuscation` - Babel AST JavaScript deobfuscation pipelines and site-specific patterns.
- `binary-analysis-patterns` - compiled-code static analysis and pattern recognition.
- `binary-lifting` - machine code to LLVM IR and lifting workflows.
- `binary-protection-bypass` - ASLR, PIE, NX, canary, RELRO, CET, MTE bypass analysis.
- `code-obfuscation-deobfuscation` - junk code, opaque predicates, self-modifying code, VM protection, string encryption.
- `ctf-reverse` - CTF reverse engineering for binaries, APKs, WASM, firmware, custom VMs, bytecode.
- `deep-analysis` - focused depth-first binary investigation after triage.
- `deobf-all` - master router for native, JavaScript, VM-protected, packed, or CTF deobfuscation.
- `java-decompile` - inspect Java dependency classes and method signatures.
- `vm-and-bytecode-reverse` - custom VM, bytecode, dispatcher, and maze-style reversing.

## Exploit Development

- `browser-exploitation-v8` - V8/browser exploitation patterns.
- `format-string-exploitation` - format-string vulnerability exploitation.
- `heap-exploitation` - heap exploitation, house techniques, IO_FILE.
- `kernel-exploitation` - kernel exploitation and mitigation bypass.
- `reverse-shell-techniques` - reverse shell payloads and shell handling.
- `stack-overflow-and-rop` - stack overflow, ROP, offsets, gadgets.
- `symbolic-execution-tools` - angr, Z3, Unicorn, constraint solving.

## Crypto, Hashing, And Stego

- `classical-cipher-analysis` - classical cipher identification and solving.
- `hash-attack-techniques` - hash cracking and hash attack workflows.
- `lattice-crypto-attacks` - lattice-based cryptanalysis.
- `rsa-attack-techniques` - RSA attack catalog and parameter failures.
- `steganography-techniques` - stego tools and hidden-channel analysis.
- `symmetric-cipher-attacks` - block cipher and symmetric crypto attacks.

## Blockchain And AI/ML

- `ai-ml-security` - AI/ML security testing and model/system risks.
- `defi-attack-patterns` - DeFi attack patterns.
- `ghost-bits-cast-attack` - ghost bits cast attack workflows and payload cookbook.
- `llm-prompt-injection` - prompt injection, tool/output injection, jailbreak pattern analysis.
- `smart-contract-vulnerabilities` - Solidity and smart contract vulnerability patterns.

## Forensics And Detection

- `memory-forensics-volatility` - Volatility memory forensics and cheatsheet usage.
- `network-protocol-attacks` - name-resolution poisoning and network protocol attacks.
- `traffic-analysis-pcap` - pcap traffic analysis.
- `yara-rule-authoring` - YARA/YARA-X rule writing and detection engineering.

## Common Combinations

- API target with auth bugs: `api-recon-and-docs` plus `api-auth-and-jwt-abuse` or `api-authorization-and-bola`.
- Web injection unknown: `injection-checking`, then the exact injection skill.
- SSRF plus parser confusion: `ssrf-server-side-request-forgery` plus `open-redirect` or `dns-rebinding-attacks`.
- Java app exploit chain: `deserialization-insecure`, `jndi-injection`, and `java-decompile`.
- AD path: `active-directory-acl-abuse`, `active-directory-kerberos-attacks`, `active-directory-certificate-services`, and `ntlm-relay-coercion`.
- Container or cluster: `container-escape-techniques`, `kubernetes-pentesting`, and `linux-privilege-escalation`.
- Binary CTF: `ctf-reverse`, `binary-protection-bypass`, `anti-debugging-techniques`, and `symbolic-execution-tools`.
- JS obfuscation: `deobf-all`, then `ast-deobfuscation` or `code-obfuscation-deobfuscation`.
- Pwn challenge: `stack-overflow-and-rop`, `heap-exploitation`, `format-string-exploitation`, or `kernel-exploitation`.
- Mobile app: `android-pentesting-tricks` or `ios-pentesting-tricks`, plus `mobile-ssl-pinning-bypass`.
