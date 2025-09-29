# Project Context

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