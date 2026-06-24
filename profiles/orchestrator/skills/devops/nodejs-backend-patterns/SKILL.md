---
name: nodejs-backend-patterns
description: "Node.js backend development patterns — Express file uploads with non-ASCII filenames, multer config, EJS templates, plus reference for multi-chain collector service architecture."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [nodejs, express, backend, file-upload, multer, ejs]
    related_skills: [kanban-worker]
---

# Node.js Backend Patterns

## When to load

- Building an Express REST API or web app
- Implementing file upload/download endpoints
- User uploads files with non-ASCII names (Chinese, Japanese, Korean, etc.)
- Setting up multer for multipart file handling
- Configuring EJS server-side rendering with AJAX frontend
- Referencing a multi-chain collector service architecture (see references/)

## Multipart filename encoding (CRITICAL)

**Problem**: `multer` (via `busboy`) decodes multipart `Content-Disposition` filenames using **latin-1** (ISO-8859-1) by default. If the browser sends UTF-8 filenames (which all modern browsers do), non-ASCII characters become corrupted:

```
"月度版本总结报告.html" → "æ\x9c\x88åº¦ç\x89\x88æ\x9c¬æ\x8a¥å\x91\x8a.html"
```

The corruption is deterministic: each UTF-8 byte is interpreted as a latin-1 character. This means the original bytes are preserved — you can recover them.

**Fix**: Decode `file.originalname` from latin-1 back to UTF-8 before using it:

```javascript
function decodeOriginalName(originalname) {
  return Buffer.from(originalname, 'latin1').toString('utf8');
}

// Use in multer config:
const storage = multer.diskStorage({
  filename: function (req, file, cb) {
    const decodedName = decodeOriginalName(file.originalname);
    const safeName = generateSafeFilename(decodedName);
    file._decodedOriginalname = decodedName; // attach for later use
    cb(null, safeName);
  },
});

// Use in fileFilter:
fileFilter: function (req, file, cb) {
  const decodedName = decodeOriginalName(file.originalname);
  if (isAllowedExtension(decodedName)) {
    cb(null, true);
  } else {
    cb(new Error('Invalid file type'), false);
  }
}
```

**Always use `_decodedOriginalname` (or equivalent) in responses** instead of `file.originalname`:

```javascript
res.json({
  message: `File "${req.file._decodedOriginalname}" uploaded!`,
  originalName: req.file._decodedOriginalname,
});
```

