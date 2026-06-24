# PUT Upload Pattern (nginx-style `curl -T`)

User preference: for internal CLI/CI upload workflows, prefer `curl -T` over multipart. Much simpler for scripting.

## UX comparison

```bash
# Multipart (verbose, requires field name)
curl -X POST http://host:8000/api/upload -F "report=@report.html"

# PUT (minimal, nginx-style)
curl -T report.html http://host:8000/upload/report.html
curl -T report.html "http://host:8000/upload/月度报告.html"
curl -T report.html http://host:8000/upload/   # name from file or query

# Batch (cleaner loop)
for f in *.html; do curl -T "$f" http://host:8000/upload/; done
```

## Express implementation

Key difference from multipart: `curl -T` sends raw body via PUT, not `multipart/form-data`. Cannot use multer — need raw body parsing.

```javascript
const express = require('express');
const fs = require('fs');
const path = require('path');

// Raw body parser middleware — streams request body to a file
function putUploadHandler(uploadsDir, { maxSize = 50 * 1024 * 1024, allowedExtensions } = {}) {
  return async (req, res) => {
    // 1. Determine filename
    //    Priority: URL path param > query string > Content-Disposition
    let filename = req.params.filename
      || req.query.name
      || parseContentDispositionFilename(req.headers['content-disposition']);

    if (!filename) {
      return res.status(400).json({ success: false, error: 'No filename specified. Use /upload/<name> or ?name=<name>' });
    }

    // 2. Sanitize + validate
    const safeName = sanitizeFilename(filename);
    const ext = path.extname(safeName).toLowerCase();
    if (allowedExtensions && !allowedExtensions.has(ext)) {
      return res.status(400).json({ success: false, error: `Extension ${ext} not allowed` });
    }

    // 3. Generate timestamped storage name
    const storedName = generateSafeFilename(safeName);
    const filePath = path.join(uploadsDir, storedName);

    // 4. Stream request body directly to file (no buffering entire body)
    const writeStream = fs.createWriteStream(filePath);
    let bytesReceived = 0;
    let aborted = false;

    req.on('data', (chunk) => {
      bytesReceived += chunk.length;
      if (bytesReceived > maxSize && !aborted) {
        aborted = true;
        writeStream.destroy();
        // Clean up partial file
        fs.unlink(filePath, () => {});
        res.status(413).json({ success: false, error: `File too large (max ${maxSize} bytes)` });
        req.destroy();
      }
    });

    req.pipe(writeStream);

    writeStream.on('finish', () => {
      if (aborted) return;
      res.json({
        success: true,
        message: `File "${safeName}" uploaded via PUT`,
        filename: storedName,
        originalName: safeName,
        size: bytesReceived,
      });
    });

    writeStream.on('error', (err) => {
      if (!aborted) {
        res.status(500).json({ success: false, error: 'Write failed: ' + err.message });
      }
      fs.unlink(filePath, () => {});
    });
  };
}

// Parse filename from Content-Disposition header (optional fallback)
function parseContentDispositionFilename(header) {
  if (!header) return null;
  const match = header.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/i);
  return match ? decodeURIComponent(match[1].replace(/"$/, '')) : null;
}

// Mount routes
app.put('/upload/:filename', putUploadHandler(UPLOADS_DIR, { allowedExtensions: ALLOWED_EXTENSIONS }));
app.put('/upload/', putUploadHandler(UPLOADS_DIR, { allowedExtensions: ALLOWED_EXTENSIONS }));
```

## Content-Length validation

`curl -T` sends `Content-Length` header automatically. Validate it upfront before streaming:

```javascript
// Add before the streaming logic:
const contentLength = parseInt(req.headers['content-length'], 10);
if (contentLength > maxSize) {
  return res.status(413).json({ success: false, error: `File too large (${contentLength} bytes, max ${maxSize})` });
}
```

## Coexistence with multipart

Keep both endpoints — PUT for CLI/scripts, POST multipart for browser forms:

| Method | Path              | Body type              | Client          |
|--------|-------------------|------------------------|-----------------|
| PUT    | `/upload/:name`   | Raw file bytes         | curl -T, CI/CD  |
| POST   | `/api/upload`     | multipart/form-data    | Browser AJAX    |
| POST   | `/upload`         | multipart/form-data    | Browser form    |

## Pitfalls

- **express.raw() vs streaming**: `express.raw()` buffers the entire body into memory before the handler runs. For large files, use `req.pipe(writeStream)` instead to stream directly to disk.
- **Missing filename**: `curl -T file.txt http://host/upload/` (trailing slash, no filename in URL) requires fallback to query param or Content-Disposition. Always validate filename is present.
- **HTTP method**: `curl -T` sends PUT, not POST. Make sure routes use `app.put()`, not `app.post()`.
