---
name: nginx-security-headers
description: >
  Authorized nginx hardening and assessment: HTTP security headers, TLS
  termination settings, server_tokens, common reverse-proxy and header
  misconfigurations. Use when reviewing nginx.conf / sites-enabled, missing
  CSP/HSTS/XFO, weak TLS, version disclosure, or hardening org-owned edge
  proxies — not for attacking third-party sites without permission.
---

# Nginx Security Headers And Hardening

Assess and harden **nginx** as a reverse proxy or static edge for systems you
own or are explicitly authorized to test. Focus on response headers, TLS
surface, identity disclosure, and common config mistakes that weaken browser
and transport security.

## Scope And Authorization

- **In scope:** org-owned nginx configs, staging/prod under written engagement,
  local labs, CTF targets that include nginx config or edge assessment.
- **Out of scope:** unauthenticated mass scanning of the Internet; exploiting
  third-party edges without permission; DoS (slowloris, large body floods)
  against shared production without explicit approval.
- Prefer **config review + controlled response checks** over aggressive load.
- Capture evidence from **your** test hostnames and accounts; redact cookies,
  tokens, client certs, and internal hostnames from reports when policy requires.
- Do not weaken production TLS or remove auth “just to test” without a rollback
  plan and change window.

## Use When

- Reviewing `nginx.conf`, `conf.d/*`, `sites-enabled/*`, or ingress-nginx /
  OpenResty snippets that terminate HTTP(S)
- Responses lack or weaken **security headers** (CSP, HSTS, XFO, Referrer-Policy,
  Permissions-Policy, COOP/COEP when relevant)
- Edge shows **version banners**, default pages, or debug locations
- TLS ciphers/protocols are outdated; mixed HTTP/HTTPS; missing redirect to HTTPS
- Proxy misconfig: bad `X-Forwarded-*`, open proxy traits, WebSocket upgrade
  without auth notes, path alias / merge_slashes issues
- Chinese/English teams: nginx 安全头, HSTS, server_tokens, TLS 加固, 反向代理误配置

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Clickjacking impact / frame PoC | `clickjacking` |
| CSP bypass / XSS under CSP | `content-security-policy-bypass`, `xss-cross-site-scripting` |
| CORS `Access-Control-*` logic | `cors-cross-origin-misconfiguration` |
| HTTP request smuggling at proxy boundaries | `request-smuggling` |
| Host header / cache poison chains | `http-host-header-attacks`, `web-cache-deception` |
| Application code fixes behind the proxy | `code-quality-standards` |
| Redis/data-store exposure behind the edge | `redis-security-misconfig` |

## Header Baseline (what good looks like)

Values must match **app needs**; over-strict CSP can break prod — stage first.

| Header / control | Typical hardened direction | Notes |
| --- | --- | --- |
| `Strict-Transport-Security` | `max-age≥15552000; includeSubDomains` (+ `preload` only if preload-ready) | HTTPS only; do not set on plain HTTP |
| `Content-Security-Policy` | Default-deny with explicit `script-src` / `object-src 'none'` etc. | App-owned; edge can add baseline + report-uri |
| `X-Frame-Options` | `DENY` or `SAMEORIGIN` | Prefer CSP `frame-ancestors` as primary |
| `Content-Security-Policy: frame-ancestors` | `'none'` or explicit allowlist | Modern clickjacking control |
| `X-Content-Type-Options` | `nosniff` | Low risk to enable broadly |
| `Referrer-Policy` | `strict-origin-when-cross-origin` or stricter | Avoid leaking tokens in query via Referer |
| `Permissions-Policy` | Disable unused powerful features | Camera/mic/geolocation etc. |
| `Cross-Origin-Opener-Policy` | `same-origin` when isolation needed | Coordinate with app (breaks some integrations) |
| `Cross-Origin-Resource-Policy` | `same-site` / `same-origin` for sensitive assets | Not a substitute for auth |
| `server_tokens` | `off` | Hides nginx version in `Server` and error pages |
| Error pages | Custom 4xx/5xx without stack traces | App may still leak; edge should not add more |

