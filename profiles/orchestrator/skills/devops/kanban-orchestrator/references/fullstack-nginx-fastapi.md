# Nginx + React + FastAPI Dual-Container Deployment

Validated working architecture for fullstack projects where:
- **Backend**: FastAPI + Python 3.12-slim (port 8000, internal only)
- **Frontend**: React/Vite compiled to static files, served by Nginx (port 3000, public)

## docker-compose.yml

```yaml
services:
  app:  # Backend
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: shortlink-backend
    expose: ["8000"]  # NOT ports — only accessible to Nginx
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///app/data/shortlink.db
      - CORS_ALLOWED_ORIGINS=*  # Nginx handles CORS
    volumes:
      - sqlite-data:/app/data
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    networks: [app-network]

  nginx:  # Frontend + Reverse Proxy
    image: nginx:alpine
    container_name: shortlink-frontend
    ports: ["3000:3000"]  # Public port
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      app:
        condition: service_healthy
    networks: [app-network]

volumes:
  sqlite-data:
    driver: local
networks:
  app-network:
    driver: bridge
```

## nginx.conf

```nginx
server {
    listen 3000;

    # Frontend static files (SPA with history fallback)
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API reverse proxy — add /v1 prefix if backend needs it
    location /api/ {
        rewrite ^/api/(.*)$ /api/v1/$1 break;
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check proxy (Docker health check hits port 3000)
    location /health {
        proxy_pass http://app:8000;
    }
}
```

## Dockerfile (Backend)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS production
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 8000

# CRITICAL: Use GET (-qO-), not HEAD (--spider) — FastAPI may reject HEAD with 405
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Key Pitfalls

1. **Health check 405**: `wget --spider` sends HEAD, FastAPI `/health` only accepts GET. Use `wget -qO-`.
2. **API prefix mismatch**: Frontend calls `/api/links`, backend expects `/api/v1/links`. Use Nginx `rewrite`.
3. **Field name mismatch**: Frontend sends `url`, backend expects `target_url`. Causes 422 errors.
4. **glibc vs musl**: Builder and production stages must use same base family (both slim or both alpine).
5. **Nginx reload**: After changing nginx.conf, run `docker compose restart nginx`.
