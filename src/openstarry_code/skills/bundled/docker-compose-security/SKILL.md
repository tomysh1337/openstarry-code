---
name: docker-compose-security
description: >
  Review and harden docker-compose files for privileged mode, host port
  publishing, secrets, volume mounts, networks, and capability grants. Use when
  docker-compose.yml security, privileged containers, docker.sock mounts,
  Compose secrets, host network mode, or authorized Compose misconfig review.
---

# Docker Compose Security

Assess and harden **Docker Compose** so stacks do not grant host-equivalent
power, publish unintended services, or embed secrets in plain files. Defensive
and authorized work only.

## Scope And Authorization

- **In scope:** Compose files/overrides/stacks you own or are contracted to
  harden; local lab/CTF; read-only customer Compose under written engagement.
- **Out of scope:** Attacking third-party hosts via `docker.sock`; escalating
  misconfig on shared prod without approval; publishing real credentials.
- Prefer static review and `docker compose config` first. Gate privileged or
  escape experiments behind ownership and a **lab** host.
- Redact passwords, tokens, keys, and customer hostnames from reports.
- Deep breakout research → `container-escape-techniques` (lab). Image build →
  `dockerfile-best-practices`. App/YAML quality → `code-quality-standards`.

## Use When

- Reviewing `docker-compose.yml` / `compose.yaml` / overrides
- `privileged: true`, `pid/ipc/uts: host`, `network_mode: host`, broad `cap_add`
- Host publishes DB/admin ports as bare `PORT:PORT` / all interfaces
- Secrets in `environment:`, committed `.env`, or build args
- Mounts of `/var/run/docker.sock`, `/`, `/etc`, or other sensitive host paths
- Mentions: Compose security, privileged compose, docker.sock, Compose secrets

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Dockerfile multi-stage / non-root image | `dockerfile-best-practices` |
| Lab container breakout / cgroup escape | `container-escape-techniques` |
| Kubernetes NetworkPolicy | `k8s-network-policy` |
| Full K8s RBAC / cluster pentest | `kubernetes-pentesting` |
| App reliability inside the container | `code-quality-standards` |

## Workflow

### 1. Inventory

1. Render effective config: `docker compose -f … config` (authorized env only).
2. List services, images (tag/digest), networks, volumes, profiles.
3. Note rootful vs rootless Docker; map internet-facing vs internal services.

### 2. Privilege and isolation

| Setting | Prefer |
| --- | --- |
| `privileged: true` | Off; minimal `cap_add` only |
| `cap_add: [ALL]` / unconfined seccomp/apparmor | Defaults + least caps |
| `pid`/`ipc`/`uts: host`, `network_mode: host` | Avoid; use bridge/custom nets |
| Root `user` / omitted USER | Non-root matching image |
| Host `devices:` | Narrow and justified |

Privileged + sensitive mounts → note impact; validate escape only via
`container-escape-techniques` on lab hosts.

### 3. Ports and networks

1. Prefer `127.0.0.1:PORT:PORT` for admin/debug; avoid bare publishes for DB/MQ.
2. Do not publish backends; use user-defined networks; `internal: true` when fit.
3. Drop leftover debug ports; confirm each publish matches product intent.

### 4. Secrets

1. No passwords/tokens in committed `environment:`, `.env`, or `build.args`.
2. Prefer Compose `secrets:` (file/external) mounted read-only when available.
3. Ship `.env.example` placeholders only; rotate anything that was committed.
4. Do not bake secrets into images (`dockerfile-best-practices`).

### 5. Volume and socket mounts

| Mount | Guidance |
| --- | --- |
| `docker.sock` | Root-equivalent — avoid on app services |
| Host `/`, `/etc`, Docker root | Deny by default |
| Config/static binds | Prefer `:ro` |
| Secret files on host | `ro` + host mode 0600 |

### 6. Images and verify

1. Pin tags/digests; avoid prod `latest`.
2. Align Compose `user:` with hardened image (`dockerfile-best-practices`).
3. Apply `code-quality-standards` when editing Compose/scripts/tests.
4. Re-render config; confirm ports/flags; document exceptions with owner/expiry.
5. Prove exposure from config — do not demo host compromise on shared prod.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Compose privileged, ports, secrets, mounts, nets | **This skill** | — |
| Dockerfile / non-root / secrets-in-layers | `dockerfile-best-practices` | this skill for runtime |
| Lab breakout (sock/privileged/cgroup) | `container-escape-techniques` | this skill for evidence |
| K8s workloads / cluster pentest | `kubernetes-pentesting` | — |
| Pod NetworkPolicy design/review | `k8s-network-policy` | — |
| Compose/app structure and tests | `code-quality-standards` | this skill for intent |

- **`dockerfile-best-practices`:** image side; Compose can undo non-root via
  `user:`, mounts, or privileged.
- **`container-escape-techniques`:** authorized lab host-boundary validation only.
- **`kubernetes-pentesting`:** cluster runtime, not Compose files.
- **`code-quality-standards`:** baseline when implementing fixes.

## Checklist

- [ ] Scope/authorization clear; no out-of-scope host abuse
- [ ] Effective Compose inventoried (services, nets, volumes)
- [ ] No unjustified privileged / host namespaces / unconfined profiles
- [ ] Caps minimized; non-root `user` where supported
- [ ] Publishes intentional; admin/DB not on all interfaces without exception
- [ ] Backends internal; secrets not in VCS; safe secret mounts
- [ ] No `docker.sock` / sensitive host mounts on untrusted services
- [ ] Images pinned; aligned with `dockerfile-best-practices`
- [ ] Fixes follow `code-quality-standards`; residuals documented
- [ ] Escape claims only via `container-escape-techniques` in lab

## Rules

- `docker.sock` and `privileged` are critical, not style nits.
- Least publish, least privilege, secrets out of VCS, read-only where possible.
- Authorized org/lab only; evidence from config, not destructive demos.
- Review image **and** Compose — neither alone is sufficient.
