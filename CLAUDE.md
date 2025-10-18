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

## Agent Skills (Official + Custom Auto-Learning)

### Overview
Official Agent Skills with experimental auto-learning layer

### Available Skills
- **Validation Loop** - Self-correcting validation workflow
- **Pattern Scout** - Find external code examples
- **Skill Generator** (Meta) - Creates skills from patterns

### Auto-Learning
```bash
npm run learn:track           # Interactive tracking
npm run learn:record "..." "..."  # Manual tracking
npm run learn:list           # Show learned skills
```

### How It Works
1. Explain methodology (1st time)
2. System tracks pattern (1/2)
3. Similar request (2nd time)
4. Skill auto-generated (2/2)
5. Future requests auto-invoke

### Manual Skills
```bash
npm run skill:create [name]   # Create skill template
npm run skill:list           # Show all skills
```

### Official Format
```yaml
---
name: [Gerund Form]
description: [What + When]
---
[Instructions <500 lines]
```

### Files
```
.claude/
├── skills/
│   ├── validation/
│   ├── scout/
│   └── auto-*/
└── learning/
    └── patterns.json
```

### Integration
Works with existing context-engine.mjs:
- PRP → Scout → Implement → Skills
- Skills auto-invoke based on patterns
- npm run sync updates CLAUDE.md

### References
- [Official Docs](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
