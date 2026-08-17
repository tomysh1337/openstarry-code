---
name: minecraft-mapping-js
description: 编写和调试 Minecraft 1.20.1 Forge/ModLauncher 客户端 JavaScript 插件。适用于 SRG、官方混淆、启动器重映射或魔改端环境，以及 Mojmap 字段名无法直接访问的情况；覆盖类型确认、反射解析、Holder 解包、调试日志和性能安全的成品化流程。
---

# Minecraft 混淆环境 JS 插件编写

本技能面向 Minecraft 1.20.1 及相近 Forge/ModLauncher 客户端脚本环境。输入通常包括 `types.d.ts`、脚本系统说明、Java/Kotlin 参考实现，以及日志或崩溃报告。

## 编写约定

1. 每个插件必须以 IIFE 包裹，避免变量污染。
2. 通过 `client.registerModule(name, key, category, defaultEnable)` 注册模块；不绑定按键使用 `-1`。
3. 事件即使模块未启用也可能触发，因此回调首行检查 `client.isEnabled(MODULE)`。
4. 模块设置使用 `"模块名:设置名"`：`getBool`、`getNumber` 或 `getMode`。

```js
(function () {
    var MODULE = "ModuleName";
    client.registerModule(MODULE, -1, "Visual", false);

    events.on("tick", function () {
        if (!client.isEnabled(MODULE)) return;
        // enabled logic
    });
})();
```

## 先确认运行时类型

源码中的 `MobEffects.NIGHT_VISION`、`Items.DIAMOND_SWORD`、`Blocks.STONE` 等 Mojmap 字段在 Forge/SRG/混淆运行时可能变成 `f_19611_`、`field_XXXXX` 或单字符名。字段读取为 `undefined` 时，先判断映射差异，不要据此认定类不存在。

按以下优先级确定类名：

1. 在 `types.d.ts` 中查找完整类型名，例如 `net_minecraft_world_effect_MobEffects` 对应 `net.minecraft.world.effect.MobEffects`。
2. 查看 Java/Kotlin 参考实现的 `import`。
3. 从日志或崩溃报告提取 Minecraft、Forge/FML、ModLauncher naming、mixin 和调用栈信息。
4. 使用 `Class.forName` 验证候选类名。

```js
var Class = Java.type("java.lang.Class");
try {
    var cls = Class.forName("net.minecraft.world.effect.MobEffects");
    log("class ok: " + cls.getName());
} catch (e) {
    log("class failed: " + e);
}
```

Java 内部类或枚举使用二进制类名，而不是 JS 属性链。例如 Java 源码的 `VertexFormat.Mode` 应加载为 `VertexFormat$Mode`；`types.d.ts` 中扁平化的 `com_mojang_blaze3d_vertex_VertexFormat_Mode` 通常对应同一类型。

```js
var VertexFormatMode = Java.type("com.mojang.blaze3d.vertex.VertexFormat$Mode");
var mode = VertexFormatMode.QUADS;
```

优先传递稳定、完整的类名，由脚本运行时解析类映射；不要手工猜测 `f_`、`field_`、`a/b/c` 一类运行时字段名。

## 以稳定特征扫描混淆字段

字段名不稳定时，枚举静态字段、读取其值，并用对象自身的稳定特征定位目标。启动时扫描一次、缓存结果，随后只使用缓存。

```js
var Class = Java.type("java.lang.Class");
var Modifier = Java.type("java.lang.reflect.Modifier");

function scanStaticFieldOnce(className, predicate) {
    try {
        var cls = Class.forName(className);
        var fields = Java.from(cls.getDeclaredFields());

        for (var i = 0; i < fields.length; i++) {
            var field = fields[i];
            try {
                if (!Modifier.isStatic(field.getModifiers())) continue;
                field.setAccessible(true);

                var value = field.get(null);
                if (predicate(value, field)) return value;
            } catch (inner) {
                // 单个字段不可读时继续扫描。
            }
        }
    } catch (e) {
        log("scan failed: " + className + " " + e);
    }

    return null;
}
```

特征应优先选择以下信息，而不是混淆字段名：

- 注册名或 `ResourceLocation`，如 `minecraft:night_vision`。
- 描述 ID 或 translation key，如 `effect.minecraft.night_vision`。
- 枚举的 `serializedName` / `getSerializedName()`。
- 对象实现的接口、父类或行为方法返回值，如 `getDescriptionId()`、`getRegistryName()`、`builtInRegistryHolder().key().location()`。

字段值可能是目标对象，也可能是 `Holder<T>`。谓词应尝试直接匹配并尝试 `value()` 解包：

```js
function unwrapByDescriptionId(obj, targetId) {
    if (obj == null) return null;

    try {
        if (String(obj.getDescriptionId()) === targetId) return obj;
    } catch (e) {}

    try {
        var value = obj.value();
        if (value != null && String(value.getDescriptionId()) === targetId) return value;
    } catch (e) {}

    return null;
}
```

## 调试到成品的流程

先写调试版，记录：加载与模块注册、`Java.type` / `Class.forName` 结果、字段总数、候选解析结果、命中字段和对象类、构造函数、关键方法返回值、调用后状态、禁用后的清理状态。tick 日志必须限频，例如每两秒一次。

```js
log("[ModuleDBG] loaded");
log("[ModuleDBG] class ok: " + cls.getName());
log("[ModuleDBG] fields count=" + fields.length);
log("[ModuleDBG] resolved by field=" + field.getName());
```

确认类名、字段命中、构造函数签名、方法返回值、状态变更和清理流程后，再精简脚本：删除大部分日志，保留必要 `try/catch`，只在启动阶段执行反射，之后复用缓存对象。tick 内避免高开销扫描和大量日志。

```js
(function () {
    var MODULE = "ModuleName";
    var CATEGORY = "Render";
    var target = scanTargetOnce();

    client.registerModule(MODULE, -1, CATEGORY, false);

    function scanTargetOnce() {
        // Class.forName + reflection scan + stable predicate
        return null;
    }

    function onEnable() {
        if (target == null) return;
        // apply once
    }

    function onDisable() {
        if (target == null) return;
        // cleanup
    }

    function onTick() {
        if (!client.isEnabled(MODULE)) return;
        if (target == null) return;
        // maintain state
    }

    events.on("enable", function (module) {
        if (module === MODULE) onEnable();
    });
    events.on("disable", function (module) {
        if (module === MODULE) onDisable();
    });
    events.on("tick", onTick);
})();
```

## 客户端设置和网络负载

写入 `OptionInstance`、渲染设置、光照贴图、Gamma、Shader 或矩阵前，确认参数的 Java 包装类型。JS 数值可能被推断为 `Integer` 或 `Double`，类型不匹配可能在后续渲染阶段触发 `ClassCastException`。渲染对象还可能被 Embeddium、Oculus、Sodium Extra 或 mixin 修改；优先选用稳定的公开 API、实体效果、状态对象或原版机制。

发送自定义负载时，先由 `types.d.ts` 与实际协议版本确认构造器签名、通道名和缓冲区编码；对每个包的构造与发送结果记录调试日志。
