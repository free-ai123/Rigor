# Docker Python Multi-Stage — glibc vs musl Compatibility

## The Problem

When using multi-stage Docker builds for Python projects, mixing base image families between stages causes C-extension packages to fail at runtime:

```dockerfile
# Builder stage — glibc
FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage — musl (INCOMPATIBLE!)
FROM python:3.12-alpine AS production
COPY --from=builder /install /usr/local
# → pydantic_core._pydantic_core: ModuleNotFoundError
# → numpy, cryptography, grpcio, etc. will also fail
```

**Root cause**: Alpine Linux uses `musl` libc while Debian (slim) uses `glibc`. C extensions compiled against glibc in the builder stage cannot load in the musl-based production stage.

## The Fix

Use the same base image family for both stages:

```dockerfile
# Builder stage
FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage — same family ✅
FROM python:3.12-slim AS production

# Note: Alpine commands (apk) don't work in slim; use apt-get
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

# Also: Alpine's addgroup/adduser syntax differs from Debian
# Alpine:  RUN addgroup -S appgroup && adduser -S appuser -G appgroup
# Debian:  RUN groupadd -r appgroup && useradd -r -g appgroup appuser
```

## Affected Packages

Any Python package with C extensions will break:
- `pydantic-core` (pydantic v2 dependency)
- `numpy`, `pandas`, `scipy`
- `cryptography`
- `grpcio`
- `psycopg2`, `mysqlclient`
- `lxml`, `Pillow`

Pure Python packages (FastAPI, SQLAlchemy, httpx, etc.) are unaffected.

## Quick Check

If your container logs show `ModuleNotFoundError` for a package you know is installed, run:
```bash
docker exec <container> python -c "import <package>; print(<package>.__file__)"
```
If the `.so` file exists but can't be loaded, it's a libc mismatch.
