# Project Retrospective: SecurePaste

**Date**: 2026-06-24  
**Project Type**: Web Application (Secure Text Sharing)  
**Roles Used**: 10 / 12 (Data Scientist & Data Engineer skipped)  
**Duration**: 4.5 hours

---

## What We Built

- **Product**: SecurePaste — ephemeral, encrypted code/text sharing
- **Key Features**:
  - AES-256-GCM encryption at rest
  - Burn-after-read with atomic transaction locking
  - Password protection with bcrypt hashing
  - Syntax highlighting frontend
  - Docker + Redis rate limiting deployment

---

## Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Quality Score | 85/100 | ≥ 80 | ✅ |
| Test Coverage | 89.2% | ≥ 80% | ✅ |
| Security Issues | 1 (High, Fixed) | 0 | ⚠️ |
| Auto-Fix Success | 100% (2/2) | ≥ 80% | ✅ |
| UAT Result | Passed | Passed | ✅ |
| Total Tasks | 14 | - | - |
| Tasks Auto-Fixed | 2 | - | - |

---

## What Went Well

1. **TDD-First Workflow**: QA wrote 42 test cases BEFORE implementation. Engineers implemented to spec. Zero rework on features.
2. **Security Left-Shift**: Security Auditor caught race condition in the design phase. If caught post-deployment, this would have been a data breach.
3. **Self-Correction Loop**: 2 bugs were automatically detected, fixed, and re-verified without human intervention.
4. **Knowledge Reuse**: The `decision-001` (persistent workspace) prevented the code review access issue seen in previous projects.

---

## What Went Wrong

1. **Race Condition on Burn-After-Read** (SEC-001, BUG-001)
   - **Root Cause**: Backend Engineer used SELECT + DELETE without transaction lock
   - **Impact**: Burn-after-read guarantee violated under concurrent access
   - **Fix**: `SELECT ... FOR UPDATE` within a transaction
   - **Lesson**: ALWAYS use transactional locks for delete-after-read patterns

2. **Missing Rate Limiting** (SEC-002, BUG-002)
   - **Root Cause**: DevOps Engineer forgot to configure rate limiting middleware
   - **Impact**: Password endpoint vulnerable to brute force
   - **Fix**: Redis-based token bucket rate limiter
   - **Lesson**: Rate limiting should be in the default CI/CD template, not added manually

---

## Knowledge Captured

New entries added to the knowledge base:

| Entry | Type | Relevance |
|-------|------|-----------|
| `gotcha-race-condition-burn` | Gotcha | ALL delete-after-read patterns |
| `pattern-atomic-delete` | Pattern | Concurrent-safe deletion |
| `pattern-aes256-paste` | Pattern | Encryption at rest for text services |
| `decision-redis-rate-limit` | Decision | Rate limiting with Redis + token bucket |

---

## Next Project Improvements

1. Add rate limiting to the default CI/CD pipeline template
2. Create a "concurrency checklist" for the Tech Lead to review during architecture phase
3. Consider adding a load testing task for projects with concurrent access requirements

---

## Quality Gate Summary

| Gate | Status | Details |
|------|--------|---------|
| Code Review | ✅ Pass | All findings addressed |
| Security Audit | ✅ Pass | SEC-001 fixed, SEC-002 fixed, SEC-003 mitigated |
| QA Test | ✅ Pass | 42/42 tests passed, coverage 89.2% |
| UAT | ✅ Pass | All 5 user stories accepted |

**Overall: PASSED — Project ready for production.**
