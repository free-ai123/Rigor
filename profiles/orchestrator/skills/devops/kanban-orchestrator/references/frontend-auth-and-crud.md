# Frontend Auth + CRUD Pattern for React + FastAPI Fullstack

Validated pattern for adding user authentication and delete functionality to an existing React frontend that talks to a FastAPI backend.

## Backend: Auth Endpoint

Add a simple login endpoint that returns a token compatible with the existing auth dependency:

```python
# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, email FROM users WHERE email = :email"),
        {"email": body.email}
    )
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Mock token format matching dependencies.py _verify_jwt_token
    token = f"mock:{user.id}:{user.email}"
    return LoginResponse(access_token=token)
```

Register in `main.py`:
```python
from app.routers import auth
app.include_router(auth.router)  # /api/v1/auth
```

## Frontend: Token Injection in API Service

Add token retrieval and Authorization header injection to the shared API service:

```typescript
// src/services/api.ts
const getToken = () => localStorage.getItem('token');

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | {}),
  };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  // ... rest of fetch logic
}

export async function login(email: string, password: string) {
  return request<{ access_token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}
```

## Frontend: Login Page

```typescript
// src/pages/Login.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../services/api';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await login(email, password);
      localStorage.setItem('token', res.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };
  // ... render form with email/password inputs
}
```

## Frontend: Route Guards (ProtectedRoute)

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
};

// Usage:
<Route path="/" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
<Route path="/login" element={<LoginPage />} />
```

## Frontend: Delete with Optimistic Update

```typescript
// In Dashboard or List component
const handleDelete = async (id: number, code: string) => {
  if (!confirm(`Delete "/${code}"?`)) return;
  try {
    await deleteLink(String(id));
    // Optimistic update — remove from local state immediately
    setItems(prev => prev.filter(l => l.id !== id));
    // Refresh related data (e.g. stats)
    const statsRes = await getStats({ days: 14 });
    setStats(statsRes);
  } catch (e) {
    alert("Failed to delete");
  }
};
```

## Frontend: Logout

```typescript
// In Layout component
const handleLogout = () => {
  localStorage.removeItem('token');
  navigate('/login');
};
```

## Pitfalls

1. **PostCSS config ES module syntax**: `postcss.config.js` MUST use `module.exports = {}` (CommonJS), NOT `export default {}` (ESM). Node 18 Vite build will fail with `Unexpected token 'export'`.

2. **401 redirect loop**: If the API service doesn't inject the token, protected routes will 401 → redirect to login → user logs in → token stored → but requests still 401. Verify `getToken()` and header injection work by checking Network tab for `Authorization: Bearer mock:...`.

3. **TypeScript unused imports**: After refactoring api.ts, remove unused type imports (e.g. `Link`) or `tsc` build will fail.

4. **Lucide-react dependency**: If using lucide-react icons, ensure it's in `package.json` dependencies: `"lucide-react": "^0.279.0"`.
