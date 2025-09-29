You are my Context Engineering scout.

Here is the project intent (from PRD):
---
Project: New Project

Context (excerpt):
# Product Requirement Document (PRD)

## Idea
Build a production-ready BRD/PRD generation system that automatically converts unstructured business ideas into structured Business Requirement Documents (BRDs) and Product Requirement Documents (PRDs) using multiple LLM providers (ChatGPT-5, Claude 4.1 Opus, Gemini 2.5 Pro). The system provides cost tracking, quality validation, and exports documents in multiple formats.

## Why
- **KPI impact**:
  - Reduce document creation time from 2-3 weeks to < 2 minutes
  - Improve requirement quality with automated SMART criteria validation
  - Reduce rework cycles by ensuring BRD-PRD traceability
  - Lower costs through intelligent LLM provider selection and caching
- **User/Process**:
  - Product Managers: Quickly formalize ideas into standardized documents
  - Engineering Teams: Get clear, validated requirements reducing ambiguity
  - Stakeholders: Faster approval cycles with consistent formatting
  - Process: Fits at project inception phase, before development kickoff
- **Constraints**:
  - Stack: Python 3.11+, FastAPI, Pydantic, multi-LLM support
  - Performance: BRD < 45s, PRD < 60s generation time
  - Cost: < $2.00 per document pair gener
---

Our stack (from CLAUDE.md):
---
## Tech Stack
- Python 3.11+
- FastAPI (async web framework)
- Pydantic v2 (data validation)
- Multiple LLM providers: OpenAI ChatGPT-5, Anthropic Claude 4.1 Opus, Google Gemini 2.5 Pro
- PostgreSQL 15+ (optional, for caching/audit logs)
- pytest + pytest-asyncio for testing
- Docker for containerization

## Project Conventions (initial)
- Async/await for all I/O operations
- Type hints throughout (enforced with mypy)
- Pydantic models for all data validation
- Repository pattern for data access
- Factory pattern for LLM client selection
- Structured logging with contextual information
- All new features require tests and pass validation loop (lint/test/type-check)
- Cost tracking mandatory for all LLM operations
- Security-first: input sanitization, rate limiting, secure credential storage
---

Tasks:
1) Identify common design patterns for this project in the stack above.
2) Source 3–5 public example implementations (docs/blogs/repos). Summarize; do not paste large proprietary code.
3) For each example, provide:
   - PATTERN (name)
   - USE WHEN (scenarios)
   - KEY CONCEPTS (bullets)
   - Minimal, sanitized code stub (safe placeholders, compilable skeleton) for examples/[category]/.
4) Anti-patterns to avoid (short rationale).
5) Test cases (unit + integration) and security/privacy considerations.

Deliverable format (Markdown):
- One section per example, each starting with:
/**
 * PATTERN: ...
 * USE WHEN: ...
 * KEY CONCEPTS: ...
 */
- Short code stub below the header. No business logic, no secrets.
- Add 'Source: <URL>' on a single line for my notes.
