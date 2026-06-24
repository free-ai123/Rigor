# CR-to-Fix Decomposition Pattern

## When to Use
After a code review produces findings grouped by severity (Critical/High/Medium/Low) across multiple modules, decompose into kanban tasks using this phased approach.

## Phase Structure

### Phase 1: Critical + High (parallel across modules)
Group findings by **module**, not by severity alone. Create one task per module containing all Critical + High issues for that module.

**Rationale**: Critical/High issues block deployment and must be fixed first. Grouping by module allows parallel execution while keeping related changes together.

**Example**:
- Task A: Backend Critical + High (auth, security, N+1 queries)
- Task B: Frontend Critical + High (JWT storage, type safety, accessibility)
- Task C: Infrastructure Critical + High (missing configs, security, CI/CD)
- Task D: Rust Critical + High (concurrency, error handling)

All Phase 1 tasks have **no dependencies** and run in parallel.

### Phase 2: Medium + Low (dependent on Phase 1)
Create one task per module for Medium + Low issues. Each depends on its corresponding Phase 1 task.

**Rationale**: Medium/Low issues often touch the same files as Critical/High fixes. Running them after Phase 1 avoids merge conflicts.

**Example**:
- Task E: Backend Medium + Low (depends on Task A)
- Task F: Frontend Medium + Low (depends on Task B)
- Task G: Tests rewrite (depends on Task A + Task D, since tests cover backend + Rust)

### Phase 3: Review + Security Audit
- Task H: Code review (depends on ALL Phase 2 tasks)
- Task I: Security audit (depends on Task H)

### Phase 4: UAT Re-verification
- Task J: UAT (depends on Task H + Task I)

## Task Body Template

```
你是 [role]。修复第N轮 CR 发现的 [severity] 级问题：

[Issue 1 ID]. [Issue title]
    文件: [file:line]
    修复: [specific fix instruction]

[Issue 2 ID]. [Issue title]
    文件: [file:line]
    修复: [specific fix instruction]

...

所有修复在: ~/projects/[project]/[component]/
修复后运行 [verification command] 验证。
```

## Key Principles

1. **Group by module, not severity**: A backend engineer fixing Critical issues should also fix High issues in the same files to avoid context switching.

2. **Explicit file:line references**: Every issue must cite the exact location. Workers should not search for problems.

3. **Specific fix instructions**: Not "fix this" but "change line X to Y" or "add Depends(get_current_user) to function signature".

4. **Verification command**: End each task with a concrete check (py_compile, cargo check, npm run type-check).

5. **No cross-module dependencies in Phase 1**: Backend Critical fixes should not wait for Frontend Critical fixes. They are independent.

## Common Pitfalls

- **Over-decomposition**: Creating 20 tasks for 20 issues. Group by module to reduce coordination overhead.
- **Under-specification**: "Fix N+1 queries" without file:line. Workers will guess wrong.
- **Missing verification**: No verification command = no confidence the fix works.
- **Phase 1 dependencies**: If Task A depends on Task B in Phase 1, you've mis-grouped. Phase 1 must be fully parallel.
- **f-string interpolation in execute_code**: When building task bodies with `execute_code`, use raw strings or escape carefully. `\\n` in f-strings can produce literal backslash-n in task descriptions instead of newlines. Prefer plain string concatenation or triple-quoted strings without f-variables.
- **CR findings may already be fixed from prior rounds**: When this is a second+ round CR on the same project, some Critical/High issues identified in the fresh review may have already been addressed by a previous UAT fix cycle. Workers will report "already fixed" and complete quickly. This is normal — verify by reading the worker's summary before deciding if follow-up is needed.
- **Quota exhaustion requires fallback to direct execution**: When kanban workers hit HTTP 429 (API quota), switch to `delegate_task` for complex work (subagents share orchestrator quota) and `execute_code` with `read_file`/`patch`/`terminal` for mechanical fixes (no LLM calls). Batch fixes aggressively in Tier 3: read files, apply patches, run py_compile — all without LLM overhead.

## Example from Polymarket CR (2026-05)

**Phase 1** (5 tasks, all parallel):
- T-CR1: Backend Critical (C1-C5)
- T-CR2: Frontend Critical+High (C6, H8-H16)
- T-CR3: Infrastructure Critical+High (C7-C12, H17-H27)
- T-CR4: Backend High (H1-H7)
- T-CR5: Rust Medium (M-R1 to M-R5)

**Phase 2** (3 tasks):
- T-CR6: Backend Medium+Low (depends on T-CR1, T-CR4)
- T-CR7: Frontend Medium+Low (depends on T-CR2)
- T-CR8: Tests rewrite (depends on T-CR1, T-CR4)

**Phase 3** (2 tasks):
- T-CR9: Code review (depends on T-CR3, T-CR5, T-CR6, T-CR7, T-CR8)
- T-CR10: Security audit (depends on T-CR9)

**Phase 4** (1 task):
- T-CR11: UAT (depends on T-CR9, T-CR10)

Total: 11 tasks for 12 Critical + 27 High + 42 Medium + 28 Low findings.
