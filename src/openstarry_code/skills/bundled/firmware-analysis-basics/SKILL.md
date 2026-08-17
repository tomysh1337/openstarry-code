---
name: firmware-analysis-basics
description: >
  Firmware analysis basics for owned devices, vendor-supplied images, and CTF
  firmware blobs: identification, binwalk unpack, filesystem extract (squashfs,
  jffs2, ubifs, initramfs), credential/config triage, and hand-off to binary RE.
  Use when analyzing router/IoT/embedded firmware dumps under authorization —
  not for unauthorized device exploitation.
---

# Firmware Analysis Basics

## When To Use

- You have a firmware image (`.bin`, `.img`, `.trx`, vendor upgrade package, flash dump) and need a **safe first-pass unpack**.
- Goal is to map partitions, extract rootfs, find configs/keys/scripts, and list interesting binaries.
- CTF “firmware” or IoT challenge where the flag lives in squashfs, nvram defaults, or a web admin binary.

**Do not use as primary skill when:**

| Situation | Prefer instead |
| --- | --- |
| Already-extracted ELF/PE and deep RE | `binary-re` (triage → static → dynamic) |
| Live mobile app testing | `android-pentesting-tricks` / Frida playbook |
| Need isolated detonation of extracted malware | `security-sandbox` first |
| PCAP from device network only | `traffic-analysis-pcap` |

This skill covers **image → filesystem → triage**. Deep disassembly, emulation, and Frida on extracted binaries hand off to `binary-re` / `frida-hooking-playbook`.

## Scope And Authorization

- **In scope:** firmware you own; images from authorized hardware assessments; vendor GPL dropboxes you are licensed to analyze; training/CTF firmware.
- **Out of scope:** dumping or attacking third-party devices without authorization; building exploit packs against unowned production fleets; distributing decrypted vendor secrets outside the engagement.
- Keep the **original image immutable**. All unpack/carve output goes under `derived/`.
- Hash the image before and after copy; never “fix” the only copy of a dump in place.
- Redact default passwords, cloud tokens, private keys, and customer PII found in configs when reporting outside the lab.
- Do not flash modified firmware to devices outside written scope.

## Prerequisites

| Tool | Role |
| --- | --- |
| `file`, `sha256sum` / `Get-FileHash`, `binwalk` | Type, integrity, signatures, extract |
| `strings`, `xxd` / `hexdump` | Quick content and header peeks |
| `sasquatch` / `squashfs-tools` (`unsquashfs`) | SquashFS rootfs |
| `jefferson` / `jefferson` alternatives, `mtd-utils` | JFFS2 (as available) |
| `ubireader` / `ubi_reader` | UBI/UBIFS |
| `fakeroot`, `cpio`, `gzip`/`xz` | initramfs / cpio archives |
| `7z` / `tar` / `unzip` | Vendor outer wrappers |
| `qemu-system-*` / `qemu-user` (later) | Emulation — only after sandbox decision |
| `r2` / `rabin2` / Ghidra | Binary triage hand-off |

```bash
binwalk -h | head
which unsquashfs sasquatch jefferson ubireader_extract_images 2>/dev/null
```

Document missing tools; partial extract is still useful.

## Workflow

### 1. Preserve and fingerprint

```bash
mkdir -p derived/firmware
cp -n firmware.bin derived/firmware/firmware.bin   # or copy once; never overwrite original
sha256sum firmware.bin | tee derived/firmware/firmware.bin.sha256
file firmware.bin
ls -la firmware.bin
```

```bash
# Header / magic
xxd firmware.bin | head -n 20
strings -n 8 firmware.bin | rg -i 'u-boot|linux version|squashfs|UBI|jffs2|OpenWrt|buildroot|Android' | head
```

Record: size, entropy impressions (binwalk will expand), any vendor version strings in the first/last 64 KiB.

```bash
# Tail often holds signatures or dual-image metadata
xxd firmware.bin | tail -n 20
strings -n 8 -t x firmware.bin | tail
```

### 2. Signature scan (binwalk)

```bash
binwalk firmware.bin | tee derived/firmware/binwalk.txt
binwalk -E firmware.bin | tee derived/firmware/binwalk-entropy.txt   # entropy plot data if supported
```

Read the table for:

| Signature (examples) | Meaning |
| --- | --- |
| uImage / TRX / Android bootimg | Bootloader / kernel wrapper |
| gzip/xz/lzma compressed data | Nested payload — extract and re-scan |
| Squashfs filesystem | Common Linux rootfs |
| JFFS2 / UBIFS / CramFS | Flash filesystems |
| ELF | Embedded kernels or bare binaries at offset |
| PKCS / cert / private key markers | Crypto material (handle carefully) |

