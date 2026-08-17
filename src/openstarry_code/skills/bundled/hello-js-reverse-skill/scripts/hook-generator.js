#!/usr/bin/env node
'use strict';

const OBSERVATION_TYPES = ['cookie', 'xhr', 'fetch', 'json', 'base64'];
const BEHAVIOR_TYPES = ['stealth', 'debugger-bypass'];

function literal(value) {
    return JSON.stringify(String(value ?? ''));
}

const HOOK_TEMPLATES = {
    cookie: (options = {}) => `(function() {
    var target = ${literal(options.target)};
    var owner = document;
    var descriptor = null;

    while (owner) {
        descriptor = Object.getOwnPropertyDescriptor(owner, 'cookie');
        if (descriptor) break;
        owner = Object.getPrototypeOf(owner);
    }

    if (!owner || !descriptor || typeof descriptor.get !== 'function' || typeof descriptor.set !== 'function') {
        console.warn('[Hook:Cookie] cookie descriptor not found');
        return;
    }
    if (descriptor.configurable === false) {
        console.warn('[Hook:Cookie] cookie descriptor is not configurable');
        return;
    }
    if (descriptor.set.__codexObservationHook) {
        console.log('[Hook:Cookie] already installed');
        return;
    }

    var originalGet = descriptor.get;
    var originalSet = descriptor.set;
    function observedCookieSetter(value) {
        var text = String(value);
        if (!target || text.indexOf(target) !== -1) {
            console.log('[Hook:Cookie] set:', text);
            console.trace('[Hook:Cookie] call stack');
        }
        return originalSet.call(this, value);
    }
    observedCookieSetter.__codexObservationHook = true;

    Object.defineProperty(owner, 'cookie', {
        get: function() { return originalGet.call(this); },
        set: observedCookieSetter,
        enumerable: descriptor.enumerable,
        configurable: descriptor.configurable
    });
    console.log('[Hook:Cookie] observation hook installed on descriptor owner');
})();`,

    xhr: (options = {}) => `(function() {
    var target = ${literal(options.target)};
    var originalOpen = XMLHttpRequest.prototype.open;
    var originalSend = XMLHttpRequest.prototype.send;
    var originalSetHeader = XMLHttpRequest.prototype.setRequestHeader;

    XMLHttpRequest.prototype.open = function(method, url) {
        this.__codexMethod = method;
        this.__codexUrl = String(url);
        this.__codexHeaders = {};
        return originalOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.setRequestHeader = function(name, value) {
        this.__codexHeaders = this.__codexHeaders || {};
        this.__codexHeaders[name] = value;
        return originalSetHeader.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function(body) {
        if (!target || (this.__codexUrl && this.__codexUrl.indexOf(target) !== -1)) {
            console.log('[Hook:XHR]', this.__codexMethod, this.__codexUrl, {
                headers: this.__codexHeaders || {},
                body: body
            });
            console.trace('[Hook:XHR] call stack');
        }
        return originalSend.apply(this, arguments);
    };
    console.log('[Hook:XHR] observation hook installed');
})();`,

    fetch: (options = {}) => `(function() {
    var target = ${literal(options.target)};
    var originalFetch = window.fetch;
    window.fetch = function(input, init) {
        var url = typeof input === 'string' ? input : String(input && input.url || '');
        if (!target || url.indexOf(target) !== -1) {
            console.log('[Hook:Fetch]', url, init || {});
            console.trace('[Hook:Fetch] call stack');
        }
        return originalFetch.apply(this, arguments);
    };
    console.log('[Hook:Fetch] observation hook installed');
})();`,

    json: () => `(function() {
    var originalParse = JSON.parse;
    var originalStringify = JSON.stringify;
    JSON.parse = function(text) {
        var result = originalParse.apply(this, arguments);
        console.log('[Hook:JSON] parse:', typeof text === 'string' ? text.slice(0, 300) : text);
        return result;
    };
    JSON.stringify = function(value) {
        var result = originalStringify.apply(this, arguments);
        console.log('[Hook:JSON] stringify:', typeof result === 'string' ? result.slice(0, 300) : result);
        return result;
    };
    console.log('[Hook:JSON] observation hook installed');
})();`,

    base64: () => `(function() {
    var originalAtob = window.atob;
    var originalBtoa = window.btoa;
    window.atob = function(value) {
        var result = originalAtob.apply(this, arguments);
        console.log('[Hook:Base64] atob:', String(value).slice(0, 160), '=>', String(result).slice(0, 160));
        return result;
    };
    window.btoa = function(value) {
        var result = originalBtoa.apply(this, arguments);
        console.log('[Hook:Base64] btoa:', String(value).slice(0, 160), '=>', String(result).slice(0, 160));
        return result;
    };
    console.log('[Hook:Base64] observation hook installed');
})();`,

    stealth: () => `(function() {
    var navigatorOwner = Object.getPrototypeOf(navigator);
    Object.defineProperty(navigatorOwner, 'webdriver', {
        get: function() { return undefined; },
        configurable: true
    });
    console.warn('[Hook:Stealth] behavior-changing webdriver override installed');
})();`,

    'debugger-bypass': () => `(function() {
    var OriginalFunction = Function;
    window.Function = function() {
        var args = Array.prototype.slice.call(arguments);
        var body = args[args.length - 1];
        if (typeof body === 'string') args[args.length - 1] = body.replace(/debugger\\s*;?/g, '');
        return OriginalFunction.apply(this, args);
    };
    window.Function.prototype = OriginalFunction.prototype;
    console.warn('[Hook:DebuggerBypass] behavior-changing Function override installed');
})();`,
};

