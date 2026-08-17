# Research Sources And Verification Notes

This skill synthesizes procedures; it does not copy article prose. Treat the blog sources as leads and the official documentation or reproduced behavior as stronger evidence.

## Original Request Source

- URL: https://bbs.kanxue.com/thread-276068-1.htm
- Indexed title: `[原创]native层逆向分析（上篇）`
- Indexed publication date: 2023-02-10
- Context: Android native-layer prerequisites and reverse-analysis workflow.
- Access note: The live page returned a human-verification gate and the unauthenticated HTTP path returned a cloud-defense timeout. Only the public index title, date, and summary were used. No verification challenge was bypassed.

## CSDN Sources Used

### Native逆向指北(一)——BiliBili Sign

- URL: https://blog.csdn.net/qq_38851536/article/details/114238361
- Published: 2021-02-28
- Source handle: `qq_38851536` / 白龙~
- Contribution: Demonstrates static-vs-dynamic JNI resolution, runtime `RegisterNatives` tuple capture, fixed-input active calls, JNItrace noise reduction, IDA correlation, algorithm fingerprinting, and dynamic buffer verification.
- Verification: The registration layout matches the JNI specification. The workflow was retained; app-specific offsets, keys, commands, and deprecated Frida CLI assumptions were not encoded.

### Android安卓破解之逆向分析SO常用的IDA分析技巧

- URL: https://blog.csdn.net/earbao/article/details/51573833
- Published: 2016-06-03
- Source handle: `earbao`
- Contribution: Provides practical leads for importing structures, correcting function boundaries, distinguishing ARM/Thumb mode, and distrust of failed decompilation.
- Verification: Only version-independent analysis principles were retained. Old IDA menu paths, Android versions, and dump commands are not normative.

### Android中分析某短视频的数据请求加密协议（IDA动态调试SO）第二篇

- URL: https://blog.csdn.net/F0ED9cZN4Ly992G/article/details/78950881
- Published: 2018-01-02
- Source handle: `F0ED9cZN4Ly992G`
- Contribution: Demonstrates managed-to-native tracing, environment-bound behavior, dynamic confirmation of a decisive branch, minimal instruction patching, and end-to-end replay.
- Verification: The skill retains the evidence sequence and patch discipline, not the target-specific bypass or obsolete debugger setup.

### app安卓逆向之Native层代码静态分析基础

- URL: https://blog.csdn.net/weixin_43900244/article/details/118192820
- Published: 2021-06-24; visibly modified in 2022
- Source handle: `weixin_43900244`
- Contribution: Confirms the original article's likely topic shape: ARM basics, IDA, JNI calls, native patching, and library replacement.
- Verification: The visible article body was incomplete and contains simplified register descriptions. It was used only as a topic lead, never as sole technical evidence.

## Primary Documentation

### Android JNI Tips

- URL: https://developer.android.com/training/articles/perf-jni
- Verified claim: Android supports explicit `RegisterNatives` mapping and native-method discovery, and recommends registration from `JNI_OnLoad` for common designs.

### Oracle JNI Specification

- URL: https://docs.oracle.com/javase/8/docs/technotes/guides/jni/spec/functions.html#RegisterNatives
- URL: https://docs.oracle.com/javase/8/docs/technotes/guides/jni/spec/design.html
- Verified claim: Defines `JNINativeMethod`, JNI name encoding, signatures, and registration behavior.

### Frida JavaScript API

- URL: https://frida.re/docs/javascript-api/
- Verified claim: `Interceptor.attach` requires bit zero to represent ARM vs Thumb state for hard-coded 32-bit ARM addresses; pointers returned by Frida APIs are handled correctly. The API also documents module enumeration and address-to-module lookup.

### Arm Procedure Call Standard

- URL: https://github.com/ARM-software/abi-aa/tree/main/aapcs64
- Used for: AArch64 argument, result, preserved-register, and stack conventions. Always consult the current ABI document for aggregates, vector values, variadic functions, and hidden return pointers.

## Validation Performed During Skill Creation

- Parsed a real Android AAR containing multiple ABI shared libraries with the bundled inventory script.
- Verified ELF class, machine, type, hashes, and `PT_LOAD` segment mapping without modifying the archive or libraries.
- Ran Python compilation checks and the skill-creator validator.
- Forward-tested the workflow independently against a realistic Android JNI reverse-engineering prompt.