```bash
# Extract all known signatures to derived tree (does not modify original)
binwalk -e -M -C derived/firmware/binwalk-root firmware.bin
# -e extract, -M matryoshka recursive, -C output dir
```

If auto-extract fails on SquashFS, note the **decimal offset** from `binwalk` and carve manually (next steps).

### 3. Carve by offset when needed

```bash
# Example: SquashFS at offset 0x00100000 (replace with real offset from binwalk)
OFFSET=$((0x00100000))
dd if=firmware.bin of=derived/firmware/rootfs.squashfs bs=1 skip=$OFFSET status=progress
file derived/firmware/rootfs.squashfs
binwalk derived/firmware/rootfs.squashfs
```

Compressed kernel payload example:

```bash
OFFSET=$((0x00020000))
dd if=firmware.bin of=derived/firmware/payload.gz bs=1 skip=$OFFSET
file derived/firmware/payload.gz
gunzip -k derived/firmware/payload.gz 2>/dev/null || xz -d -k derived/firmware/payload.xz
binwalk derived/firmware/payload
```

Always re-run `file` + `binwalk` on carved pieces.

### 4. Filesystem extract

#### SquashFS

```bash
unsquashfs -d derived/firmware/rootfs derived/firmware/rootfs.squashfs
# If vendor-modified squashfs:
sasquatch derived/firmware/rootfs.squashfs -d derived/firmware/rootfs
```

#### JFFS2

```bash
# Tooling varies; jefferson is common in firmware RE kits
jefferson derived/firmware/rootfs.jffs2 -d derived/firmware/rootfs-jffs2
# Or:
# binwalk -e may already drop jffs2-root
```

#### UBI / UBIFS

```bash
ubireader_display_info firmware.bin
ubireader_extract_images -o derived/firmware/ubi firmware.bin
ubireader_extract_files -o derived/firmware/ubifs firmware.bin
```

#### initramfs / cpio

```bash
# After finding ASCII cpio or gzip-compressed initramfs
mkdir -p derived/firmware/initramfs
cd derived/firmware/initramfs
gzip -dc ../initramfs.gz | cpio -idmv
# or: cpio -idmv < ../initramfs.cpio
```

#### Vendor outer package

```bash
7z x -o derived/firmware/outer firmware.bin
# or unzip / tar as file(1) indicates — then binwalk inner images
find derived/firmware/outer -type f -exec file {} \;
```

### 5. Rootfs triage (configs, secrets, attack surface)

Work **read-only** on the extract; copy singles out for analysis.

```bash
ROOT=derived/firmware/rootfs
find "$ROOT" -type f | head -200
find "$ROOT" -type f \( -name 'passwd' -o -name 'shadow' -o -name '*config*' -o -name '*.pem' -o -name '*.key' \) 2>/dev/null
```

High-value paths (presence varies by distro):

| Path pattern | Why |
| --- | --- |
| `/etc/passwd`, `/etc/shadow`, `/etc/public.key` | Accounts / embedded keys |
| `/etc/config/*` (OpenWrt UCI) | Network, wifi defaults |
| `/etc_ro/`, `/etc/defaults/` | Factory defaults, often hard-coded creds |
| `/www/`, `/usr/www/`, lighttpd/nginx conf | Web admin surface |
| `/usr/bin/`, `/sbin/`, `/bin/` | Busybox applets + custom admin binaries |
| `/lib/`, `/usr/lib/*.so` | Custom libs (crypto, cloud client) |
| `/etc/ssl/`, `*.pem`, `*.crt` | TLS material |
| NV-style: `nvram`, `xxx_default.xml` | Default SSID/passwords |

```bash
# Credential-oriented strings (redact in reports)
rg -n -i 'password|passwd|pwd=|admin|root:|private_key|BEGIN RSA|api[_-]?key|secret' "$ROOT" 2>/dev/null | head -100

# Web and service clues
rg -n -i 'cgi-bin|lighttpd|httpd|dropbear|telnet|ubus|tr-069|cwmp' "$ROOT" 2>/dev/null | head -80

# Busybox vs real ELFs
file "$ROOT"/bin/* "$ROOT"/sbin/* "$ROOT"/usr/bin/* 2>/dev/null | rg 'ELF|symbolic'
```

List setuid and world-writable only as **lab findings** (local privesc context on emulated/device lab):

```bash
find "$ROOT" -type f -perm -4000 2>/dev/null
find "$ROOT" -type f -perm -0002 2>/dev/null | head
```

### 6. Kernel / version notes

```bash
strings firmware.bin | rg -i 'Linux version [0-9]' | head
strings "$ROOT"/bin/busybox | rg -i 'BusyBox v' | head
cat "$ROOT"/etc/openwrt_release 2>/dev/null
cat "$ROOT"/etc/os-release 2>/dev/null
```

Architecture of extracted ELFs drives later QEMU/`binary-re` choices:

