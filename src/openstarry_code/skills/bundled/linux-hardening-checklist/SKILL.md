---
name: linux-hardening-checklist
description: >
  Authorized Linux host hardening checklist: accounts and SSH, firewall and
  listening services, package/update hygiene, filesystem and kernel sysctl,
  audit/logging, and service least privilege. Use when hardening org-owned
  Linux servers, lab VMs, or reviewing baseline CIS-style controls — not for
  attacking third-party hosts without permission.
---

# Linux Hardening Checklist

Apply a **defensive baseline** on Linux hosts you own or are explicitly
authorized to harden or assess. Prefer reversible changes with rollback.

## Scope And Authorization

- **In scope:** org-owned Linux servers/workstations, staging/prod under written
  engagement, local labs, CTF boxes when the goal is defensive review.
- **Out of scope:** unauthorized third-party lockout; destructive prod changes
  without change control; implanting backdoors under a hardening pretext.
- Inventory first (`ss`, packages, `sshd -T`). Gate firewall/SSH/sysctl behind
  console recovery; snapshot configs. Redact hostnames, IPs, keys from reports.
- Risky kernel/exploit validation → `security-sandbox`. Residual offensive
  privesc (lab/owned) → `linux-privilege-escalation`.

## Use When

- Building/reviewing a Linux **server baseline** (SSH, firewall, updates)
- Closing CIS/Lynis/OpenSCAP findings; hardening golden images or AMIs
- Lab VMs that should not be trivially rootable after setup
- Chinese/English: Linux 加固, SSH 加固, sysctl, 防火墙基线, 主机安全清单

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Low shell → root enumeration | `linux-privilege-escalation` |
| Exploit / kernel PoC isolation | `security-sandbox` |
| Windows host baseline | `windows-hardening-basics` |
| Automation script/module quality | `code-quality-standards` |

## Workflow

### 1. Inventory and recovery path

Record distro/role/exposure and confirm out-of-band recovery before SSH or
firewall changes. Backup `/etc/ssh/sshd_config*`, firewall rules, sudoers.

```bash
# Authorized host only
uname -a; cat /etc/os-release
ss -lntup 2>/dev/null || ss -lntu
systemctl list-units --type=service --state=running
```

### 2. Accounts, sudo, and SSH

| Control | Direction |
| --- | --- |
| Root SSH | Prefer `PermitRootLogin no` |
| Password auth | Prefer keys; disable passwords on Internet-facing SSH when possible |
| Users | Disable unused accounts; no shared interactive logins |
| sudo | Least privilege; avoid NOPASSWD:ALL; log sudo |
| Homes | Restrict perms (`700`/`750`); no world-writable homes |

```bash
sshd -T 2>/dev/null | grep -Ei 'permitroot|passwordauth|pubkey|allowusers'
getent passwd | awk -F: '$3>=1000 || $3==0 {print}'
ls -la /etc/sudoers /etc/sudoers.d 2>/dev/null
```

### 3. Network exposure and host firewall

Map each listener to a required service. Default-deny inbound except management
and app ports from known sources. No public bind for admin UIs, DBs, Redis, or
Docker API.

### 4. Packages, updates, and units

Enable security update cadence. Remove unused packages/legacy services. Disable
unused systemd units; avoid world-writable `ExecStart` paths.

### 5. Filesystem, kernel, MAC

| Area | Checks |
| --- | --- |
| Mounts | `nodev,nosuid,noexec` on `/tmp`, `/var/tmp`, `/dev/shm` when feasible |
| SUID/caps | Inventory unexpected SUID/`getcap`; remove or justify |
| sysctl | ASLR on; tighten `kptr_restrict` / `dmesg_restrict` per distro baseline |
| MAC | SELinux enforcing or AppArmor profiles — no silent permissive mode |

```bash
find /usr /bin /sbin -perm -4000 -type f 2>/dev/null | head -80
getcap -r / 2>/dev/null | head -40
sysctl kernel.randomize_va_space kernel.kptr_restrict 2>/dev/null
getenforce 2>/dev/null; aa-status 2>/dev/null | head
```

### 6. Logging, time, verify

Centralize auth/sudo/sshd logs; NTP synced. After changes, re-test SSH from an
approved path with a second session still open. Document residual exceptions
with owner and expiry. Automate via config management; apply
`code-quality-standards` to enforcement scripts.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Linux host baseline / CIS-style checklist | **This skill** | — |
| Lab/owned low shell → root | `linux-privilege-escalation` | this skill for defensive gaps |
| Windows baseline | `windows-hardening-basics` | — |
| Risky PoC isolation | `security-sandbox` | this skill for production controls |
| Automation modules / shell quality | `code-quality-standards` | this skill for control intent |

## Checklist

- [ ] Authorization, role, and console/recovery path recorded
- [ ] Inventory: OS, listeners, running services, admin paths
- [ ] SSH hardened (root login, auth methods); reload verified
- [ ] Unused accounts disabled; sudo least privilege; home perms sane
- [ ] Host firewall default-deny; only required ports from required sources
- [ ] No unnecessary public admin/DB/cache listeners
- [ ] Patch path enabled; unused packages/services removed
- [ ] SUID/capabilities reviewed; tmp mounts hardened where possible
- [ ] sysctl/ASLR and MAC (SELinux/AppArmor) state documented
- [ ] Logging/time sync adequate for auth and privilege events
- [ ] Exceptions documented; automation follows `code-quality-standards`
- [ ] Risky validation isolated via `security-sandbox` when needed

## Rules

- **Defense and authorized assessment only** on lab/owned systems.
- Never lock yourself out: change SSH/firewall with console or a second session.
- Prefer reduced listen surface and least privilege over obscure kernel tweaks.
- Do not disable SELinux/AppArmor without a tracked exception.
- Quote evidence (`sshd -T`, `ss`, paths, versions). Residual offensive privesc
  validation → `linux-privilege-escalation` under the same authorization only.
