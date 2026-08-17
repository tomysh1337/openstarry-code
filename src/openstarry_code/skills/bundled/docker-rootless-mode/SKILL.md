---
name: docker-rootless-mode
description: >
  Install, operate, and harden Docker Engine in rootless mode: user namespaces,
  dockerd-rootless-setuptool, systemd user units, slirp4netns/pasta networking,
  storage drivers, and known limitations vs rootful Docker. Use when setting up
  rootless Docker, troubleshooting non-root dockerd, comparing rootless security
  boundaries, fixing rootless port/network/storage issues, or reducing host
  impact of a compromised container runtime on owned developer or lab hosts.
---

# Docker Rootless Mode

Run **Docker Engine without a privileged host root daemon**: `dockerd` and
containers execute under a normal user with Linux **user namespaces**, so
container UID 0 maps to an unprivileged host UID. Prefer rootless for
developer laptops, CI agents, and shared multi-tenant build hosts when full
rootful privileges are not required. **Owned systems, labs, and authorized
deployments only.**

## Scope And Authorization

- **In scope:** Installing and operating rootless Docker on hosts **you own** or
  are contracted to configure; developer workstations; lab/CI agents; documenting
  security trade-offs and residual risks for org hardening reviews.
- **Out of scope:** Escalating access on third-party hosts; bypassing org policy
  that requires rootful/managed runtimes; attacking production without change
  control; unauthorized breakout against systems you do not own.
- Prefer config review and controlled local tests. Gate kernel/sysctl or
  privileged helper changes behind ownership and rollback plans.
- Redact usernames, host paths, registry tokens, and customer topology.
- Image build → `dockerfile-best-practices`. Compose → `docker-compose-security`.
  Lab host-boundary research → `container-escape-techniques`. Scripts →
  `code-quality-standards`.

## When To Use

- Installing or migrating to **rootless Docker** (`dockerd-rootless-setuptool.sh`,
  `DOCKER_HOST=unix:///run/user/UID/docker.sock`)
- Hardening developer/CI hosts so a compromised daemon is **not host root**
- Debugging rootless failures: ports &lt; 1024, VPN/DNS, volume mounts, cgroup v2,
  overlayfs, fuse-overlayfs, or `newuidmap`/`newgidmap` subuid ranges
- Choosing **slirp4netns vs pasta** (or similar) user-mode networking
- Comparing rootless isolation to rootful, Podman rootless, or rootless
  containerd/nerdctl
- Mentions: Docker rootless, rootless dockerd, user namespace Docker, non-root
  Docker daemon, dockerd-rootless

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Dockerfile multi-stage / non-root image USER | `dockerfile-best-practices` |
| Compose privileged, ports, secrets, mounts | `docker-compose-security` |
| Lab container→host escape methodology | `container-escape-techniques` |
| K8s pod security / cluster pentest | `kubernetes-pod-security` / `kubernetes-pentesting` |
| App/scripts quality while automating setup | `code-quality-standards` |

## Workflow

### 1. Confirm prerequisites and subid maps

1. Record OS, kernel, cgroup version, and authorization for host changes.
2. Ensure `uidmap`, `dbus-user-session`, and (as needed) `fuse-overlayfs`,
   `slirp4netns` or `pasta` packages are available per distro docs.
3. Verify `/etc/subuid` and `/etc/subgid` grant a large subordinate range
   (commonly ≥65536 IDs). Without maps, user namespaces fail.

```bash
id; uname -r
cat /etc/subuid /etc/subgid
export DOCKER_HOST="unix:///run/user/$(id -u)/docker.sock"
```

### 2. Install and enable rootless dockerd

1. Prefer the official rootless setup for the installed Docker package
   (`dockerd-rootless-setuptool.sh install`) on **owned** hosts.
2. Enable lingering if the daemon must survive logout:
   `loginctl enable-linger $USER`.
3. Export `PATH`/`DOCKER_HOST` (or a dedicated context); run `docker info` and
   confirm rootless / user-namespace remapping — not a silent rootful socket.

### 3. Networking, ports, and storage

| Concern | Rootless guidance |
| --- | --- |
| Ports &lt; 1024 | Often blocked; use high ports or approved unprivileged-port sysctl |
| Bridge / NAT | User-mode stack (slirp4netns/pasta); different perf and hairpin behavior |
| Host network | Limited or unavailable vs rootful; document app impact |
| Storage | Prefer overlayfs when allowed; else fuse-overlayfs; note performance |
| Privileged | Still weak isolation — avoid; rootless shrinks *host* blast radius only |

Do not mount the **rootful** `/var/run/docker.sock` into workloads — that
restores host-equivalent control and undoes rootless intent.

### 4. Security expectations

**Benefits:** daemon and containers lack host root; many classic socket/privileged
daemon impact paths shrink on multi-user build hosts.

**Not a silver bullet:** kernel CVEs, weak host mounts, secrets in images, and
app RCE still matter. Rootless does **not** replace non-root image `USER`, least
Compose privileges, or network policy. Document residual risk.

### 5. Verify, migrate, and document

1. Smoke: `docker run --rm hello-world`; publish a high port; write a volume under `$HOME`.
2. Point Compose/CI at the rootless socket via `DOCKER_HOST` or context; do not
   mix rootful and rootless clients by accident.
3. Migration: re-pull under user data-root; re-create named volumes; tune user unit.
4. Apply `code-quality-standards` on install scripts/unit drop-ins.
5. Must-stay-rootful exceptions (GPU, special devices) need **owner + expiry**.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Rootless install, user unit, subuid, networking limits | **This skill** | — |
| Image non-root USER, multi-stage, secrets-in-layers | `dockerfile-best-practices` | this skill for daemon mode |
| Compose privileged / docker.sock / host mounts | `docker-compose-security` | this skill for rootless context |
| Authorized lab breakout / privileged proof | `container-escape-techniques` | this skill for expected isolation |
| CI wiring of Docker socket/context | `ci-cd-pipeline-patterns` | this skill for rootless env |
| Setup scripts / unit files quality | `code-quality-standards` | this skill for correct flags |

## Output Checklist

- [ ] Host ownership/authorization and env (dev/lab/CI) recorded
- [ ] `subuid`/`subgid` ranges present; uidmap helpers work
- [ ] Rootless install path used; user unit enabled; linger decided intentionally
- [ ] `DOCKER_HOST` / context points at user socket — not rootful by mistake
- [ ] `docker info` confirms rootless operation
- [ ] Networking choice (slirp4netns/pasta) noted; low-port strategy documented
- [ ] Storage driver chosen and smoke-tested (overlay vs fuse-overlayfs)
- [ ] No unjustified privileged containers or rootful docker.sock mounts
- [ ] CI/Compose clients updated; images/volumes under user data-root if migrated
- [ ] Residual risks and rootful exceptions have owner + expiry
- [ ] Related image/Compose/escape work routed; scripts follow code quality baseline
