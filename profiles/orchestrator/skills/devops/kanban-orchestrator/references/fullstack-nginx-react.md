# Full-Stack Deployment: Nginx + FastAPI + React

## Architecture Pattern
Separate containers for Frontend and Backend, bridged by Nginx reverse proxy.

```text
Browser
  ↓ (Port 3000)
┌──────────────────────────────────────┐
│  Nginx Container                     │
│  ├─ /         → React dist/ (SPA)    │
│  └─ /api/*    → http://app:8000      │
└──────────────────────────────────────┘
         ↓ (Internal Network)
┌──────────────────────────────────────┐
│  FastAPI Container (Port 8000)       │
│  ├─ /api/v1/links                   │
│  └─ /health                         │
└──────────────────────────────────────┘
```

## Docker Compose (Production Ready)

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: shortlink-backend
    expose: ["8000"]  # Internal only
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///app/data/shortlink.db
      - CORS_ALLOWED_ORIGINS=*  # Allow Nginx
    volumes:
      - sqlite-data:/app/data
    networks: [app-network]

  nginx:
    image: nginx:alpine
    container_name: shortlink-frontend
    ports: ["3000:3000"]
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      app:
        condition: service_healthy
    networks: [app-network]

volumes:
  sqlite-data:
networks:
  app-network:
    driver: bridge
```

## Nginx Configuration

Crucial for handling SPA routing and API versioning.

```nginx
server {
    listen 3000;
    server_name localhost;

    # 1. Frontend SPA
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html; # Fallback for SPA
    }

    # 2. Backend API Proxy
    # Rewrite /api/* to /api/v1/* to match backend routes
    location /api/ {
        rewrite ^/api/(.*)$ /api/v1/$1 break;
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 3. Health Checks
    location /health { proxy_pass http://app:8000; }
    location /ready  { proxy_pass http://app:8000; }
}
```

## Build Commands

**Frontend (Node.js Docker):**
```bash
docker run --rm -v ./frontend:/app -w /app node:18-alpine sh -c "npm install && npm run build"
```
*Result: `./frontend/dist/` contains static assets.*

**Backend (FastAPI Docker):**
```bash
docker compose up -d --build
```
