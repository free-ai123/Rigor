# Gotcha: Race Condition on Burn-After-Read

**Severity**: High  
**Created**: 2026-06-24  
**Project**: SecurePaste  
**Status**: Active

---

## Scenario

In the SecurePaste project, the `burn_after_read` feature was implemented as:

```python
# BAD - Race condition
paste = db.query(Paste).filter_by(id=paste_id).first()
if paste:
    content = paste.content
    db.delete(paste)
    db.commit()
    return content
```

Under concurrent access (10 simultaneous requests), multiple requests read the content before any of them deleted it.

---

## Root Cause

SELECT followed by DELETE without a transaction lock creates a time-of-check-to-time-of-use (TOCTOU) race condition.

---

## Solution

Use `SELECT ... FOR UPDATE` within a transaction:

```python
# GOOD - Atomic
with db.transaction():
    paste = db.query(Paste).filter_by(id=paste_id).with_for_update().first()
    if paste:
        content = paste.content
        db.delete(paste)
        db.commit()
        return content
    return None  # Already deleted
```

---

## Prevention

**For ALL projects with delete-after-read patterns:**
1. Tech Lead must review concurrency requirements during architecture phase
2. Code Reviewer must check for transaction locks on delete-after-read code
3. QA Engineer must include concurrent access test cases (TC-003 in SecurePaste)