```bash
file "$ROOT"/bin/busybox
readelf -h "$ROOT"/bin/busybox 2>/dev/null | rg -i 'Class|Machine'
rabin2 -I "$ROOT"/usr/sbin/httpd 2>/dev/null
```

### 7. Basic binary RE triage (hand-off, not full RE)

For each interesting ELF (httpd, cloud agent, custom `*`d):

```bash
BIN="$ROOT/usr/sbin/interestingd"
mkdir -p derived/firmware/bins
cp -n "$BIN" derived/firmware/bins/
sha256sum derived/firmware/bins/* | tee derived/firmware/bins/hashes.txt

file "$BIN"
rabin2 -I "$BIN"
rabin2 -l "$BIN"
rabin2 -zz "$BIN" | rg -i 'http|ssl|password|sprintf|/etc|nvram|system\(' | head -50
```

Then open **`binary-re`** (triage → static). Dynamic run / service emulation:

1. Prefer **`security-sandbox`** (snapshot, no production net).
2. Use `binary-re/dynamic-analysis` (QEMU user/system) for syscalls and behavior.
3. If a real or emulated userspace is running **same arch**, runtime hooks may use **`frida-hooking-playbook`**.

Do **not** run unknown extracted daemons on a production host.

### 8. Flash dump vs upgrade package

| Source | Notes |
| --- | --- |
| Vendor upgrade `.bin` | Often header + kernel + rootfs; binwalk usually enough |
| Full NAND/NOR dump | Multiple partitions; use offsets from bootloader docs or repeated binwalk; watch OOB/spare if raw NAND |
| Android `boot.img` / `system.img` | May need `unpack_bootimg` / `simg2img` then mount or debugfs — still hash-first, extract to `derived/` |

```bash
# sparse Android system image (if applicable)
simg2img system.img derived/firmware/system.raw.img
# mount only inside lab VM with clear authorization
```

### 9. Failure modes

| Problem | Action |
| --- | --- |
| SquashFS “magic” but unsquashfs fails | Try `sasquatch`; wrong offset; LZMA variant; endianness |
| binwalk false positives | Confirm with `file` on carve; check entropy; ignore tiny “filesystem” hits |
| Encrypted rootfs | Look for decrypt stub in bootloader/userland; keys in earlier partition; stop and document — no guessing vendor DRM keys outside scope |
| Partial dump | Note missing partitions; avoid claiming complete SBOM |
| Windows host paths | Run binwalk/WSL/Linux VM; keep `derived/` on a case-sensitive volume when possible |

## Routing

| Observation / need | Next skill |
| --- | --- |
| Extracted ELF needs full RE | `binary-re` → `binary-re/triage` then static/dynamic |
| RE tools missing | `binary-re/tool-setup` |
| Emulate or detonate untrusted extract | `security-sandbox` then `binary-re/dynamic-analysis` |
| Runtime hooks on emulated/on-device process | `frida-hooking-playbook` |
| Device is Android app-centric, not raw flash | `android-pentesting-tricks` |
| TLS traffic from device after lab boot | `tls-plaintext-acquisition` → `mobile-ssl-pinning-bypass` if pin blocks |
| PCAP from device network | `traffic-analysis-pcap` / `NetworkProtocolAnalysisSkill` |
| Hidden data in non-firmware carrier | `steganography-techniques` |

**Primary vs helper:** Firmware image unpack/triage → this skill. Any serious binary understanding → `binary-re`. Isolation → `security-sandbox`. Mobile app package testing → `android-pentesting-tricks`. Pinning on companion apps → `mobile-ssl-pinning-bypass`.

## Output Checklist

- [ ] Image path, size, SHA-256 (original preserved)
- [ ] `file` + `binwalk` summary (key offsets/signatures)
- [ ] Extract command(s) and `derived/` layout
- [ ] Rootfs type (squashfs/jffs2/ubifs/initramfs/other)
- [ ] OS/distro/kernel/busybox version strings (if any)
- [ ] Architecture of primary ELFs
- [ ] Interesting configs, default creds (redacted for share-out), web stack notes
- [ ] List of high-value binaries copied for RE (with hashes)
- [ ] Encryption/packing blockers still open
- [ ] Explicit next skill: usually `binary-re` and/or `security-sandbox`

## Rules

- Authorized firmware only; ownership or written scope required for dumps and live device work.
- Never overwrite the only firmware copy; extract only under `derived/`.
- Do not flash patched images or default-credential abuse against systems outside scope.
- Treat private keys and cloud tokens as secrets; minimize retention.
- Validate “findings” with file paths + hashes + command output, not guesswork from a single `strings` hit.
- Encrypted blobs: document evidence of encryption; do not invent keys.
- Execution and network-connected emulation only inside an agreed sandbox (`security-sandbox`).
