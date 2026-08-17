#!/usr/bin/env node
'use strict';

const fs = require('node:fs');

function decodedText(buffer) {
    const text = buffer.toString('utf8');
    if (!text || text.includes('\uFFFD')) return null;
    return /^[\x09\x0a\x0d\x20-\x7e]*$/.test(text) ? text : null;
}

function isCanonicalBase64(value) {
    if (value.length < 4 || value.length % 4 !== 0) return false;
    if (!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
        return false;
    }
    try {
        return Buffer.from(value, 'base64').toString('base64') === value;
    } catch {
        return false;
    }
}

function isCanonicalBase64Url(value) {
    if (!value || !/^[A-Za-z0-9_-]+$/.test(value)) return false;
    const padding = '='.repeat((4 - (value.length % 4)) % 4);
    try {
        return Buffer.from(value + padding, 'base64url').toString('base64url') === value;
    } catch {
        return false;
    }
}

function analyzeValue(input) {
    const value = String(input).trim();
    const candidates = [];
    const properties = {};
    const notes = [];

    if (!value) {
        return {
            input: value,
            length: 0,
            candidates: [{ kind: 'empty', evidence: 'The value is empty.' }],
            properties,
            notes: ['Capture the request before and after the value is populated.'],
        };
    }

    if (/^[0-9]+$/.test(value)) {
        candidates.push({ kind: 'decimal-integer', evidence: `${value.length} decimal digits.` });
        if (value.length === 10 || value.length === 13) {
            notes.push(`The length is compatible with a Unix timestamp in ${value.length === 10 ? 'seconds' : 'milliseconds'}; verify it against capture time.`);
        }
    } else if (/^[0-9a-f]+$/i.test(value) && value.length % 2 === 0) {
        const bytes = Buffer.from(value, 'hex');
        candidates.push({
            kind: 'hex',
            evidence: `${value.length} hexadecimal characters decode to ${bytes.length} bytes.`,
        });
        properties.decodedBytes = bytes.length;
        const text = decodedText(bytes);
        if (text !== null) properties.decodedText = text;
        notes.push('Hex length alone does not distinguish a digest, MAC, ciphertext, random token, or encoded bytes.');
    } else if (/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)) {
        candidates.push({ kind: 'uuid', evidence: 'The value has a canonical UUID shape.' });
    } else if (/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(value)) {
        candidates.push({ kind: 'three-segment-base64url-token', evidence: 'Three dot-separated Base64url-compatible segments.' });
        notes.push('Decode the first two segments for structure, but validate the signing flow separately.');
    } else if (isCanonicalBase64(value) && /[+/=]/.test(value)) {
        const bytes = Buffer.from(value, 'base64');
        candidates.push({
            kind: 'base64',
            evidence: `Canonical standard Base64 syntax with padding or standard-only characters decodes to ${bytes.length} bytes.`,
        });
        properties.decodedBytes = bytes.length;
        const text = decodedText(bytes);
        if (text !== null) properties.decodedText = text;
    } else if (isCanonicalBase64Url(value) && /[-_]/.test(value)) {
        const bytes = Buffer.from(value, 'base64url');
        candidates.push({
            kind: 'base64url',
            evidence: `Canonical Base64url syntax with URL-safe characters decodes to ${bytes.length} bytes.`,
        });
        properties.decodedBytes = bytes.length;
        const text = decodedText(bytes);
        if (text !== null) properties.decodedText = text;
    } else if (/^[\x20-\x7e]+$/.test(value)) {
        candidates.push({ kind: 'printable-text-or-opaque-token', evidence: 'The value contains printable ASCII characters.' });
        if (isCanonicalBase64Url(value)) {
            notes.push('Its alphabet is also Base64url-compatible, but alphabet compatibility alone is not enough to label it as encoded data.');
        }
    } else {
        candidates.push({ kind: 'opaque-or-unicode-value', evidence: 'No strict built-in format matched.' });
    }

    notes.push('Recover the producer call chain and verify a hypothesis with known input and intermediate bytes.');
    return { input: value, length: value.length, candidates, properties, notes };
}

function analyzeMultiple(samples) {
    const normalized = samples.map((sample) => String(sample).trim());
    const analyses = normalized.map(analyzeValue);
    const lengths = [...new Set(normalized.map((sample) => sample.length))];
    const candidateKinds = analyses.map((analysis) => analysis.candidates.map((item) => item.kind));
    const commonKinds = candidateKinds.length === 0
        ? []
        : candidateKinds[0].filter((kind) => candidateKinds.every((kinds) => kinds.includes(kind)));

    return {
        sampleCount: normalized.length,
        lengths,
        fixedLength: lengths.length === 1,
        commonKinds,
        analyses,
        nextStep: 'Compare the changed request input, canonical pre-transform bytes, and output. Do not infer an algorithm from fixed length.',
    };
}

function formatReport(input) {
    const analysis = analyzeValue(input);
    const lines = [
        'Format and encoding triage',
        `Input: ${analysis.input.slice(0, 80)}${analysis.input.length > 80 ? '...' : ''}`,
        `Length: ${analysis.length}`,
        'Candidates:',
    ];

    for (const candidate of analysis.candidates) {
        lines.push(`- ${candidate.kind}: ${candidate.evidence}`);
    }
    if (Object.keys(analysis.properties).length > 0) {
        lines.push(`Properties: ${JSON.stringify(analysis.properties)}`);
    }
    lines.push('Notes:');
    for (const note of analysis.notes) lines.push(`- ${note}`);
    lines.push('Warning: shape alone cannot identify a hash, MAC, cipher, or signing algorithm.');
    return lines.join('\n');
}

function usage() {
    return [
        'Usage:',
        '  node crypto-identifier.js "<value>"',
        '  node crypto-identifier.js --file=<json-file>',
        '  node crypto-identifier.js --compare "<sample-1>" "<sample-2>"',
    ].join('\n');
}

if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length === 0) {
        console.log(usage());
    } else if (args[0] === '--compare') {
        console.log(JSON.stringify(analyzeMultiple(args.slice(1)), null, 2));
    } else if (args[0].startsWith('--file=')) {
        const payload = JSON.parse(fs.readFileSync(args[0].slice(7), 'utf8'));
        const values = Array.isArray(payload) ? payload : Object.values(payload);
        console.log(JSON.stringify(analyzeMultiple(values), null, 2));
    } else {
        console.log(formatReport(args[0]));
    }
}

module.exports = {
    analyzeValue,
    analyzeMultiple,
    formatReport,
    identify: analyzeValue,
};
