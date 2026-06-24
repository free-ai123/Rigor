# CLI & Programmatic Upload Patterns for Express + Multer

## curl (most common)

```bash
# Single file
curl -X POST http://localhost:8000/api/upload \
  -F "report=@/path/to/file.pdf"

# With custom filename
curl -X POST http://localhost:8000/api/upload \
  -F "report=@/path/to/file.pdf;filename=自定义文件名.pdf"

# Batch upload
for f in /path/to/reports/*.html; do
  curl -s -X POST http://localhost:8000/api/upload -F "report=@$f"
  echo
done
```

## Python requests

```python
import requests

with open("report.pdf", "rb") as f:
    resp = requests.post("http://localhost:8000/api/upload", files={"report": f})
    print(resp.json()["message"])

# Custom filename
with open("report.pdf", "rb") as f:
    resp = requests.post("http://localhost:8000/api/upload", files={
        "report": ("自定义文件名.pdf", f, "application/pdf")
    })
```

## Shell script for batch upload with status

```bash
#!/bin/bash
SERVER="http://localhost:8000/api/upload"
SUCCESS=0; FAIL=0

for file in "$1"/*.html "$1"/*.pdf "$1"/*.docx; do
  [ -f "$file" ] || continue
  filename=$(basename "$file")
  result=$(curl -s -X POST "$SERVER" -F "report=@$file")
  if echo "$result" | grep -q '"success":true'; then
    echo "✅ $filename"
    ((SUCCESS++))
  else
    echo "❌ $filename"
    ((FAIL++))
  fi
done
echo "Done: $SUCCESS ok, $FAIL failed"
```

## Endpoint comparison

| Endpoint | Method | Response | Use case |
|----------|--------|----------|----------|
| `/api/upload` | POST | JSON | Scripts, programs, CLI |
| `/upload` | POST | 302 redirect | Browser forms |
| `/upload/:name` | PUT | JSON | `curl -T` nginx-style (see `put-upload-pattern.md`) |
