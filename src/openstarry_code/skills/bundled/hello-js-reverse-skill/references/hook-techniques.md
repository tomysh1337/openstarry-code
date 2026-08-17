# Observation Hooks

Install the narrowest hook that reveals the decisive request path. Start with observation-only hooks and change one variable at a time.

## Cookie Descriptor Rule

`document.cookie` is normally defined on `Document.prototype` or another prototype, not on the `document` instance. Find the descriptor owner and wrap its original getter and setter:

```javascript
(function() {
    var owner = document;
    var descriptor = null;
    while (owner) {
        descriptor = Object.getOwnPropertyDescriptor(owner, 'cookie');
        if (descriptor) break;
        owner = Object.getPrototypeOf(owner);
    }
    if (!owner || !descriptor || typeof descriptor.get !== 'function' || typeof descriptor.set !== 'function') return;

    var originalGet = descriptor.get;
    var originalSet = descriptor.set;
    Object.defineProperty(owner, 'cookie', {
        get: function() { return originalGet.call(this); },
        set: function(value) {
            console.log('[Hook:Cookie] set:', String(value));
            console.trace('[Hook:Cookie] call stack');
            return originalSet.call(this, value);
        },
        enumerable: descriptor.enumerable,
        configurable: descriptor.configurable
    });
})();
```

Do not replace `document.cookie` with an in-memory string. That changes cookie semantics and can invalidate the behavior being measured.

## Generated Hooks

Use the local generator:

```bash
node scripts/hook-generator.js --type=xhr --target="/api/"
node scripts/hook-generator.js --type=fetch --target="/api/"
node scripts/hook-generator.js --type=cookie --target="session_name"
node scripts/hook-generator.js --type=all --target="/api/"
```

`--type=all` contains only these observation hooks:

- `cookie`
- `xhr`
- `fetch`
- `json`
- `base64`

The generator escapes the target as a JavaScript string literal. Inspect generated code before injection and remove broad hooks once the decisive function is known.

## Behavior-Changing Hooks

`stealth` and `debugger-bypass` modify page behavior. They are never included in `all` and must be selected explicitly:

```bash
node scripts/hook-generator.js --type=stealth
node scripts/hook-generator.js --type=debugger-bypass
```

Use them only after proving that an observation-only trace is blocked, record the baseline first, and validate that the behavior change did not alter the signature input.

## Capture Sequence

1. Install one XHR or fetch hook before the triggering action.
2. Capture method, URL, headers, body, and call stack.
3. Repeat with one changed input.
4. Hook the nearest parameter builder or serialization boundary.
5. Compare the pre-transform value and output across both samples.
6. Remove the broad hook and reproduce from a reset baseline.
