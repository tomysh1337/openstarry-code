---
name: windows-hardening-basics
description: >
  Authorized Windows host hardening basics: local accounts and LSA, RDP and
  network exposure, Windows Update and features, Defender/ASR, audit policy,
  SMB/LLMNR reductions, and service least privilege. Use when hardening
  org-owned Windows servers or workstations, lab VMs, or reviewing baseline
  controls — not for unauthorized attacks on third-party systems.
---

# Windows Hardening Basics

Apply a **defensive baseline** on Windows hosts you own or are explicitly
authorized to harden or assess. Prefer GPO/MDM settings; validate remote access
before tightening RDP or firewall.

## Scope And Authorization

- **In scope:** org-owned Windows Server/clients, staging/prod under written
  engagement, lab VMs, CTF boxes when the goal is defensive review.
- **Out of scope:** unauthorized third-party lockout; destructive prod changes
  without change control; planting persistence under a hardening pretext.
- Inventory first (users, listeners, shares, Defender). Gate RDP/firewall behind
  console or alternate admin session. Redact names, SIDs, secrets from reports.
- Malware/exploit validation → `security-sandbox`. Residual offensive privesc
  (lab/owned) → `windows-privilege-escalation`.

## Use When

- Building/reviewing a Windows **server/workstation baseline**
- Closing CIS/Microsoft baseline findings; golden images, Autopilot/MDM, GPO
- Reducing open RDP, LLMNR, or shared local admin passwords
- Chinese/English: Windows 加固, RDP 安全, Defender ASR, 本地管理员, 主机基线

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Low-priv shell → admin/SYSTEM | `windows-privilege-escalation` |
| Linux host baseline | `linux-hardening-checklist` |
| Isolate malware / exploit repro | `security-sandbox` |
| PowerShell/DSC automation quality | `code-quality-standards` |

## Workflow

### 1. Inventory and recovery path

Record edition/build, role (DC, member, workstation, bastion), domain vs
workgroup, and public exposure. Confirm console/KVM recovery before RDP changes.

```powershell
# Authorized host only
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
whoami /all
Get-NetTCPConnection -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
Get-Service | Where-Object Status -eq 'Running' | Select-Object Name,DisplayName
```

### 2. Accounts and local admin

| Control | Direction |
| --- | --- |
| Local admin | Unique per host or Windows LAPS; no shared passwords |
| Guest / stale | Disable Guest and unused local accounts |
| UAC | Enabled; no silent elevation for standard users |
| LSA / Credential Guard | Enable where hardware and edition support |
| Secrets | No passwords in scripts; vault/LAPS for admin secrets |

```powershell
Get-LocalUser | Format-Table Name,Enabled,LastLogon
Get-LocalGroupMember Administrators
```

### 3. Remote access and network

1. **RDP:** not on `0.0.0.0/0`; restrict source/VPN; NLA on; prefer bastion.
2. **WinRM:** admin networks only; HTTPS when exposed.
3. **Firewall:** default inbound block; allow only required ports.
4. **SMB:** disable SMBv1; no anonymous shares.
5. **LLMNR/NetBIOS:** disable where DNS fully covers name resolution (test first).

```powershell
Get-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections
Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -ErrorAction SilentlyContinue
Get-NetFirewallProfile | Format-Table Name,Enabled,DefaultInboundAction
```

### 4. Updates, features, Defender

Patch via Windows Update/WSUS/Autopatch. Remove unused roles (legacy SMB1, unused
IIS). Prefer WDAC/AppLocker in audit→enforce when mature. Keep Defender real-time
and Tamper Protection on; enable high-value ASR rules (audit then block). BitLocker
for laptops and sensitive servers; vault recovery keys.

```powershell
Get-MpComputerStatus | Select-Object AMServiceEnabled,RealTimeProtectionEnabled,IoavProtectionEnabled
Get-MpPreference | Select-Object DisableRealtimeMonitoring,AttackSurfaceReductionRules_Ids
```

### 5. Audit, services, verify

Enable advanced audit for logon, account management, and process creation where
accepted; forward to SIEM. Review auto-start services/tasks for weak binary ACLs
(user-writable service path → fix ACLs). Keep an admin session open until RDP/WinRM
still works from the approved path. Document exceptions with owner and expiry.
Automate via GPO/DSC/Intune; apply `code-quality-standards` to enforcement code.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Windows host baseline hardening | **This skill** | — |
| Lab/owned low-priv → admin/SYSTEM | `windows-privilege-escalation` | this skill for defensive gaps |
| Linux baseline | `linux-hardening-checklist` | — |
| Malware / exploit isolation | `security-sandbox` | this skill for production controls |
| PowerShell/DSC/automation quality | `code-quality-standards` | this skill for control intent |

## Checklist

- [ ] Authorization, role, domain/workgroup, console recovery recorded
- [ ] Inventory: build, listeners, services, RDP/WinRM state
- [ ] Local admins unique/LAPS; Guest disabled; blank passwords blocked
- [ ] RDP/WinRM not Internet-open; NLA on; firewall default inbound block
- [ ] SMBv1 disabled when possible; shares reviewed
- [ ] LLMNR/NetBIOS policy decided and tested if disabled
- [ ] Patch channel healthy; unused roles/features removed
- [ ] Defender real-time on; ASR/Tamper Protection considered
- [ ] BitLocker for portable/sensitive disks; audit/log forwarding OK
- [ ] Service/task binary ACLs not user-writable
- [ ] Exceptions documented; automation follows `code-quality-standards`
- [ ] Risky validation isolated via `security-sandbox` when needed

## Rules

- **Defense and authorized assessment only** on lab/owned systems.
- Never lock out the only admin path; change RDP/firewall with console backup.
- Prefer Microsoft/org baselines; do not permanently disable Defender/ASR
  without a ticket. Cite evidence (`Get-MpComputerStatus`, listeners). Residual
  offensive privesc → `windows-privilege-escalation` under the same auth only.
