# Product Requirements Document: SecurePaste

**Version**: 1.0  
**Date**: 2026-06-24  
**Author**: Product Manager (AI)  
**Status**: Approved

---

## 1. Overview

**SecurePaste** is a secure, ephemeral code/text sharing service. Users can paste code or text, optionally set a password, set an expiration time, and generate a shareable link. The content is encrypted at rest and deleted permanently after the first read (burn-after-read) or after expiration.

### Problem Statement

Developers frequently need to share code snippets, logs, or credentials. Existing solutions like Pastebin store data in plaintext indefinitely, creating security and privacy risks. SecurePaste solves this with encryption, expiration, and burn-after-read.

### Target Users

- Developers sharing sensitive code/logs
- Security teams sharing credentials or findings
- Any user needing temporary, secure text sharing

---

## 2. User Stories

### US-001: Create a Secure Paste (P0)
**As a** developer, **I want to** paste text/code and set expiration options, **so that** I can securely share it.

**Acceptance Criteria**:
- Given I'm on the homepage, when I paste text and select expiration (1 hour / 24 hours / 7 days), then I get a unique link
- Given I set a password, when the recipient opens the link, they are prompted for the password before viewing
- Given the paste is created, when I check storage, the content is AES-256 encrypted at rest

### US-002: View and Burn-After-Read (P0)
**As a** recipient, **I want to** view the content once (if burn-after-read is enabled), **so that** the sender knows the data is permanently deleted after viewing.

**Acceptance Criteria**:
- Given the link has burn-after-read enabled, when I view the content, then it is permanently deleted from the database
- Given concurrent access, when two users open the link simultaneously, only ONE can view the content

### US-003: Password Protection (P0)
**As a** sender, **I want to** set a password on my paste, **so that** only people with the password can view it.

**Acceptance Criteria**:
- Given I set a password, when the recipient opens the link, they see a password prompt
- Given a wrong password, when they submit, they see an error (max 5 attempts before temporary lock)
- Given the paste password, it must be stored as bcrypt hash, NOT plaintext

### US-004: Syntax Highlighting (P1)
**As a** developer, **I want** the content to be displayed with syntax highlighting, **so that** code is readable.

### US-005: Raw Link Access (P2)
**As a** developer, **I want** a raw text link (e.g., `/raw/{id}`), **so that** I can use it with `curl` or scripts.

---

## 3. API Requirements

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/v1/pastes` | POST | Create a new paste | None |
| `/api/v1/pastes/{id}` | GET | View paste (triggers burn if enabled) | Password in header/body |
| `/api/v1/pastes/{id}/exists` | HEAD | Check if paste exists | None |
| `/raw/{id}` | GET | Raw text access | Password in header |

### Request/Response Schema

**POST /api/v1/pastes**
```json
{
  "content": "string (max 1MB)",
  "password": "string (optional)",
  "burn_after_read": "boolean (default: false)",
  "expiration_seconds": "integer (3600 / 86400 / 604800)"
}
```

**Response**: `{"id": "uuid", "url": "https://...", "expires_at": "ISO8601"}`

---

## 4. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Encryption | AES-256-GCM at rest |
| Password Storage | bcrypt (cost factor ≥ 12) |
| Response Time | < 200ms for POST, < 100ms for GET |
| Max Content Size | 1 MB |
| Availability | 99.9% |
| Rate Limiting | 10 pastes/minute per IP |

---

## 5. Security Requirements

1. **Content must be encrypted at rest** — Never store plaintext content
2. **Passwords must be hashed with bcrypt** — Never store plaintext passwords
3. **Burn-after-read must be atomic** — Race conditions on concurrent reads are NOT acceptable
4. **Links must be unguessable UUIDs** — No sequential IDs
5. **Rate limiting on password attempts** — Max 5 attempts per 15 minutes

---

## 6. Out of Scope

- User accounts and login
- File upload (text only)
- Team/collaboration features
