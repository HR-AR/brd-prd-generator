# Request
Implement core BRD/PRD document generator with multi-LLM support

## Why
- Reduce document creation time from weeks to minutes
- Ensure consistent quality with automated validation

## Research To-Dos
- [ ] Identify files we'll create/edit
- [ ] Draft pattern stub(s) if missing
- [ ] Define tests & metrics

## Paste-Here Prompts
- WHY/KPIs: Reduce BRD/PRD creation from 2-3 weeks to <2 minutes, improve requirement quality with SMART validation
- File targeting: src/core/generator.py, src/llm/client.py, src/core/models.py
- Pattern stub: Factory pattern for LLM selection, async orchestration for document generation
- Implementation plan: 1) Create Pydantic models 2) Build LLM client wrapper 3) Implement generator orchestration
- Validation fixit: make lint && make test && make build