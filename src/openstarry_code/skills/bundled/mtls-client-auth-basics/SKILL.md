---
name: mtls-client-auth-basics
description: >
  Mutual TLS (mTLS) client authentication basics for owned or authorized systems:
  client cert trust, require-and-verify config, identity mapping, revocation, and
  common misconfigs. Use when designing or reviewing mTLS between services or APIs,
  debugging client-certificate failures, assessing optional vs required client auth,
  or hardening private-key and trust-store handling for client certs.
---

# mTLS Client Auth Basics

**Mutual TLS**: server authenticates the client with an X.509 certificate during the
TLS handshake (plus server-cert validation). Design, config review, authorized assessment,
and remediation — not unlicensed third-party attacks.

## When To Use

| Situation | Direction |
| --- | --- |
| Service/API **requires client certificates** or mesh/B2B mTLS design | **This skill** |
| Failures: `certificate required`, `unknown ca`, handshake alerts | **This skill** |
| Review `ssl_verify_client`, `ClientAuth`, `require_and_verify_client_cert` | **This skill** |
| Optional client certs, SAN/CN→identity, CRL/OCSP gaps | **This skill** |
| HTTPS plaintext when mTLS blocks ordinary proxies (owned) | `tls-plaintext-acquisition` |
| Private keys / PKCS#12 / CA material in repo or images | `secrets-management-hygiene` |
| Cert loaders / auth middleware implementation | `code-quality-standards` |

## Scope And Authorization

- **In scope:** org-owned services, labs, CTFs, or written engagement naming TLS
  terminators, clients, and CAs you may exercise.
- **Out of scope:** forging client certs on systems you do not own; mass Internet mTLS
  probes; using stolen production client keys outside IR/authorized tests.
- Prefer lab/staging CAs and synthetic client certs; follow org PKI for production.
- Treat client private keys, PKCS#12 passphrases, and CA keys as high-tier secrets —
  redact from tickets, logs, and examples.
- Capture only traffic you may terminate or key-log. Do not disable production
  `require` client auth without change window, rollback, and compensating controls.

## Workflow

### 1. Map the trust model

| Field | Capture |
| --- | --- |
| TLS terminator | LB, ingress, mesh sidecar, app |
| Client auth mode | off / optional / required |
| Trust anchors | CA bundle, SPIFFE trust domain, mesh CA |
| Checks | chain, expiry, SAN/CN, key usage / `clientAuth` EKU |
| Identity map | SAN URI/DNS/email → principal / SPIFFE ID / ACL |
| Revocation | CRL, OCSP, or short-lived certs + automation |
| Downstream | re-verify at app vs proxy-injected identity headers only |

```text
Client (+ cert/key) ⇄ TLS: server cert + client cert
  Server verifies client chain against trust store (+ optional CRL/OCSP)
  App maps verified identity → authorization
```

### 2. Baseline happy path (authorized)

1. Connect with a **valid** client cert from the trusted CA; confirm app success.
2. Log verified subject/SAN/fingerprint only — never the private key.
3. Note end-to-end mTLS vs edge terminate + re-encrypt or plaintext east-west.

```bash
# Owned/lab only
openssl s_client -connect app.example:443 -servername app.example \
  -cert client.crt -key client.key -CAfile ca.crt </dev/null
curl -vk --cert client.crt --key client.key --cacert ca.crt https://app.example/health
```

### 3. Config and policy review

| Check | Secure baseline | Common failure |
| --- | --- | --- |
| Mode | **Required** on sensitive listeners | Optional → unauthenticated still reaches app |
| Trust store | Pin org/mesh CA only | System public roots for client auth |
| Identity | Allowlist SAN/SPIFFE patterns | Any cert from CA → full access |
| EKU | Expect `clientAuth` | Server certs accepted as clients |
| Lifetime / revoke | Short-lived + CRL/OCSP or rapid expire | Multi-year keys; no revoke path |
| Headers | Edge overwrites identity after local verify | App trusts client-sent `X-SSL-Client-*` |
| TLS version | 1.2+ (prefer 1.3) | Legacy protocols on mTLS ports |

### 4. Authorized negative tests

Minimal in-scope probes; one clear reject per class is enough:

1. **No cert** when required → fail closed.
2. **Wrong CA** / self-signed client → reject.
3. **Expired** / not-yet-valid → reject.
4. **Valid CA, wrong SAN** (other env/service) → reject or least privilege.
5. **Optional mode:** unauthenticated must not perform privileged actions.
6. **Header spoof:** backend request with forged client-identity headers and no cert —
   must not trust unless path is private and edge always overwrites.

Do not flood handshakes or brute-force serials against shared production.

### 5. Keys, debug, implement, remediate

- **Keys:** no private keys in git/images; secret store or workload identity; separate
  dev/stage/prod CAs or name constraints → `secrets-management-hygiene`.
- **Debug:** server TLS logs and authorized key logging; if proxies stay empty, use
  `tls-plaintext-acquisition` on owned clients. Check clock skew, chain send, SNI.
- **Code:** fail closed if trust bundle missing; parse peer cert from TLS stack, not
  untrusted headers; log fingerprint/subject only → `code-quality-standards`.
- **Remediate:** require+verify; pin CA; SAN/SPIFFE allowlists; short-lived certs or
  revoke; strip spoofable identity headers; env-separated trust.

## Routing

| Need | Skill |
| --- | --- |
| mTLS design, require/verify, identity map, misconfig assessment | **This skill** |
| Plaintext capture when mTLS blocks MITM proxy (owned) | `tls-plaintext-acquisition` |
| Client/CA keys, PKCS#12, rotation, no secrets in VCS | `secrets-management-hygiene` |
| Safe cert load, middleware, tests, error paths | `code-quality-standards` |

**Required helpers:** `tls-plaintext-acquisition` (owned plaintext under mTLS);
`secrets-management-hygiene` (key/CA lifecycle); `code-quality-standards` (cert load / client-auth code).

## Output Checklist

- [ ] Authorization/scope recorded (hosts, CAs, clients)
- [ ] Trust model: terminator, mode, anchors, identity map, revocation
- [ ] Happy-path valid client cert evidenced
- [ ] Negatives: no cert, wrong CA, expired, wrong identity (as applicable)
- [ ] Optional vs required and header-spoof risk assessed
- [ ] Key material hygiene checked (`secrets-management-hygiene`)
- [ ] Debug used authorized methods if needed (`tls-plaintext-acquisition`)
- [ ] Code/config changes meet `code-quality-standards` (fail closed, no key logs)
- [ ] Residual risk documented; secrets redacted from evidence

## Rules

- **Authorized systems only.** Defense, hardening, and scoped assessment.
- mTLS authenticates the TLS client — still enforce app authorization on mapped identity.
- Optional client auth is not authentication for privileged routes.
- Never paste live private keys or production PKCS#12 into tickets or chat.
- Clean negatives (all probes correctly rejected) are valuable — report them.