**Missing headers alone** may be low severity on static marketing sites; raise
severity when combined with sensitive authenticated UI, weak CSP + XSS sink,
or missing HSTS on login/cookie domains.

## Workflow

### 1. Inventory config and exposure

1. Locate effective config: `nginx -T` (authorized host) or repo templates /
   ConfigMaps / Helm values for ingress-nginx.
2. Map **server_name**, listen ports, TLS cert paths, `root`/`alias`,
   `proxy_pass` upstreams, and which locations are public vs authenticated.
3. Note include order and duplicate `add_header` inheritance quirks (see below).
4. Record whether TLS terminates at nginx, a cloud LB, or both.

```bash
# On an owned host only
nginx -t
nginx -T 2>/dev/null | sed -n '1,200p'   # full dump — store as evidence artifact
```

### 2. Observe live responses (authorized)

```bash
# Replace with in-scope host; do not blast unrelated IPs
curl -sI https://app.example/
curl -sI http://app.example/                 # expect redirect to HTTPS
curl -sI https://app.example/login
curl -vk https://app.example/ 2>&1 | grep -E 'SSL|TLS|subject:|expire'
```

Collect per path when CDNs or location blocks differ:

- Document vs API (`/`, `/api/`, `/static/`)
- Error paths (`/no-such-page`) — `add_header` often **missing** on error
  responses unless `always` is used
- Redirect responses (3xx) — headers may not copy unless configured

### 3. Security headers assessment

For each interesting path, build a matrix: header present / value / path scope.

**Common misconfigs:**

| Pattern | Risk |
| --- | --- |
| `add_header` only in `server`, overridden empty in `location` | Nested `add_header` **replaces** parent list in nginx — easy to drop HSTS/CSP on API location |
| Header only on `200`, not errors | Error pages framable or sniffable |
| HSTS on HTTP server block | Ignored or confusing; enforce HTTPS redirect first |
| CSP `default-src *` / `script-src 'unsafe-inline' 'unsafe-eval'` | Weak; treat as incomplete control |
| `X-Frame-Options: ALLOW-FROM` | Obsolete; ignored by modern browsers |
| Duplicate conflicting CSP/XFO | Document effective browser behavior |
| Security headers only on apex, not `www` / API host | Cookie domain may still be at risk |

### 4. TLS and HTTP→HTTPS

On authorized endpoints:

1. Protocols: disable SSLv3 / TLS 1.0 / 1.1 for public HTTPS unless a documented
   exception exists.
2. Prefer TLS 1.2+ with modern cipher suites; enable TLS 1.3 when clients allow.
3. Certificates: valid chain, not expired, correct SAN; prefer automated renew.
4. Redirect: `return 301 https://$host$request_uri` (or canonical host) on `:80`.
5. HSTS only after HTTPS is stable on all subdomains you include.
6. Optional: OCSP stapling, session tickets policy per org crypto baseline.

```bash
# Lab/owned host examples
openssl s_client -connect app.example:443 -servername app.example </dev/null 2>/dev/null | openssl x509 -noout -dates -subject
nmap --script ssl-enum-ciphers -p 443 app.example   # only if nmap is approved in scope
```

Deep TLS fingerprinting of custom stacks may use `NetworkProtocolAnalysisSkill`
or `tls-plaintext-acquisition` when plaintext/capture is required for the
engagement — not for breaking others’ TLS.

### 5. Server tokens, defaults, and info leaks

1. `server_tokens off;` in `http` or `server`.
2. Remove or protect default welcome page and autoindex (`autoindex off`).
3. Avoid `stub_status` on public interfaces without auth and network allowlists.
4. Do not expose `.git`, backup files, or editor swap via static `root` mistakes.
5. Proxy error bodies: ensure upstream stack traces are not passed through
   unchanged on production.

### 6. Reverse-proxy misconfig (high-signal)

