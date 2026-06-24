# Docker + FastAPI Pitfalls (from short-link-service project)

## Health check: `wget --spider` returns 405 on FastAPI

FastAPI's `@app.get("/health")` only accepts GET requests. `wget --spider` sends a HEAD request, which FastAPI rejects with `405 Method Not Allowed`.

**Fix:** Use `wget -qO-` (sends GET) instead:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:8000/health || exit 1
```

## Multi-stage build: base image must be consistent across stages

If the builder stage uses `python:3.12-slim` (Debian, glibc) and the production stage uses `python:3.12-alpine` (musl), C-extension packages like `pydantic-core` will fail with:
```
ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
```

**Fix:** Use the same base image family across all stages:
```dockerfile
FROM python:3.12-slim AS builder
# ...
FROM python:3.12-slim AS production  # NOT alpine
```

When switching from alpine to slim, change Alpine-specific commands:
- `apk add --no-cache wget` → `apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*`
- `addgroup -S / adduser -S` → `groupadd -r / useradd -r`

## Nginx + FastAPI reverse proxy config

When serving a React SPA via Nginx with FastAPI backend on a separate container:
```nginx
server {
    listen 3000;
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;  # SPA fallback
    }
    location /api/ {
        proxy_pass http://backend:8000;  # Docker service name
    }
}
```

Backend should listen on internal port (e.g. 8000) and NOT expose ports to the host — only Nginx exposes 3000.
