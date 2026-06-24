# Example Project: URL Shortener

This directory shows what Rigor produces after completing a real project.

## What's Here

```
examples/url-shortener/
├── artifacts/                    # What each role produced
│   ├── product-manager/
│   │   ├── prd.md                # Product Requirements Document
│   │   └── user-stories.json     # Structured user stories
│   ├── tech-lead/
│   │   ├── dag-plan.json         # Task dependency graph
│   │   └── module-contracts.json # Module interfaces
│   ├── backend-engineer/
│   │   ├── api-spec.json         # OpenAPI 3.0 specification
│   │   └── db-schema.sql         # Database migrations
│   ├── frontend-engineer/
│   │   ├── component-tree.md     # Component hierarchy
│   │   └── api-integration.md    # API integration guide
│   ├── qa-engineer/
│   │   ├── test-report.md        # Test results and coverage
│   │   └── test-suite/           # Automated test scripts
│   ├── security-auditor/
│   │   └── security-report.md    # Security audit findings
│   ├── devops-engineer/
│   │   ├── deployment-config.yaml  # Deployment configuration
│   │   └── ci-pipeline.yaml      # CI/CD pipeline
│   └── technical-writer/
│       ├── README.md             # Project documentation
│       └── api-docs.md           # API reference
├── shared/
│   ├── decisions/                # Architecture decisions made during this project
│   ├── patterns/                 # Reusable patterns discovered
│   ├── gotchas/                  # Pitfalls encountered
│   └── retrospectives/           # Project retrospective report
└── dashboard.json                # Final project dashboard
```

## How to Use This Example

1. **Study the artifacts** — See what each role produces
2. **Compare to your output** — Is your Rigor project producing similar artifacts?
3. **Use as template** — Copy the structure for your own projects

## Running This Project Yourself

```bash
# Deploy Rigor
bash scripts/setup-expert-team.sh

# Create the same task
hermes kanban create "Build a URL shortener with custom codes, click tracking, and link expiration" --triage

# Watch it work
hermes kanban list
hermes kanban show 1 --tree
```

## Project Summary

| Metric | Value |
|--------|-------|
| Project Type | Web Application |
| Roles Activated | 12 (all) |
| Total Tasks | 14 |
| Duration | ~4 hours |
| Quality Score | 85/100 |
| Test Coverage | 88.5% |
| Auto-Fix Success | 100% (2/2) |
| Security Issues | 1 (Medium, resolved) |