| Check | Why |
| --- | --- |
| `proxy_set_header Host` / `X-Forwarded-For` / `X-Forwarded-Proto` | Wrong Host → cache/host attacks; wrong proto → insecure cookie flags / mixed redirects |
| Trust of client-supplied `X-Forwarded-*` | Only trust from known LB hop; overwrite or use `$proxy_add_x_forwarded_for` carefully |
| `proxy_pass` trailing slash | Path prefix strip bugs → unexpected routing |
| WebSocket `Upgrade` / `Connection` | Missing headers break apps; open upgrades need app auth (see `websocket-security`) |
| Large `client_max_body_size` without app limits | Upload abuse surface (`upload-insecure-files`) |
| `merge_slashes off` + alias | Historical path normalization issues; test authorized path variants |
| Open proxy (`proxy_pass http://$host` style) | SSRF/open relay class — fix immediately |

### 7. Implement or recommend hardened snippets

Apply via config management; test `nginx -t` and canary traffic. Pair app-level
header logic with `code-quality-standards` when frameworks set CSP/HSTS too.

### 8. Verify and document

1. Re-`curl -sI` all critical paths including 404 and 301.
2. Browser devtools: confirm HSTS, CSP console only for expected tightenings.
3. Record residual exceptions (third-party scripts forcing weak CSP).
4. Secrets in config (`ssl_certificate_key` paths, basic auth files, private
   key material in repo) → hand lifecycle to `secrets-management-hygiene`.

## Concrete Config Examples

### Minimal hardened server (TLS + headers + tokens)

```nginx
# /etc/nginx/conf.d/app.conf — illustrative; adjust paths and CSP to the app
server_tokens off;

# Redirect HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name app.example;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name app.example;

    ssl_certificate     /etc/nginx/tls/fullchain.pem;
    ssl_certificate_key /etc/nginx/tls/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache   shared:SSL:10m;
    # ssl_ciphers ... per current Mozilla intermediate/modern guideline

    # OCSP stapling (when chain supports it)
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 1.1.1.1 8.8.8.8 valid=300s;
    resolver_timeout 5s;

    # Use "always" so error and redirect responses also get headers
    add_header Strict-Transport-Security "max-age=15552000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Frame-Options "DENY" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    # Start CSP in report-only if migrating a legacy app:
    # add_header Content-Security-Policy-Report-Only "default-src 'self'; ..." always;
    add_header Content-Security-Policy "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'" always;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection        "";
    }
}
```

### Avoid dropping parent headers in a location

**Bad** — location `add_header` clears inherited security headers from `server`:

```nginx
server {
    add_header Strict-Transport-Security "max-age=15552000" always;
    add_header X-Content-Type-Options "nosniff" always;

    location /api/ {
        # Only this header is sent — HSTS/nosniff dropped
        add_header Cache-Control "no-store" always;
        proxy_pass http://api_upstream;
    }
}
```

**Good** — repeat required headers in the location, or set them only at the level
that does not get overridden; map-based includes help:

```nginx
# snippets/security-headers.conf
add_header Strict-Transport-Security "max-age=15552000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header X-Frame-Options "DENY" always;

# in location /api/
include snippets/security-headers.conf;
add_header Cache-Control "no-store" always;
```

### Hide version and lock down status

```nginx
http {
    server_tokens off;

    server {
        # Internal-only metrics — not on public server_name
        listen 127.0.0.1:8081;
        location /nginx_status {
            stub_status;
            allow 127.0.0.1;
            deny all;
        }
    }
}
```

### Static site: deny hidden files and autoindex

```nginx
location ~ /\. {
    deny all;
    access_log off;
    log_not_found off;
}

autoindex off;
```

### WebSocket upgrade proxy (auth still required at app)

```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade    $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host       $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 3600s;
}
```

Message auth/origin testing → `websocket-security`.

### Basic auth file hygiene (pair with secrets skill)

```nginx
location /admin-tools/ {
    auth_basic           "restricted";
    auth_basic_user_file /etc/nginx/htpasswd/admin;  # not in git; mode 0640 root:www-data
    proxy_pass http://127.0.0.1:8080;
}
```