**Why this happens**: The HTML spec says multipart filenames should be encoded as UTF-8, but busboy (multer's parser) reads them as latin-1 for historical compatibility. The raw bytes arrive intact — they just need re-interpretation.

See `references/multipart-filename-encoding.md` for the full encoding analysis and verification test cases.

## Filename sanitization for international characters

**Wrong**: `/[^a-zA-Z0-9._-]/g` — strips ALL non-ASCII, destroying Chinese/Japanese/Korean characters.

**Correct**: Use Unicode property escapes with the `u` flag:

```javascript
// Keep all letters (\p{L}) and numbers (\p{N}) from any language
safe = safe.replace(/[^\p{L}\p{N}._-]/gu, '_');
```

This preserves:
- English letters (a-z, A-Z)
- Chinese characters (汉字)
- Japanese (ひらがな, カタカナ, 漢字)
- Korean (한글)
- Cyrillic, Arabic, etc.
- Numbers (0-9, ０-９)
- Dots, underscores, hyphens

Only replaces: path separators, control characters, and special symbols.

## Download endpoint with RFC 5987

For browser downloads with non-ASCII filenames, use both `filename` (ASCII fallback) and `filename*` (UTF-8):

```javascript
const encodedName = encodeURIComponent(safeName);
res.setHeader('Content-Disposition',
  `attachment; filename="${encodedName}"; filename*=UTF-8''${encodedName}`
);
```

## Standard Express + Multer + EJS project structure

```
project/
├── app.js              # Express app with routes
├── package.json        # express, multer, ejs, dayjs
├── views/
│   └── index.ejs       # Server-rendered template
├── public/
│   ├── style.css       # Static styles
│   └── app.js          # Frontend JS (AJAX calls)
├── uploads/            # Uploaded files (gitignore)
└── scripts/
    └── health-check.sh # Optional health check
```

### Typical app.js skeleton

```javascript
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const dayjs = require('dayjs');

const app = express();
const PORT = process.env.PORT || 8000;
const UPLOADS_DIR = path.join(__dirname, 'uploads');

// EJS + static + body parsing
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(UPLOADS_DIR));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Ensure uploads dir
if (!fs.existsSync(UPLOADS_DIR)) fs.mkdirSync(UPLOADS_DIR, { recursive: true });

// Multer config (with decodeOriginalName fix)
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOADS_DIR),
  filename: (req, file, cb) => {
    const decoded = decodeOriginalName(file.originalname);
    const safe = generateSafeFilename(decoded);
    file._decodedOriginalname = decoded;
    cb(null, safe);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 50 * 1024 * 1024 }, // 50MB
  fileFilter: (req, file, cb) => {
    const decoded = decodeOriginalName(file.originalname);
    cb(null, /\.(html?|htm)$/i.test(decoded));
  },
});

// Routes: GET /, POST /upload, GET /api/reports, POST /api/upload,
//         POST /api/delete/:filename, GET /reports/:filename, GET /download/:filename
```

### AJAX auto-refresh pattern

For upload/delete without page reload, provide JSON API endpoints alongside traditional form routes:

```javascript
// JSON API for AJAX
app.post('/api/upload', upload.single('report'), (req, res) => {
  res.json({ success: true, files: getReportList() });
});

app.post('/api/delete/:filename', (req, res) => {
  // ... delete logic ...
  res.json({ success: true, files: getReportList() });
});

app.get('/api/reports', (req, res) => {
  res.json({ success: true, files: getReportList() });
});

// Traditional form routes (no-JS fallback)
app.post('/upload', upload.single('report'), (req, res) => {
  res.redirect('/?success=uploaded');
});
```

Frontend uses `fetch()` to call JSON APIs, then re-renders the DOM with the returned `files` array — no `location.reload()` needed.

## Multi-format file upload pattern

When extending beyond HTML to support office formats (PDF, Word, Excel, PPT, images, archives), use this structure:

```javascript
// 1. Extension whitelist as a Set (O(1) lookup)
const ALLOWED_EXTENSIONS = new Set([
  '.html', '.htm', '.pdf', '.doc', '.docx',
  '.xls', '.xlsx', '.ppt', '.pptx',
  '.txt', '.md', '.csv',
  '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp',
  '.zip', '.rar', '.7z', '.tar', '.gz',
]);

// 2. MIME type mapping (for correct Content-Type on download)
function getMimeType(filename) {
  const ext = path.extname(filename).toLowerCase();
  const map = {
    '.html': 'text/html; charset=utf-8',
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.txt': 'text/plain; charset=utf-8',
    '.csv': 'text/csv; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.zip': 'application/zip',
    '.rar': 'application/x-rar-compressed',
  };
  return map[ext] || 'application/octet-stream';
}

// 3. File type classification (for frontend icons/labels)
function getFileTypeInfo(filename) {
  const ext = path.extname(filename).toLowerCase();
  const docs = ['.html','.htm','.pdf','.doc','.docx','.xls','.xlsx','.ppt','.pptx','.txt','.md','.csv'];
  const imgs = ['.png','.jpg','.jpeg','.gif','.bmp','.svg','.webp'];
  const archives = ['.zip','.rar','.7z','.tar','.gz'];
  if (docs.includes(ext)) return { category: 'document', label: ext.replace('.','').toUpperCase(), icon: '📄' };
  if (imgs.includes(ext)) return { category: 'image', label: ext.replace('.','').toUpperCase(), icon: '🖼️' };
  if (archives.includes(ext)) return { category: 'archive', label: ext.replace('.','').toUpperCase(), icon: '📦' };
  return { category: 'other', label: ext.replace('.','').toUpperCase(), icon: '📎' };
}
```

**View/download routing**: HTML files render inline, all others auto-redirect to download:

```javascript
app.get('/reports/:filename', (req, res) => {
  // ... path safety checks ...
  const ext = path.extname(safeName).toLowerCase();
  if (!['.html', '.htm'].includes(ext)) {
    return res.redirect('/download/' + encodeURIComponent(safeName));
  }
  // HTML: render inline
  const content = fs.readFileSync(filePath, 'utf-8');
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(content);
});

app.get('/download/:filename', (req, res) => {
  // ... path safety checks ...
  const content = fs.readFileSync(filePath);
  const encodedName = encodeURIComponent(safeName);
  res.setHeader('Content-Disposition',
    `attachment; filename="${encodedName}"; filename*=UTF-8''${encodedName}`);
  res.setHeader('Content-Type', getMimeType(safeName)); // NOT fixed text/html
  res.setHeader('Content-Length', content.length);
  res.send(content);
});
```

**Security**: Explicitly block executable extensions even if they somehow bypass the whitelist:

```javascript
const BLOCKED_EXTENSIONS = new Set(['.exe', '.bat', '.sh', '.js', '.vbs', '.ps1', '.cmd', '.msi']);
// Check BEFORE the whitelist to give a clear error message
if (BLOCKED_EXTENSIONS.has(path.extname(decodedName).toLowerCase())) {
  return cb(new Error('不允许的文件格式，仅支持: HTML, PDF, Word, Excel, PPT, 文本, 图片, 压缩包'), false);
}
```

**Frontend**: Update the `accept` attribute on the file input to match the backend whitelist:

```html
<input type="file" name="report" accept=".html,.htm,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.md,.csv,.png,.jpg,.jpeg,.gif,.bmp,.svg,.webp,.zip,.rar,.7z,.tar,.gz">
```

## Pitfalls

**multer v2.x changed API**: multer 2.x returns `file.originalname` as latin-1-decoded string (same as 1.x). The `Buffer.from(name, 'latin1').toString('utf8')` fix works for both versions. Always test with actual non-ASCII filenames.

**`express.static` path conflict**: If you mount `app.use('/uploads', express.static(...))`, do NOT also have a route `app.get('/uploads/:filename')` — the static middleware will intercept first. Use a different route prefix like `/reports/:filename` for viewing.

**File deletion race condition**: If multiple requests try to delete the same file simultaneously, `fs.unlink` may throw `ENOENT`. Wrap in try/catch and return success if file is already gone (idempotent delete).

**Large file uploads crash**: Without `limits: { fileSize: N }`, multer buffers entire files into memory. For large uploads, set a limit and handle `MulterError('LIMIT_FILE_SIZE')` gracefully.

**EJS template XSS**: When injecting `reports` data into EJS, use `<%- JSON.stringify(reports) %>` (unescaped) for script tags, but escape all user-facing text with `<%= %>` (escaped). Never use `<%- %>` on raw user input.

**`__dirname` in Docker**: When containerized, `__dirname` resolves to the container path (e.g., `/app/`). Ensure `uploads/` is mapped as a Docker volume, or files disappear on container restart.

**Stale node processes serving old code**: Multiple `node` processes may coexist on the same machine (Hermes gateway, other projects, PM2 workers). Killing `node app.js` via `pkill -f 'node app.js'` may leave a process running from a different path that serves outdated code. **Before starting a new test instance**: (1) `pkill -9 -f node` to kill ALL node processes, (2) verify with `pgrep -af node` that nothing remains, (3) start fresh. Symptom: API endpoints return 404 for routes that exist in your current code — you're hitting an old process.

**`readFileSync` on large files blocks the event loop**: Using `fs.readFileSync()` for file downloads/reads (up to 50MB with multer limits) blocks the entire Node.js process during I/O. Under concurrent load, this causes request queuing and timeouts. **Fix**: Use `fs.createReadStream(filePath).pipe(res)` for downloads, and set `Content-Length` from `fs.statSync` (cheap) before piping. Same applies to `readdirSync` + `statSync` in file listing — use `fs.promises.readdir` + `fs.promises.stat` for async listing.

**Missing `/health` endpoint**: If you ship a `scripts/health-check.sh` that curls `/health`, make sure the Express app actually defines `app.get('/health', ...)`. Common oversight — the script exists but the route doesn't, causing health checks to always fail with 404.

**PM2 auto-restart hides dead processes**: If the service keeps coming back after `kill`, it's managed by PM2. In Hermes environments, **each profile has its own PM2 daemon** at `/root/.hermes/profiles/<profile>/home/.pm2` (plus the default `/root/.pm2`). A previous task may have started `pm2 start ecosystem.config.js` that auto-restarts on kill. To truly stop: (1) find the PM2 daemon: `ps aux | grep 'God Daemon'`, (2) stop the app via that PM2: `PM2_HOME=<path> pm2 delete <app-name>`, or (3) kill the daemon itself: `kill <daemon-pid>`. Verify with `ss -tlnp sport = :<port>` that the port is actually released.

## CLI & programmatic upload

For uploading files from scripts, CI/CD pipelines, or other programs (not browser forms), use `POST /api/upload` which returns JSON. See `references/cli-upload-patterns.md` for curl, Python requests, Python urllib, and batch shell script examples.

**nginx-style PUT upload (`curl -T`)**: For simpler CLI uploads, implement `PUT /upload/:filename` that accepts raw file bytes (no multipart). Preferred by users for scripting/CI workflows. See `references/put-upload-pattern.md` for Express implementation with streaming, size limits, and coexistence with multipart endpoints.
See `references/pm2-multi-daemon.md` for managing PM2 when multiple profile-level daemons coexist.

## Verification checklist

When reviewing an Express + multer upload implementation:
- [ ] `decodeOriginalName()` applied to `file.originalname` before use
- [ ] Filename sanitization uses Unicode-aware regex (`\p{L}`, `\p{N}`, `u` flag)
- [ ] File extension validated on decoded name (not raw latin-1)
- [ ] `fileSize` limit set in multer config
- [ ] Download endpoint uses `filename*=UTF-8''` for non-ASCII support
- [ ] Path traversal protection: `sanitizeFilename` + `startsWith(UPLOADS_DIR)` check
- [ ] JSON API endpoints return updated file list for AJAX auto-refresh
- [ ] Error responses are JSON (not HTML) for API routes
- [ ] File reads use `createReadStream().pipe()` not `readFileSync` for large files
- [ ] `/health` endpoint defined if health-check script references it
- [ ] PUT upload endpoint (`curl -T` style) implemented if CLI simplicity is a requirement

---

## Multi-Chain Collector Service Architecture

See `references/collector-architecture.md` for the full 38-file structure, 15-table schema, .env config (12 sections), AES-256-GCM key encryption, task locking patterns, nonce allocation, idempotency, RPC failover, and monitoring queries for the ETH/BSC/TRON collector service.

Quick reference — key patterns from the collector:
1. **Task locking**: `UPDATE collect_task SET locked_by=?, locked_until=? WHERE id=? AND status IN (0,3) AND (locked_until IS NULL OR locked_until < UNIX_TIMESTAMP())`
2. **Nonce allocation**: Transaction + `SELECT FOR UPDATE` on nonce_state, `max(local_next_nonce, chain_pending_nonce)`
3. **Idempotency**: `collect_task_open` with `UNIQUE(task_key)` where task_key = `chain:symbol:from_address`
4. **RPC failover**: Query rpc_endpoint ordered by priority ASC, skip status=2 (unhealthy), increment fail_count on error
5. **AES-256-GCM**: Store cipher (TEXT hex) + iv (VARCHAR 12-byte hex) + tag (VARCHAR 16-byte hex) separately
6. **Config-driven**: All thresholds, gas params, confirm blocks, timeouts read from .env via envConfig — zero hardcoded values
