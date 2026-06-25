
import os, uuid, sqlite3, bcrypt
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from cryptography.fernet import Fernet

# --- Config ---
# Fix: Docker compose might pass an empty string, check for that
raw_key = os.getenv("AES_KEY")
AES_KEY = raw_key if raw_key else Fernet.generate_key()
if not raw_key:
    print("⚠️ [SECURITY] AES_KEY not set. Using temporary key. Data will be lost on restart.")
    
f = Fernet(AES_KEY)

app = FastAPI(title="SecurePaste", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- DB Setup ---
DATA_DIR = os.path.join("/app", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "securepaste.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS pastes (id TEXT PRIMARY KEY, content BLOB, password_hash TEXT, burn_after_read BOOLEAN, expires_at TEXT)")
init_db()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    try: yield conn
    finally: conn.close()

class PasteReq(BaseModel):
    content: str; password: Optional[str] = None; burn_after_read: bool = False; expiration_seconds: int = 86400

@app.get("/", response_class=HTMLResponse)
async def index():
    try:
        with open(os.path.join(os.path.dirname(__file__), "static", "index.html")) as f: return f.read()
    except FileNotFoundError:
        return "Frontend not found"

@app.post("/api/v1/pastes")
def create(req: PasteReq):
    pid = str(uuid.uuid4())
    exp = (datetime.now() + timedelta(seconds=req.expiration_seconds)).isoformat()
    pwd = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode() if req.password else None
    enc = f.encrypt(req.content.encode())
    with get_db() as db: db.execute("INSERT INTO pastes VALUES (?,?,?,?,?)", (pid, enc, pwd, req.burn_after_read, exp)); db.commit()
    return {"id": pid, "url": f"/p/{pid}", "expires_at": exp}

def parse_datetime(s):
    """兼容 Python 3.6 的 ISO datetime 解析"""
    # Python 3.6 没有 datetime.fromisoformat()，用 strptime 替代
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")

@app.get("/api/v1/pastes/{pid}")
def get_paste(pid: str, x_paste_password: Optional[str] = Header(None)):
    with get_db() as db: row = db.execute("SELECT * FROM pastes WHERE id=?", (pid,)).fetchone()
    if not row: raise HTTPException(404, "Not found")
    if parse_datetime(row["expires_at"]) < datetime.now():
        with get_db() as db: db.execute("DELETE FROM pastes WHERE id=?", (pid,)); db.commit()
        raise HTTPException(404, "Expired")
    if row["password_hash"]:
        if not x_paste_password or not bcrypt.checkpw(x_paste_password.encode(), row["password_hash"].encode()):
            raise HTTPException(401, "Wrong password")
    content = f.decrypt(row["content"]).decode()
    if row["burn_after_read"]:
        with get_db() as db: db.execute("DELETE FROM pastes WHERE id=?", (pid,)); db.commit()
    return {"content": content, "expires_at": row["expires_at"]}

if __name__ == "__main__":
    import uvicorn; uvicorn.run(app, host="0.0.0.0", port=8000)
