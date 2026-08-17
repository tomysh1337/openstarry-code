#!/usr/bin/env python3
import argparse
import json
import re
import struct
import sys
import zipfile
from pathlib import Path


PRINTABLE_RE = re.compile(rb"[ -~]{4,}")

SIGNATURES = {
    "zkm_or_zelix": [rb"Zelix", rb"KlassMaster", rb"\bZKM\b"],
    "jnic_or_native_obfuscator": [
        rb"JNIC",
        rb"native-obfuscator",
        rb"native obfuscator",
        rb"JNI_OnLoad",
        rb"RegisterNatives",
        rb"Java_",
    ],
    "vmprotect_or_vmp": [rb"VMProtect", rb"VMProtectBegin", rb"vmpsoft", rb"\.vmp0", rb"\.vmp1", rb"\.vmp"],
    "themida_or_winlicense": [rb"Themida", rb"WinLicense", rb"\.themida", rb"\.winlice"],
    "allatori": [rb"Allatori", rb"allatori"],
    "dasho": [rb"DashO", rb"PreEmptive"],
    "stringer": [rb"Stringer", rb"Licel"],
    "proguard_or_r8": [rb"ProGuard", rb"proguard", rb"com.android.tools.r8", rb"\bR8\b"],
}

NATIVE_SUFFIXES = (".so", ".dll", ".dylib", ".jnilib")
CLASS_SUFFIX = ".class"
DEX_SUFFIX = ".dex"


def strings_from_bytes(data, limit=10000):
    out = []
    for match in PRINTABLE_RE.finditer(data):
        out.append(match.group().decode("latin1", errors="ignore"))
        if len(out) >= limit:
            break
    return out


def scan_signatures(data):
    hits = {}
    for name, patterns in SIGNATURES.items():
        matched = []
        for pat in patterns:
            if re.search(pat, data, re.IGNORECASE):
                matched.append(pat.decode("latin1", errors="ignore"))
        if matched:
            hits[name] = sorted(set(matched))
    return hits


def parse_class(data):
    result = {
        "valid": False,
        "major_version": None,
        "utf8_constants": [],
        "native_methods": [],
        "parse_error": None,
    }
    try:
        if len(data) < 10 or data[:4] != b"\xca\xfe\xba\xbe":
            result["parse_error"] = "not a class file"
            return result
        minor, major, cp_count = struct.unpack_from(">HHH", data, 4)
        result["major_version"] = major
        pos = 10
        cp = [None] * cp_count
        i = 1
        while i < cp_count:
            tag = data[pos]
            pos += 1
            if tag == 1:
                size = struct.unpack_from(">H", data, pos)[0]
                pos += 2
                raw = data[pos : pos + size]
                pos += size
                text = raw.decode("utf-8", errors="replace")
                cp[i] = text
                result["utf8_constants"].append(text)
            elif tag in (3, 4):
                pos += 4
            elif tag in (5, 6):
                pos += 8
                i += 1
            elif tag in (7, 8, 16, 19, 20):
                pos += 2
            elif tag in (9, 10, 11, 12, 17, 18):
                pos += 4
            elif tag == 15:
                pos += 3
            else:
                raise ValueError(f"unknown constant pool tag {tag} at index {i}")
            i += 1

        pos += 6
        interfaces_count = struct.unpack_from(">H", data, pos)[0]
        pos += 2 + interfaces_count * 2

        def skip_members(pos):
            count = struct.unpack_from(">H", data, pos)[0]
            pos += 2
            for _ in range(count):
                pos += 6
                attr_count = struct.unpack_from(">H", data, pos)[0]
                pos += 2
                for _ in range(attr_count):
                    pos += 2
                    attr_len = struct.unpack_from(">I", data, pos)[0]
                    pos += 4 + attr_len
            return pos

        pos = skip_members(pos)
        method_count = struct.unpack_from(">H", data, pos)[0]
        pos += 2
        for _ in range(method_count):
            access_flags, name_idx, desc_idx, attr_count = struct.unpack_from(">HHHH", data, pos)
            pos += 8
            name = cp[name_idx] if 0 <= name_idx < len(cp) else f"#{name_idx}"
            desc = cp[desc_idx] if 0 <= desc_idx < len(cp) else f"#{desc_idx}"
            if access_flags & 0x0100:
                result["native_methods"].append(f"{name}{desc}")
            for _ in range(attr_count):
                pos += 2
                attr_len = struct.unpack_from(">I", data, pos)[0]
                pos += 4 + attr_len

        result["valid"] = True
        return result
    except Exception as exc:
        result["parse_error"] = str(exc)
        return result


def classify_blob(name, data):
    lower = name.lower()
    kind = "blob"
    if lower.endswith(CLASS_SUFFIX) or data[:4] == b"\xca\xfe\xba\xbe":
        kind = "class"
    elif lower.endswith(DEX_SUFFIX) or data[:3] == b"dex":
        kind = "dex"
    elif lower.endswith(NATIVE_SUFFIXES) or data[:4] == b"\x7fELF" or data[:2] == b"MZ":
        kind = "native"
    hits = scan_signatures(data)
    info = {"name": name, "kind": kind, "signature_hits": hits}
    if kind == "class":
        class_info = parse_class(data)
        info["major_version"] = class_info["major_version"]
        info["native_methods"] = class_info["native_methods"]
        cp_text = "\n".join(class_info["utf8_constants"]).encode("utf-8", errors="ignore")
        cp_hits = scan_signatures(cp_text)
        if cp_hits:
            info["constant_pool_hits"] = cp_hits
    if kind == "native":
        s = strings_from_bytes(data, limit=2000)
        interesting = [
            x
            for x in s
            if any(token in x.lower() for token in ("jni", "java/", "vmprotect", ".vmp", "themida", "register"))
        ][:50]
        info["interesting_strings"] = interesting
    return info


