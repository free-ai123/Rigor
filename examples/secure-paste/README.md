# Example Project: SecurePaste (Secure Code Sharing)

A secure, ephemeral code/text sharing service. **This is a real project output from Rigor.**

> 🔒 Content encrypted at rest · 🔥 Burn-after-read · 🔑 Password protection · ⏱️ Auto-expiration

**中文文档**: [查看中文 README](README.zh.md)

## What's Here

This directory contains the **complete output** of a Rigor project run. Every file was produced by an AI expert role.

```
examples/secure-paste/
├── artifacts/                    # What each role produced
│   ├── product-manager/
│   │   ├── prd.md                # Product Requirements Document (5 user stories)
│   │   └── user-stories.json     # Structured user stories (JSON)
│   ├── tech-lead/
│   │   ├── dag-plan.json         # 14-task DAG with dependencies
│   │   └── module-contracts.json # Module interfaces
│   ├── backend-engineer/
│   │   ├── api-spec.json         # OpenAPI 3.0 spec (4 endpoints)
│   │   ├── db-schema.sql         # PostgreSQL schema with AES encryption
│   │   └── status-report.json    # Task status report
│   ├── security-auditor/
│   │   └── security-report.md    # Security audit (1 High, 2 Medium - all fixed)
│   ├── qa-engineer/
│   │   ├── test-report.md        # 42 tests, 100% pass, 89.2% coverage
│   │   └── test-suite/           # Automated test scripts
│   ├── devops-engineer/
│   │   ├── deployment-config.yaml  # Docker + Redis rate limiting
│   │   └── ci-pipeline.yaml      # CI/CD pipeline
│   └── technical-writer/
│       ├── README.md             # Project documentation
│       └── api-docs.md           # API reference
├── shared/
│   ├── gotchas/
│   │   └── race-condition-burn.md  # Real pitfall found during this project
│   └── retrospectives/
│       └── secure-paste-retro.md   # Project retrospective report
├── dashboard.json                # Final project dashboard (score: 85/100)
└── README.md                     # This file
```

## Key Highlights

### 🔥 Burn-After-Read with Atomic Transactions

The Security Auditor discovered a **race condition** where concurrent reads could bypass burn-after-read:

```python
# BAD - Race condition (caught by Security Auditor)
paste = db.query(Paste).filter_by(id=id).first()
content = paste.content
db.delete(paste)  # Too late! Another request already read it

# GOOD - Fixed with transaction lock
with db.transaction():
    paste = db.query(Paste).filter_by(id=id).with_for_update().first()
    if paste:
        content = paste.content
        db.delete(paste)
        db.commit()
```

This was **automatically detected, reported, and fixed** through Rigor's self-correction loop.

### 🛡️ Security Findings

| Finding | Severity | Status |
|---------|----------|--------|
| Race condition on burn-after-read | 🔴 High | ✅ Fixed |
| Missing rate limiting on password endpoint | 🟡 Medium | ✅ Fixed |
| Content type missing validation | 🟡 Medium | ✅ Mitigated |

### 🧪 QA Results

- **42 tests, 100% pass rate**
- **Line coverage: 89.2%** (gate: ≥80%)
- **Branch coverage: 78.5%** (gate: ≥70%)
- **1 critical bug found and auto-fixed** (race condition)

## Project Metrics

| Metric | Value |
|--------|-------|
| Project Type | Web Application |
| Roles Activated | 10 / 12 |
| Total Tasks | 14 |
| Duration | 4.5 hours |
| Quality Score | **85/100** |
| Auto-Fix Success | 100% (2/2) |
| Knowledge Captured | 3 new entries |

## How to Reproduce

```bash
# 1. Clone Rigor
git clone https://github.com/free-ai123/Rigor.git
cd Rigor

# 2. Deploy
bash scripts/setup-expert-team.sh

# 3. Create the same task
hermes kanban create "Build SecurePaste: an encrypted, ephemeral code sharing service with burn-after-read, password protection, and auto-expiration" --triage

# 4. Watch 12 AI experts collaborate
hermes kanban list
hermes kanban show 1 --tree
```

## Comparison: What Other Tools Miss

| Feature | Rigor | Devin | Cursor | Copilot |
|---------|-------|-------|--------|---------|
| Race condition caught by Security Auditor | ✅ | ❌ | ❌ | ❌ |
| 42 automated tests before implementation | ✅ | ❌ | ❌ | ❌ |
| Burn-after-read atomic transaction | ✅ | ❌ | ❌ | ❌ |
| Auto-fix + re-verify without human help | ✅ | ❌ | ❌ | ❌ |
| Project retrospective with lessons learned | ✅ | ❌ | ❌ | ❌ |
