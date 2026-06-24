---
name: productivity-apps
description: "Productivity and document tools: Airtable, Google Workspace, Linear, Maps, Notion, OCR/documents, PowerPoint, Teams meeting pipeline."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [airtable, google, linear, maps, notion, ocr, powerpoint, teams, productivity]
    category: productivity
---

# Productivity Apps Suite

Eight productivity and document tools for different workflows.

---

## Mode A: Airtable REST API

**Trigger:** "airtable", "base", "records", "upsert", "table"

CRUD via curl with Bearer auth. Key patterns:
```bash
# List records with filter
curl -s "https://api.airtable.com/v0/{baseId}/{tableId}?filterByFormula={condition}" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY"

# Upsert (create or update by a field)
curl -s -X PATCH "https://api.airtable.com/v0/{baseId}/{tableId}" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"records":[{"fields":{"Name":"Test","Status":"Active"},"id":"recXXX"}]}'

# Create record
curl -s -X POST "https://api.airtable.com/v0/{baseId}/{tableId}" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"records":[{"fields":{"Name":"New Record"}}]}'
```

Filter syntax uses Airtable formula language: `AND({Status}="Active", {Priority}>=3)`

---

## Mode B: Google Workspace (Gmail, Calendar, Drive, Docs, Sheets)

**Trigger:** "gmail", "google calendar", "google drive", "google docs", "google sheets"

Uses gws CLI or Python API. Covers:
- **Gmail:** Read, search, compose, send, label, thread management
- **Calendar:** Create events, list calendars, find free slots
- **Drive:** Upload, download, search, share, permissions
- **Docs:** Create, read, edit, format
- **Sheets:** Read/write cells, formulas, formatting

Requires OAuth setup via `hermes setup` or service account credentials.

---

## Mode C: Linear (Project Management)

**Trigger:** "linear", "issue", "project", "team", "cycle"

GraphQL API via curl. Key patterns:
```bash
# Create issue
curl -s -X POST "https://api.linear.app/graphql" \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { issueCreate(input:{title:\"Bug\",teamId:\"TEAM_ID\"}){success issue{id title}}}"}'

# List issues
curl -s -X POST "https://api.linear.app/graphql" \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ issues { nodes { id title status priority } } }"}'
```

---

## Mode D: Maps (Geocoding, POIs, Routes)

**Trigger:** "geocode", "find nearby", "route", "directions", "distance"

Uses OpenStreetMap/OSRM (free, no API key):
- **Geocoding:** `https://nominatim.openstreetmap.org/search?q={query}&format=json`
- **Reverse geocoding:** `https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json`
- **Routing:** `https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson`
- **POI search:** `https://nominatim.openstreetmap.org/search?q={type}+near+{location}&format=json`

Rate limit: 1 request/second. Add `&accept-language=en` for English results.

---

## Mode E: Notion

**Trigger:** "notion", "page", "database", "workspace"

Notion REST API + ntn CLI. Key patterns:
```bash
# Search pages/databases
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28" \
  -d '{"query":"meeting"}'

# Create page
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"parent":{"database_id":"DB_ID"},"properties":{"Name":{"title":[{"text":{"content":"New Page"}}]}}}'

# ntn CLI shortcut
ntn create "Page Title" --parent DATABASE_ID
```

---

## Mode F: OCR & Document Processing

**Trigger:** "extract text from PDF", "OCR", "scan", "parse document", "read PDF"

- **pymupdf** (PyMuPDF): `fitz.open("file.pdf")` → `page.get_text()` — fast, text-based PDFs
- **marker-pdf**: Deep learning-based PDF → markdown conversion — complex layouts, scans
- **ocrmypdf**: CLI for OCR on scanned PDFs — `ocrmypdf input.pdf output.pdf`

Choice depends on PDF type: born-digital → pymupdf; scanned/image → ocrmypdf + marker-pdf.

---

## Mode G: PowerPoint

**Trigger:** "powerpoint", "pptx", "presentation", "slide", "deck"

Create, read, edit .pptx files using python-pptx. Key patterns:
```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()  # new, or Presentation("existing.pptx")
slide = prs.slides.add_slide(prs.slide_layouts[0])  # title slide
slide.shapes.title.text = "Title"
slide.placeholders[1].text = "Subtitle"
prs.save("output.pptx")
```

Supports: text boxes, images, charts, tables, shapes, animations (limited), slide layouts, masters.

---

## Mode H: Teams Meeting Pipeline

**Trigger:** "Teams meeting summary", "meeting notes", "transcript summary"

Operate the Teams meeting summary pipeline via Hermes CLI. Records meeting transcripts, generates summaries, action items, and follow-ups.

Requires Teams integration setup and appropriate permissions.