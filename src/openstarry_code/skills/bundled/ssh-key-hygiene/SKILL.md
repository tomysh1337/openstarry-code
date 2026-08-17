---
name: ssh-key-hygiene
description: >
  SSH key hygiene for org-owned hosts and workstations: modern key types,
  ssh-agent practices, authorized_keys review, permissions, rotation, and
  host-key trust. Use when hardening SSH keys, cleaning authorized_keys,
  agent-forwarding risk, or post-incident key revocation — authorized only.
---

# SSH Key Hygiene

Establish and review **SSH public-key authentication hygiene** on systems you
own or are authorized to harden: key algorithms, private-key storage, agent
use, `authorized_keys`, and lifecycle (issue → use → rotate → revoke).

## Scope And Authorization

- **In scope:** org-owned bastions, servers, workstations under ownership or
  written engagement; lab/CTF hosts where SSH config is in scope.
- **Out of scope:** brute-forcing third-party SSH; planting keys off-scope;
  harvesting keys from shared scans; disabling MFA/PAM without approval.
- Prefer **config and inventory review** over live prod login experiments.
- Redact private keys from tickets; never paste PEM into chat.
- On **private-key leak:** rotate/revoke first (`secrets-management-hygiene`), then audit auth logs.

## Use When

- Choosing or reviewing **key types** (ed25519 vs RSA, certs vs raw keys)
- Hardening **ssh-agent**, agent forwarding, or hardware-backed (`sk-`) keys
- Cleaning **`authorized_keys`** (stale keys, `command=`, `from=`)
- Fixing modes on `~/.ssh`, private keys, host keys; rotation after leave/loss/CI leak
- Chinese/English: SSH 密钥, authorized_keys, agent 转发, 主机密钥

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| General secret vault/rotation | `secrets-management-hygiene` |
| Broad host OS / sshd beyond keys | `linux-hardening-checklist` |
| Engagement recon / surface inventory | `recon-and-methodology` |
| App/IaC generating or embedding keys | `code-quality-standards` |

## Key Type Baseline

| Topic | Prefer | Avoid |
| --- | --- | --- |
| User keys | Ed25519 or `sk-ed25519` | DSA; RSA &lt; 2048; one key shared by many people |
| RSA if required | ≥ 3072 (prefer 4096) | Undocumented orphan keys |
| Deploy / CI | Per-repo/host; vaulted private half | One org-wide deploy key on every server |
| Host trust | Managed `known_hosts` or host certs | Blind `StrictHostKeyChecking=no` in prod CI |
| Passphrase | Strong on interactive keys | Unencrypted keys on multi-user disks |

Inventory by **fingerprint** (`ssh-keygen -lf`), not by pasting key bodies.

## Workflow

### 1. Inventory principals and trust paths

1. List humans, service accounts, bastions, and CI using SSH.
2. Record fingerprints, type, age, owner, last use if known.
3. Map private locations (laptop, HSM/sk, CI store) and public trust
   (`authorized_keys`, cloud metadata, `AuthorizedKeysCommand`, CMDB).
4. Flag orphans, duplicates, and world-readable private paths.

### 2. Client generation and storage

```bash
# Owned workstation only
ssh-keygen -t ed25519 -a 64 -C "user@device-purpose" -f ~/.ssh/id_ed25519_work
ssh-keygen -lf ~/.ssh/id_ed25519_work.pub
```

Private key `0600`/`0400`; `~/.ssh` `0700`. Never commit keys. Distinct work vs
personal. Vault placement → `secrets-management-hygiene`.

### 3. ssh-agent hygiene

1. Prefer agent or hardware confirmation over long-lived decrypted keys on disk.
2. **`ForwardAgent no` by default** — a compromised remote can use your local
   agent for further hops; allow only trusted jump hosts, briefly.
3. `ssh-add -l` / `ssh-add -D`: load only needed keys; clear on shared machines.
4. Protect agent sockets from open filesystem permissions.

### 4. authorized_keys review (server)

1. One principal per line; comment owner/purpose; remove departed/dead automation keys.
2. Restrict automation: `from=`, `command=`, `no-agent-forwarding,no-port-forwarding,no-X11-forwarding,no-pty`.
3. Reject weak types per policy; home/`.ssh` not group-writable (`StrictModes`).
4. With `AuthorizedKeysCommand`/IdM, review the **source of truth**, not only files.

### 5. Host keys, rotation, verify

1. Pin host keys; treat unexpected change as MITM until verified out-of-band.
2. Rotate on loss, exit, leak, or missing owner; remove public keys from all trust stores.
3. Audit auth logs after revoke; deploy-key leak → secret incident.
4. Confirm intended logins; automation meets `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SSH key types, agent, authorized_keys | **This skill** | — |
| Private key storage / vault / rotation | `secrets-management-hygiene` | this skill for SSH trust files |
| Broader SSHD/OS hardening | `linux-hardening-checklist` | this skill for key material |
| Authorized estate/SSH surface discovery | `recon-and-methodology` | this skill for key cleanup |
| Scripts/IaC installing keys | `code-quality-standards` | this skill for algorithm/permission rules |

- **`secrets-management-hygiene`:** private/deploy/CA lifecycle, no-VCS.
- **`linux-hardening-checklist`:** sshd_config and OS controls beyond keys.
- **`recon-and-methodology`:** authorized discovery before hygiene sprints.
- **`code-quality-standards`:** safe automation around key install paths.

## Checklist

- [ ] Scope clear; only owned/in-scope hosts and keys touched
- [ ] Inventory by fingerprint, owner, type, trust locations
- [ ] Prefer ed25519/hardware-backed; weak keys replaced or flagged
- [ ] Private keys out of git/images/chat; `~/.ssh` modes correct
- [ ] Agent forwarding off by default; `ssh-add` discipline documented
- [ ] `authorized_keys` free of stale keys; automation restrictions applied
- [ ] Host-key trust managed; no blind ignore in prod CI
- [ ] Rotation/revoke owned; post-leave removal verified
- [ ] Pairs with `secrets-management-hygiene` and `linux-hardening-checklist`
- [ ] Discovery via `recon-and-methodology` when estate map missing
- [ ] Automation changes meet `code-quality-standards`

## Rules

- **Defense and authorized hardening only** — never plant or harvest keys off-scope.
- Fingerprints in tickets; private material only in approved secret stores.
- Shared interactive keys block accountability — prefer one principal per human.
- Agent forwarding is a **trust extension**, not a convenience default.
---

# Note

Owns **SSH key and agent hygiene**. Pair with `secrets-management-hygiene`,
`linux-hardening-checklist`, `recon-and-methodology`, and `code-quality-standards`.