function normalizeType(type) {
    return type === 'debugger_bypass' ? 'debugger-bypass' : type;
}

function generateHook(type, options = {}) {
    const normalized = normalizeType(type);
    const generator = HOOK_TEMPLATES[normalized];
    if (!generator) {
        const available = [...OBSERVATION_TYPES, ...BEHAVIOR_TYPES, 'all'].join(', ');
        throw new Error(`Unknown hook type: ${type}. Available types: ${available}`);
    }
    return generator(options);
}

function generateAllHooks(options = {}) {
    const header = `/* Observation-only bundle: ${OBSERVATION_TYPES.join(', ')} */`;
    return [header, ...OBSERVATION_TYPES.map((type) => generateHook(type, options))].join('\n\n');
}

function usage() {
    return [
        'Usage: node hook-generator.js --type=<type> [options]',
        '',
        `Observation types: ${OBSERVATION_TYPES.join(', ')}`,
        '  all              Combine observation types only',
        `Behavior-changing types (explicit only): ${BEHAVIOR_TYPES.join(', ')}`,
        '',
        'Options:',
        '  --target=<text>  Filter cookie or request observations',
        '  --output=<file>  Write generated code to a file',
    ].join('\n');
}

if (require.main === module) {
    const options = {};
    for (const arg of process.argv.slice(2)) {
        if (arg.startsWith('--type=')) options.type = arg.slice(7);
        else if (arg.startsWith('--target=')) options.target = arg.slice(9);
        else if (arg.startsWith('--output=')) options.output = arg.slice(9);
    }

    if (!options.type) {
        console.log(usage());
    } else {
        const code = normalizeType(options.type) === 'all'
            ? generateAllHooks(options)
            : generateHook(options.type, options);
        if (options.output) {
            require('node:fs').writeFileSync(options.output, code);
            console.log(`Hook code written to: ${options.output}`);
        } else {
            console.log(code);
        }
    }
}

module.exports = {
    OBSERVATION_TYPES,
    BEHAVIOR_TYPES,
    HOOK_TEMPLATES,
    generateHook,
    generateAllHooks,
};
