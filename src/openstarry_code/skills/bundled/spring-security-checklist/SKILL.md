---
name: spring-security-checklist
description: >-
  Spring Security config checklist: SecurityFilterChain, CSRF, sessions, method
  security, CORS, password encoding, actuators, JWT resource server. Use when
  reviewing Spring Boot Security, permitAll mistakes, or hardening org-owned
  Java/Kotlin apps — authorized only.
---

# Spring Security Checklist

Defensive checklist for **Spring Security** (Boot 2.7+/3.x). Prefer repo conventions; treat every `permitAll` and custom filter as a security decision.

## Use When

- Writing/reviewing `SecurityFilterChain`, `HttpSecurity`, or resource-server JWT config
- CSRF disabled for “API” without a clear Bearer-vs-cookie model; session/cookie flags wrong
- Actuator, Swagger, or static paths public; method security missing on sensitive services
- Mentions: Spring Security, `csrf().disable()`, `permitAll`, resource server, actuator

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| JWT alg/kid/claim abuse | `api-auth-and-jwt-abuse` |
| Browser CSRF / SameSite PoCs | `csrf-cross-site-request-forgery` |
| Implementation quality / tests | `code-quality-standards` |

## Repo Config First

Repo and framework config **outrank** examples below.

1. Security 5 vs 6 APIs (`authorizeHttpRequests` vs legacy)
2. Multiple `SecurityFilterChain` beans and `@Order`
3. Auth model: form, basic, OAuth2 login, opaque token, JWT, hybrid
4. Session: `IF_REQUIRED` vs `STATELESS`; cookie domain/path; Redis session
5. CSRF: cookie apps on; SPA token repository/header names
6. CORS: app `CorsConfigurationSource` vs gateway-only
7. Secrets via vault/env — no default prod user/password
8. Actuator: management port, network policy, role gates
9. `@EnableMethodSecurity` and expression customizations
10. Tests: `spring-security-test`, MockMvc security setup

**Precedence:** Follow org SecurityConfig when it conflicts with samples. Surface
`permitAll("/**")`, CSRF off with cookie sessions, or hard-coded JWT secrets.

## Workflow

1. **Inventory:** UI/API/admin/actuator/WS; auth per path; forwarded headers;
   authority source (DB, JWT, LDAP).
2. **Filter chain:** deny-by-default; public only login/health liveness/static;
   gate admin/actuator (`env`/`heapdump` never public); avoid `web.ignoring()` on
   sensitive paths; custom filters must not skip authz.
3. **CSRF / session / cookies:**

   | Mode | Expectation |
   | --- | --- |
   | Cookie session browser app | CSRF **on**; token in header/form |
   | Pure Bearer (no cookie auth) | CSRF off only if cookies unused for auth |
   | Hybrid SPA + session cookie | CSRF on; tight CORS; no `*` + credentials |

   Regenerate session on login; `HttpOnly`/`Secure`/`SameSite`; invalidate on logout.
4. **Passwords / headers:** `BCrypt`/`Argon2`/`SCrypt` — not `{noop}`; keep
   default security headers; HTTPS cookies per edge policy.
5. **JWT resource server:** issuer, audience, JWKS; reject `alg=none`. Deep
   token work → `api-auth-and-jwt-abuse`.
6. **Verify:** MockMvc anonymous/user/admin; CSRF rejects cookie mutations;
   actuators/Swagger locked in prod.

## Good / Bad Examples

**Good — deny default + CSRF for session app**

```java
http.authorizeHttpRequests(a -> a
      .requestMatchers("/assets/**", "/login", "/actuator/health").permitAll()
      .requestMatchers("/admin/**", "/actuator/**").hasRole("ADMIN")
      .anyRequest().authenticated())
    .formLogin(Customizer.withDefaults())
    .csrf(c -> c.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse()));
```

**Bad**

```java
http.csrf(AbstractHttpConfigurer::disable)
    .authorizeHttpRequests(a -> a.anyRequest().permitAll());
```

**Good — stateless Bearer**

```java
http.sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
    .csrf(csrf -> csrf.disable()) // no cookie session auth
    .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
    .authorizeHttpRequests(a -> a.requestMatchers("/public/**").permitAll()
        .anyRequest().authenticated());
```

**Bad** — `{noop}`, default admin password, or JWT secret in prod YAML.  
**Good** — `@PreAuthorize("hasAuthority('invoice:write') and #orgId == principal.orgId")`.  
**Bad** — UI-only authZ; service layer has no method security.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Spring Security config, chains, actuators | **This skill** | — |
| Implement/refactor SecurityConfig | `code-quality-standards` | this skill |
| JWT validation / claim abuse | `api-auth-and-jwt-abuse` | this skill for wiring |
| Cookie CSRF / SameSite PoC | `csrf-cross-site-request-forgery` | this skill for CSRF repos |
| Session fixation after custom login | `session-fixation-management` | this skill |
| CORS details | `cors-cross-origin-misconfiguration` | this skill |

Always apply **`code-quality-standards`** when changing security code. Use **`api-auth-and-jwt-abuse`** for tokens and **`csrf-cross-site-request-forgery`** for browser CSRF evidence.

## Checklist

- [ ] Auth model per path (session vs Bearer vs hybrid)
- [ ] Deny-by-default; public matchers minimal
- [ ] Admin/actuator/Swagger gated or disabled in prod
- [ ] CSRF matches cookie vs Bearer reality
- [ ] Session rotates on login; logout invalidates server session
- [ ] Cookie flags Secure/HttpOnly/SameSite appropriate
- [ ] Strong PasswordEncoder; no `{noop}` / default user in prod
- [ ] JWT issuer/audience/JWKS; no weak secret in VCS
- [ ] Method security on sensitive commands
- [ ] CORS not `*` with credentials; trust proxies only from real LB
- [ ] Tests: anonymous/user/admin and CSRF where applicable
- [ ] `code-quality-standards` + routed JWT/CSRF skills when needed

## Rules

- Authorized review and hardening only.
- `csrf().disable()` needs a non-cookie auth justification.
- Prefer framework defaults over “disable everything” snippets.
- Multiple filter chains need explicit order and non-overlapping matchers.
- Redact secrets, tokens, and session IDs from tickets.