def analyze_zip(path):
    report = {
        "artifact": str(path),
        "type": "zip",
        "entries": 0,
        "classes": 0,
        "dex_files": 0,
        "native_libraries": 0,
        "native_methods": 0,
        "class_versions": {},
        "indicators": {},
        "notable_entries": [],
        "native_method_examples": [],
        "native_libraries_list": [],
    }
    with zipfile.ZipFile(path) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        report["entries"] = len(infos)
        for info in infos:
            name = info.filename
            lower = name.lower()
            if lower.endswith(CLASS_SUFFIX):
                report["classes"] += 1
            elif lower.endswith(DEX_SUFFIX):
                report["dex_files"] += 1
            elif lower.endswith(NATIVE_SUFFIXES):
                report["native_libraries"] += 1
                report["native_libraries_list"].append(name)

            if any(x in lower for x in ("manifest", "plugin.yml", "mods.toml", "fabric.mod.json", "paper-plugin.yml")):
                report["notable_entries"].append(name)

            if lower.endswith(CLASS_SUFFIX) or lower.endswith(DEX_SUFFIX) or lower.endswith(NATIVE_SUFFIXES) or "manifest" in lower:
                data = zf.read(info, pwd=None)
                blob = classify_blob(name, data)
                merge_indicators(report["indicators"], blob.get("signature_hits", {}))
                merge_indicators(report["indicators"], blob.get("constant_pool_hits", {}))
                if blob["kind"] == "class":
                    version = str(blob.get("major_version"))
                    report["class_versions"][version] = report["class_versions"].get(version, 0) + 1
                    natives = blob.get("native_methods", [])
                    report["native_methods"] += len(natives)
                    for method in natives:
                        if len(report["native_method_examples"]) < 25:
                            report["native_method_examples"].append(f"{name}: {method}")
                if blob["kind"] == "native" and blob.get("interesting_strings"):
                    report["notable_entries"].append(f"{name}: native strings matched")

    report["notable_entries"] = sorted(set(report["notable_entries"]))[:100]
    report["native_libraries_list"] = sorted(report["native_libraries_list"])[:100]
    report["hypotheses"] = hypotheses(report)
    return report


def merge_indicators(target, hits):
    for key, values in hits.items():
        target.setdefault(key, [])
        target[key].extend(values)
        target[key] = sorted(set(target[key]))


def hypotheses(report):
    out = []
    indicators = report.get("indicators", {})
    if "zkm_or_zelix" in indicators:
        out.append("strong: explicit ZKM/Zelix indicator")
    if "jnic_or_native_obfuscator" in indicators:
        out.append("strong: explicit JNI/JNIC/native-obfuscator indicator")
    if "vmprotect_or_vmp" in indicators:
        out.append("strong: explicit VMProtect/VMP indicator")
    if "themida_or_winlicense" in indicators:
        out.append("strong: explicit Themida/WinLicense indicator")
    if report.get("native_libraries", 0) and report.get("native_methods", 0):
        out.append("medium: Java native methods plus bundled native libraries")
    if report.get("dex_files", 0) and report.get("native_libraries", 0):
        out.append("medium: Android DEX plus native libraries")
    if not out:
        out.append("unknown: no strong protector signature; use bytecode and runtime triage")
    return out


def analyze_path(path):
    if zipfile.is_zipfile(path):
        return analyze_zip(path)
    data = path.read_bytes()
    blob = classify_blob(str(path), data)
    report = {
        "artifact": str(path),
        "type": blob["kind"],
        "indicators": blob.get("signature_hits", {}),
        "hypotheses": [],
    }
    if blob["kind"] == "class":
        report["major_version"] = blob.get("major_version")
        report["native_methods"] = blob.get("native_methods", [])
        merge_indicators(report["indicators"], blob.get("constant_pool_hits", {}))
    if blob["kind"] == "native":
        report["interesting_strings"] = blob.get("interesting_strings", [])
    report["hypotheses"] = hypotheses(report)
    return report


def print_text(report):
    print(f"artifact: {report['artifact']}")
    print(f"type: {report['type']}")
    for key in ("entries", "classes", "dex_files", "native_libraries", "native_methods"):
        if key in report:
            print(f"{key}: {report[key]}")
    if report.get("class_versions"):
        print(f"class_versions: {report['class_versions']}")
    if report.get("indicators"):
        print("indicators:")
        for key, values in report["indicators"].items():
            print(f"  - {key}: {', '.join(values)}")
    print("hypotheses:")
    for item in report.get("hypotheses", []):
        print(f"  - {item}")
    if report.get("native_libraries_list"):
        print("native_libraries:")
        for item in report["native_libraries_list"][:20]:
            print(f"  - {item}")
    if report.get("native_method_examples"):
        print("native_method_examples:")
        for item in report["native_method_examples"][:10]:
            print(f"  - {item}")
    if report.get("interesting_strings"):
        print("interesting_strings:")
        for item in report["interesting_strings"][:20]:
            print(f"  - {item}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Passive triage for protected Java/JNI artifacts.")
    parser.add_argument("artifact", help="Path to JAR/WAR/APK/AAB/class/native library")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    path = Path(args.artifact)
    if not path.exists():
        parser.error(f"artifact not found: {path}")
    report = analyze_path(path)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
