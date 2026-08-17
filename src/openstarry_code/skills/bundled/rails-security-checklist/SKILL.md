---
name: rails-security-checklist
description: >
  Rails security checklist for org-owned apps: strong parameters, CSRF,
  sessions/cookies, ActiveRecord injection, secrets, headers, and authZ.
  Use when reviewing Rails apps, credentials, Devise/sessions, or hardening
  before release — authorized only.
---

# Rails Security Checklist

Harden **Ruby on Rails** apps you own or are authorized to assess. Framework
controls (params, CSRF, sessions, SQL/HTML sinks) plus config hygiene.

## Use When

- Reviewing Rails (`app/`, `config/`, `Gemfile`, credentials, initializers)
- Strong params, CSRF, cookies, session store, `force_ssl`, host auth
- SQLi / XSS / open-redirect / mass-assignment in controllers and views
- Pre-release or PR security pass; Devise/Sorcery/custom auth
- Mentions: Rails security, `protect_from_forgery`, `credentials.yml.enc`, Rails 安全

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Unknown injection class deep-dive | `injection-checking` → class skill |
| Secret vault/rotation only | `secrets-management-hygiene` |
| Code reliability/tests baseline | `code-quality-standards` |
| Cross-stack mass-assignment methodology | `mass-assignment` |

## Repo Config First

Repo settings **outrank** generic defaults.

1. Rails version and `config.load_defaults`
2. `config/environments/*`, `application.rb`, session/host/CSP initializers
3. Secrets: `credentials.yml.enc` / `RAILS_MASTER_KEY` / ENV / vault — one path only
4. Auth stack (Devise, Rodauth, Warden) — match neighbors
5. Strong-params and `before_action` authZ style in existing controllers
6. Template stack (ERB/Haml/Slim, Turbo) and CSP implications
7. CI: Brakeman, bundler-audit — extend, do not weaken
8. TLS at app vs edge — align cookie `secure` with reality

Follow the repo on conflicts; surface `permit!`, global CSRF skips, committed master keys.

## Workflow

1. **Inventory** — `rails routes`, admin engines, ActiveStorage, ActionCable, Sidekiq UIs.
2. **Config** — prod `force_ssl`, `consider_all_requests_local`, host authorization, secret source, log filters.
3. **Session/authN** — login/logout/reset, remember-me, regenerate session on privilege change, cookie flags.
4. **AuthZ** — policy/scope on show/update/destroy; no bare `find(params[:id])` IDOR.
5. **Mass assignment** — allowlisted strong params only; no user-writable `role`/`admin`.
6. **Injection sinks** — SQL interpolation, unsafe `order`, `raw`/`html_safe`, shell, open redirects → `injection-checking` when class unclear.
7. **Files/SSRF** — ActiveStorage validators; user URLs to `open`/`Net::HTTP`; unsafe YAML/Marshal.
8. **Deps + verify** — `bundle audit`; Brakeman on touched code; dual-account authZ retest; `code-quality-standards` on fixes.

## Good / Bad

**Good** — `params.require(:user).permit(:name, :email)`; `User.where(email: params[:email])`; default ERB escaping; `protect_from_forgery with: :exception`; credentials encrypted; `redirect_to user_path(@user)`.

**Bad**

```ruby
@user.update!(params[:user])                 # or permit!
User.where("email = '#{params[:email]}'")
<%= raw @comment.body %>
skip_before_action :verify_authenticity_token  # broad skip
redirect_to params[:return_to]               # open redirect
# secret_key_base / RAILS_MASTER_KEY in git
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Rails security checklist / strong params / CSRF / config | **This skill** | — |
| Implementation quality, tests on fixes | `code-quality-standards` | this |
| Master key, credentials, ENV, rotation | `secrets-management-hygiene` | this for Rails paths |
| Unclear / multi-class injection | `injection-checking` | this for Rails sinks |
| SQLi/XSS/SSRF deep dive | matching class skill | this |
| Mass-assignment proofs | `mass-assignment` | this for `permit` |
| Session fixation | `session-fixation-management` | this |

### Required helpers

- **`code-quality-standards`** — every production code change.
- **`secrets-management-hygiene`** — credentials, master key, API tokens, log redaction.
- **`injection-checking`** — unknown or multi-type sinks.

## Checklist

- [ ] Version / `load_defaults` / env configs reviewed
- [ ] No master key or plaintext secrets in git
- [ ] SSL (app or edge); secure / httponly / samesite cookies
- [ ] CSRF on for cookie-session browser flows; API auth explicit if skipped
- [ ] Strong params only; no `permit!`; roles server-set
- [ ] AuthZ/policy on object access; no IDOR via raw find
- [ ] No interpolated SQL/order; no unnecessary `raw`/`html_safe`
- [ ] Redirects and hosts allowlisted; params filtered in logs
- [ ] ActiveStorage / outbound URL sinks reviewed; gems audited
- [ ] Fixes: `code-quality-standards`; secrets: `secrets-management-hygiene`; deep inject: `injection-checking`

## Rules

Authorized targets only. Evidence over speculative CVEs. Smallest fix restoring allowlists and server-side authZ. Redact credentials and PII.
