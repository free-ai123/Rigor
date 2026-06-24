# Multipart Filename Encoding — Analysis & Fix

## The Problem

When a browser uploads a file via `<input type="file">`, it sends the filename in the multipart `Content-Disposition` header:

```
Content-Disposition: form-data; name="report"; filename="月度版本总结报告.html"
```

The filename bytes are UTF-8 encoded. But `busboy` (used by `multer` internally) interprets these bytes as **latin-1** (ISO-8859-1).

## Byte-level Analysis

UTF-8 encoding of "月度":
- `月` → `0xE6 0x9C 0x88`
- `度` → `0xE5 0xBA 0xA6`

When interpreted as latin-1:
- `0xE6` → `æ`
- `0x9C` → `œ` (control char in latin-1 supplement)
- `0x88` → `ˆ` (control char)
- `0xE5` → `å`
- `0xBA` → `º`
- `0xA6` → `¦`

Result: `"月度"` → `"æœˆåº¦"` — which is what you see as "garbled" text.

## The Fix

The bytes are correct — they're just misinterpreted. Re-interpret them:

```javascript
// file.originalname is the latin-1-decoded string from multer
const correct = Buffer.from(file.originalname, 'latin1').toString('utf8');
// "月度版本总结报告.html"
```

This works because:
1. The original UTF-8 bytes arrive intact in the HTTP request
2. Busboy reads them as latin-1, producing a string where each byte → one codepoint
3. `Buffer.from(str, 'latin1')` reverses this: codepoint → byte
4. `.toString('utf8')` re-interprets those bytes as UTF-8

## Verification Test

```javascript
const assert = require('assert');

function decodeOriginalName(name) {
  return Buffer.from(name, 'latin1').toString('utf8');
}

const testCases = [
  { input: 'æ\x9c\x88åº¦ç\x89\x88æ\x9c¬æ\x8a¥å\x91\x8a.html', expected: '月度版本总结报告.html' },
  { input: 'Q2å\xAD£åº¦å\x88\x86æ\x9E\x90æ\x8A¥å\x91\x8A.html', expected: 'Q2季度分析报告.html' },
  { input: 'report.html', expected: 'report.html' }, // ASCII unchanged
];

for (const tc of testCases) {
  const result = decodeOriginalName(tc.input);
  assert.strictEqual(result, tc.expected, `Failed: ${tc.input}`);
}
console.log('All encoding tests passed');
```

## Why multer doesn't fix this

busboy has [an open issue](https://github.com/mscdex/busboy/issues/131) about this. The HTML5 spec says multipart filenames should be UTF-8, but changing busboy's default would break existing code. The fix is left to application code.

## multer version compatibility

| Version | Behavior |
|---------|----------|
| 1.4.x | `file.originalname` is latin-1 decoded |
| 2.0.x | Same — `file.originalname` is latin-1 decoded |
| 2.1.x | Same |

The `Buffer.from(name, 'latin1').toString('utf8')` fix works for all versions.

## Related: RFC 5987 for downloads

When serving files for download with non-ASCII names, browsers need the `filename*` parameter:

```
Content-Disposition: attachment; filename="report.html"; filename*=UTF-8''%E6%9C%88%E5%BA%A6%E6%8A%A5%E5%91%8A.html
```

Node.js implementation:
```javascript
const encoded = encodeURIComponent(utf8Filename);
res.setHeader('Content-Disposition',
  `attachment; filename="${encoded}"; filename*=UTF-8''${encoded}`
);
```
