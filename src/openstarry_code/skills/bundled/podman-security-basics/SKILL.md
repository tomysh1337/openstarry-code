---
name: podman-security-basics
description: >
  Authorized Podman security hardening and assessment: rootless vs rootful,
  user namespaces, capabilities, SELinux labels, privileged/host mounts,
  publish ports, Podman socket exposure, secrets, and image trust. Use when
  reviewing Containerfile runtime, podman run/quadlet/kube YAML, rootful
  daemon risks, or lab/org Podman stacks you own — not for attacking third-party hosts.
---

# Podman Security Basics

Assess and harden **Podman** (and Quadlet/systemd units) so containers do not
gain host-equivalent power, expose sockets, or ship secrets. Defensive and
authorized only. Daemonless/rootless still fails open under bad mounts or sockets.

## Scope And Authorization

- **In scope:** Podman installs, containers, pods, volumes, Quadlet units, and
  Compose-compatible files you own or are contracted to review; lab/CTF;
  read-only `podman inspect` under written engagement.
- **Out of scope:** Escaping shared multi-tenant hosts without approval; abusing
  third-party Podman/Docker sockets; destructive demos on production.
- Prefer inspect/config review before privilege experiments. Gate breakout proofs
  to **lab** hosts (`container-escape-techniques`).
- Redact registry tokens, pull secrets, SSH keys in mounts, and customer hostnames.
- Image build → `dockerfile-best-practices`. Compose-shaped YAML → also
  `docker-compose-security` where syntax overlaps.

## When To Use

- Reviewing `podman run`, Quadlet `.container`/`.kube`, `podman play kube`, or
  Podman Compose / Docker Compose on Podman
- Rootful Podman, `privileged`, host PID/IPC/net, broad `cap_add`, unconfined
  seccomp/AppArmor/SELinux
- Sensitive binds (`/`, `/etc`, home, keys) or **Podman/Docker socket**
- Rootless UID maps, SELinux `:Z`/`:z` labels, or publish on `0.0.0.0`
- Secrets in env/CLI history; floating/`latest` tags in prod
- Keywords: Podman security, rootless, podman.sock, quadlet, SELinux volume

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Containerfile multi-stage / non-root USER | `dockerfile-best-practices` |
| Compose ports/secrets/sock patterns | `docker-compose-security` |
| Lab container→host breakout | `container-escape-techniques` |
| K8s cluster RBAC (not Podman host) | `kubernetes-pentesting` |
| cosign/sigstore trust policy | `container-image-signing` |
| Scripts/units quality; secret rotation | `code-quality-standards`, `secrets-management-hygiene` |

## Workflow

### 1. Inventory runtime and trust model

1. Record version, rootless vs rootful (`podman info`), cgroup/storage, and whether
   `podman.socket` / Docker-compat socket is enabled.
2. List containers, pods, networks, volumes, Quadlet under
   `/etc/containers/systemd` or `~/.config/containers/systemd`.
3. Map public publishes vs internal services; note registry auth.

Output: inventory with owners — no tokens or private keys.

### 2. Rootless vs rootful

| Mode | Expectation |
| --- | --- |
| Rootless | Prefer for apps; verify `subuid`/`subgid` ranges |
| Rootful | Justify; treat like privileged-daemon risk |
| Socket API | `podman.socket` / docker.sock-compat ≈ host power for that user |

Rootless is not full isolation (kernel bugs, weak mounts). Document mandatory
rootful cases (devices, some CNI) and lock those hosts tightly.

### 3. Privilege and isolation

Per service (`podman inspect` / Quadlet): no `privileged` unless node-agent with
owner+expiry; drop caps (no `ALL`); keep default seccomp/SELinux; avoid
`pid`/`ipc`/`uts`/`network=host` for apps; non-root USER; justify devices and
`--security-opt label=disable`.

### 4. Mounts, labels, and socket

| Mount / option | Guidance |
| --- | --- |
| Podman/Docker socket | Host-equivalent — never on untrusted apps |
| Host `/`, `/etc`, storage root | Deny by default |
| Credential volumes | `:ro` + host 0600; SELinux `:Z` private vs `:z` shared |
| Masked paths | Keep defaults; do not unmask sensitive `/proc`/`sys` |

### 5. Network publish and secrets

1. Prefer `127.0.0.1:port:port` for admin/debug; avoid bare publishes for DB/admin.
2. User-defined networks; do not publish backends that only need inter-container traffic.
3. No passwords in `-e`, committed env, or shell history; prefer `podman secret` /
   secrets store (`secrets-management-hygiene`).
4. Pin digests/tags; avoid prod `latest`; signed/mirrored images when policy
   requires (`container-image-signing`).

### 6. Verify and remediate

Re-inspect options/publishes; confirm admin ports not world-reachable from an
approved vantage; apply `code-quality-standards` to Quadlet/scripts/CI; prove
exposure from config — do not demo host compromise on shared prod.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Podman rootless/rootful, caps, SELinux, sock, publish | **This skill** | — |
| Image non-root / layer secrets | `dockerfile-best-practices` | this for runtime |
| Compose YAML (Docker or Podman Compose) | `docker-compose-security` | this for Podman-specific |
| Lab breakout (sock/privileged/cgroup) | `container-escape-techniques` | this for evidence |
| Image signature / trust policy | `container-image-signing` | this for pins |
| Secret lifecycle; scripts/CI quality | `secrets-management-hygiene`, `code-quality-standards` | this for paths/intent |

## Output Checklist

- [ ] Scope/authorization clear; no out-of-scope host or socket abuse
- [ ] Rootless vs rootful, version, socket exposure inventoried
- [ ] No unjustified privileged / host namespaces / unconfined labels
- [ ] Caps minimized; non-root inside containers where supported
- [ ] No Podman/Docker socket or sensitive host mounts on app services
- [ ] Volume SELinux labels and `:ro` used appropriately
- [ ] Publishes intentional; admin/DB not on all interfaces without exception
- [ ] Secrets not in VCS/CLI; `podman secret` or external store used
- [ ] Images pinned; signing/mirror policy followed when required
- [ ] Fixes follow `code-quality-standards`; residuals owned with expiry
- [ ] Escape claims only via `container-escape-techniques` in lab

## Rules

- Socket access and `privileged` are **critical**, not style nits.
- Prefer rootless + least publish + least capability; secrets out of VCS.
- Authorized org/lab only; evidence from inspect/config, not destructive demos.
- Review **image and runtime** — hardened images are undone by bad Quadlet/run flags.
