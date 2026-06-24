# Full-Stack Docker Deployment Pattern

## Architecture: Nginx (Frontend) → FastAPI (Backend)

For projects with both a React/Vite frontend and a Python/FastAPI backend, use a two-container architecture behind Nginx.

### Directory Structure
```
project/
├── app/                  # FastAPI backend code
│   ├── main.py
│   ├── routers/
│   └── services/
├── frontend/             # React/Vite source
│   ├── src/
│   ├── dist/             # Built output (after npm run build)
│   └── package.json
├── nginx.conf            # Nginx reverse proxy config
├── docker-compose.yml    # Two services: app + nginx
├── Dockerfile            # Backend only (multi-stage Python)
└── requirements.txt
```

### nginx.conf Template
```nginx
server {
    listen 3000;
    server_name localhost;

    # Swagger UI — MUST be before SPA fallback
    location /docs {
        proxy_pass http://app:8000/docs;
        proxy_set_header Host $host;
    }
    location /openapi.json {
        proxy_pass http://app:8000/openapi.json;
    }

    # API reverse proxy with path rewrite
    location /api/ {
        rewrite ^/api/(.*)$ /api/v1/$1 break;
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Health checks
    location /health { proxy_pass http://app:8000; }
    location /ready  { proxy_pass http://app:8000; }

    # Frontend SPA (must be last)
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

### docker-compose.yml Template
```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: project-backend
    expose: ["8000"]
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///app/data/app.db
      - CORS_ALLOWED_ORIGINS=*
    volumes:
      - app-data:/app/data
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8000/health"]
      interval: 30s

  nginx:
    image: nginx:alpine
    container_name: project-frontend
    ports: ["3000:3000"]
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      app:
        condition: service_healthy

volumes:
  app-data:
    driver: local
```

### Key Pitfalls
1. **Health check uses GET not HEAD**: `wget --spider` sends HEAD requests which FastAPI may reject. Use `wget -qO-` instead.
2. **Alpine vs Slim C-library mismatch**: If builder uses `python:3.12-slim` (glibc), production MUST also use slim, not alpine (musl). Mixing causes `ModuleNotFoundError` for compiled packages like pydantic-core.
3. **Nginx SPA fallback swallows /docs**: Always register `/docs` and `/openapi.json` proxy locations BEFORE the `try_files` catch-all in nginx.conf.
4. **Port conflict on host**: If something else binds port 3000, Docker fails with "address already in use". Kill the old process before `docker compose up`.
