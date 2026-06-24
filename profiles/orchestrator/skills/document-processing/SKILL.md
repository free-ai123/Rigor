---
name: document-processing
description: "Document processing: extract text from PDFs/scans (OCR), edit PDF text/typos, and create/edit PowerPoint presentations."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [document, OCR, PDF, PowerPoint, text-extraction, editing]
---

# Document Processing

## Section A: OCR & Document Text Extraction (ocr-and-documents)

Extract text from PDFs and scanned documents.

- **pymupdf** — extract text from PDFs directly
- **marker-pdf** — OCR for scanned documents, images
- Use when the user needs to read content from a PDF or scan

## Section B: PDF Editing (nano-pdf)

Edit PDF text, fix typos, update titles via nano-pdf CLI using natural language prompts.

- `nano-pdf "Fix the typo on page 3" input.pdf -o output.pdf`
- Non-destructive edits — preserves formatting
- Use NL prompts, not coordinate-based editing

## Section C: PowerPoint (powerpoint)

Create, read, and edit `.pptx` presentations.

- Create new decks with slides, layouts, notes
- Read existing presentations
- Edit slides, text, images
- Support for templates and master slides
