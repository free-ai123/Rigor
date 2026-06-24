---
name: github-workflow
description: "Complete GitHub workflow: auth, repo management, PR lifecycle, code review, and issues via gh CLI or REST fallback."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Workflow, Pull-Requests, Code-Review, Issues, Authentication, Repositories, CI/CD, Git]
---

# GitHub Workflow

Complete guide for all GitHub interactions. Every section shows `gh` CLI first, then `git` + `curl` fallback for machines without `gh`.

## Auth Detection (use this FIRST)

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

# Extract owner/repo from remote
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/ ]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## Section A: Authentication Setup

Load this section when the user needs to set up GitHub auth for the first time, or when auth is broken.

### Method 1: Git-Only (No gh, No sudo)

**HTTPS with Personal Access Token:**
1. User creates token at https://github.com/settings/tokens (scopes: `repo`, `workflow`, `read:org`)
2. Configure credential helper: `git config --global credential.helper store`
3. Test: `git ls-remote https://github.com/<user>/<repo>.git` (enter username + token)

**SSH Key:**
```bash
ssh-keygen -t ed25519 -C "email@example.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub  # user adds to https://github.com/settings/keys
ssh -T git@github.com
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### Method 2: gh CLI

```bash
gh auth login                          # interactive browser
echo "<TOKEN>" | gh auth login --with-token  # headless
gh auth setup-git                      # configure git credentials
gh auth status                         # verify
```

### Using GitHub API Without gh

```bash
export GITHUB_TOKEN="<token>"
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | GitHub disabled password auth; use PAT or SSH |
| `Permission denied` | Token lacks `repo` scope; regenerate |
| `Authentication failed` | Stale cached creds; `git credential reject` then re-auth |
| `gh: command not found` + no sudo | Use git-only Method 1 |

---

## Section B: Repository Management

### Cloning
```bash
git clone https://github.com/owner/repo.git
git clone --depth 1 https://github.com/owner/repo.git  # shallow
gh repo clone owner/repo
```

### Creating
```bash
gh repo create my-project --public --clone
gh repo create my-project --private --description "..." --license MIT --clone
# curl fallback: POST https://api.github.com/user/repos
```

### Forking
```bash
gh repo fork owner/repo --clone
git remote add upstream https://github.com/owner/repo.git  # keep in sync
git fetch upstream && git merge upstream/main && git push origin main
```

### Repository Settings
```bash
gh repo edit --description "..." --visibility public
gh repo edit --enable-wiki=false --enable-issues=true
gh repo edit --add-topic "python,machine-learning"
```

### Branch Protection
```bash
# curl only — no gh shortcut
curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{"required_status_checks":{"strict":true,"contexts":["ci/test"]},"required_pull_request_reviews":{"required_approving_review_count":1}}'
```

### Secrets (GitHub Actions)
```bash
gh secret set API_KEY --body "value"
gh secret list
# curl fallback requires PyNaCl encryption — recommend gh for this
```

### Releases
```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release create v1.0.0 ./dist/binary --title "v1.0.0"
gh release list
```

### GitHub Actions
```bash
gh workflow list
gh run list --limit 10
gh run view <ID> --log-failed
gh run rerun <ID> --failed
gh workflow run ci.yml --ref main
```

---

## Section C: Pull Request Lifecycle

### Branch + Commit
```bash
git fetch origin && git checkout main && git pull origin main
git checkout -b feat/description
# (make changes)
git add . && git commit -m "feat: description"
git push -u origin HEAD
```

### Create PR
```bash
gh pr create --title "feat: ..." --body "## Summary\n...\n\nCloses #42"
# curl: POST /repos/$OWNER/$REPO/pulls with head/base/title/body
```

### Monitor CI
```bash
gh pr checks --watch          # poll until complete
# curl: GET /repos/$OWNER/$REPO/commits/$SHA/status
```

### Auto-Fix CI Loop
1. Check CI → identify failures
2. Read failure logs (`gh run view <ID> --log-failed`)
3. Fix code, commit, push
4. Re-check (up to 3 attempts, then ask user)

### Merge
```bash
gh pr merge --squash --delete-branch
gh pr merge --auto --squash --delete-branch  # auto-merge when green
```

---

## Section D: Code Review

### Local (Pre-Push)
```bash
git diff main...HEAD --stat
git diff main...HEAD
# Check for: debug statements, secrets, merge conflicts, large files
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|password\|secret"
```

### Reviewing a PR
```bash
gh pr view 123
gh pr diff 123
gh pr checkout 123              # check out locally
git fetch origin pull/123/head:pr-123 && git checkout pr-123  # git fallback
```

### Leave Comments
```bash
gh pr comment 123 --body "..."
gh pr review 123 --approve --body "LGTM"
gh pr review 123 --request-changes --body "See inline comments"
```

### Inline Review Comments
```bash
HEAD_SHA=$(gh pr view 123 --json headRefOid --jq '.headRefOid')
gh api repos/$OWNER/$REPO/pulls/123/comments \
  --method POST -f body="..." -f path="src/file.py" -f commit_id="$HEAD_SHA" -f line=45 -f side="RIGHT"
```

### Review Checklist
- **Correctness:** Edge cases, error handling, does it do what it claims?
- **Security:** No hardcoded secrets, input validation, no SQL injection/XSS
- **Quality:** Clear naming, DRY, focused functions, no unnecessary complexity
- **Testing:** New paths tested, happy + error cases covered
- **Performance:** No N+1 queries, appropriate caching, no blocking in async
- **Documentation:** Public APIs documented, non-obvious logic commented

---

## Section E: Issues Management

### Viewing
```bash
gh issue list
gh issue list --state open --label "bug"
gh issue view 42
```

### Creating
```bash
gh issue create --title "..." --body "## Description\n...\n\n## Steps to Reproduce\n..." --label "bug" --assignee "user"
```

### Managing
```bash
gh issue edit 42 --add-label "priority:high" --remove-label "needs-triage"
gh issue edit 42 --add-assignee user
gh issue comment 42 --body "..."
gh issue close 42
gh issue reopen 42
```

### Triage Workflow
1. List untriaged: `gh issue list --label "needs-triage"`
2. Read and categorize each
3. Apply labels and priority
4. Assign if owner is clear
5. Comment with triage notes

### Bulk Operations
```bash
gh issue list --label "wontfix" --json number --jq '.[].number' | xargs -I {} gh issue close {} --reason "not planned"
```

---

## Section F: Gists
```bash
gh gist create script.py --public --desc "..."
gh gist list
```

---

## Quick Reference

| Action | gh | curl endpoint |
|--------|-----|--------------|
| Auth status | `gh auth status` | `GET /user` |
| Clone | `gh repo clone o/r` | `git clone` |
| Create repo | `gh repo create` | `POST /user/repos` |
| List PRs | `gh pr list` | `GET /repos/o/r/pulls` |
| Create PR | `gh pr create` | `POST /repos/o/r/pulls` |
| PR diff | `gh pr diff N` | `GET /repos/o/r/pulls/N` |
| Review | `gh pr review N --approve` | `POST /repos/o/r/pulls/N/reviews` |
| List issues | `gh issue list` | `GET /repos/o/r/issues` |
| Create issue | `gh issue create` | `POST /repos/o/r/issues` |
| Comment | `gh issue comment N` | `POST /repos/o/r/issues/N/comments` |
| CI checks | `gh pr checks` | `GET /repos/o/r/commits/SHA/status` |
| Releases | `gh release create` | `POST /repos/o/r/releases` |
| Workflows | `gh workflow list` | `GET /repos/o/r/actions/workflows` |