Never commit `htpasswd` or private keys; use `secrets-management-hygiene`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| nginx security headers, TLS edge, server_tokens, proxy header misconfig | **This skill** | — |
| Implementing/fixing app or config-as-code safely | `code-quality-standards` | this skill for nginx semantics |
| TLS keys, htpasswd, cert private material, leaked secrets in repo | `secrets-management-hygiene` | this skill for file paths on disk |
| PCAP / cipher / custom protocol capture around the edge | `NetworkProtocolAnalysisSkill` | `traffic-analysis-pcap`, this skill for config |
| Need HTTPS plaintext for app traffic debug (owned) | `tls-plaintext-acquisition` | this skill for termination settings |
| Clickjacking impact proof | `clickjacking` | this skill for XFO / frame-ancestors |
| CSP bypass research | `content-security-policy-bypass` | this skill for delivery of CSP |
| CORS headers | `cors-cross-origin-misconfiguration` | — |
| Smuggling / CL.TE at proxy | `request-smuggling` | this skill for proxy topology notes |
| Host / cache issues | `http-host-header-attacks`, `web-cache-deception` | this skill for `Host` / `proxy_set_header` |
| WebSocket auth/origin | `websocket-security` | this skill for Upgrade proxying |

### Required helpers (when applicable)

- **`code-quality-standards`:** baseline whenever changing deployable config
  templates, Lua/OpenResty, or app code that emits headers.
- **`secrets-management-hygiene`:** private keys, DH params handling, basic-auth
  files, acme account secrets — storage, rotation, no VCS.
- **`NetworkProtocolAnalysisSkill`:** authorized PCAP, Wireshark, or protocol
  tooling when validating TLS/HTTP behavior beyond `curl`/config review.

## Checklist

- [ ] Authorization/scope recorded; only in-scope hosts exercised
- [ ] Effective config inventoried (`nginx -T` or repo equivalent)
- [ ] HTTP→HTTPS redirect verified; no sensitive cookies on cleartext
- [ ] TLS 1.2+ (prefer 1.3); weak protocols/ciphers flagged with evidence
- [ ] HSTS present on HTTPS with appropriate `max-age` / subdomain policy
- [ ] CSP (or staged report-only) fits app; `frame-ancestors` or XFO set for sensitive UI
- [ ] `X-Content-Type-Options: nosniff`, Referrer-Policy, Permissions-Policy considered
- [ ] Headers verified on **200, 3xx, and 4xx** paths (`always` or equivalent)
- [ ] No silent header drop from nested `add_header` locations
- [ ] `server_tokens off`; default page / autoindex / public stub_status locked down
- [ ] `proxy_set_header` Host / Forwarded-* correct; client XFF not blindly trusted
- [ ] Hidden files and backup paths not served from `root`/`alias`
- [ ] Secrets/keys not in git; permissions tight (`secrets-management-hygiene`)
- [ ] Config changes validated with `nginx -t` and canary; `code-quality-standards` on templates
- [ ] Residual risks documented (third-party scripts, legacy clients, CDN dual-headers)

## Rules

- Methodology is for **defense and authorized assessment** only.
- Header absence is not automatically critical — tie findings to asset sensitivity
  and exploitability (framing, XSS, cookie theft paths).
- Prefer fixing **inheritance and error-path** header gaps; scanners often miss them.
- Do not enable HSTS `preload` without org commitment to long-lived HTTPS on all
  included subdomains.
- Coordinate CDN/LB headers so edge and origin do not emit conflicting CSP/HSTS.
- Keep originals of configs immutable in evidence packs; store redacted working
  copies for tickets.
---

# Note

This skill owns **nginx edge hardening**: security headers, TLS termination
hygiene, server tokens, and common reverse-proxy misconfig. Pair with
`clickjacking` / CSP skills for browser impact, `secrets-management-hygiene` for
key material, `code-quality-standards` for safe change practice, and
`NetworkProtocolAnalysisSkill` when packet-level proof is required.
