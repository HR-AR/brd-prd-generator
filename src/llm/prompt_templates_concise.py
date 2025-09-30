"""
Concise, investor-grade prompt templates for BRD and PRD generation.
No fluff - just high-quality, actionable content.
"""
from datetime import datetime
from typing import Optional


def get_brd_prompt(user_idea: str) -> str:
    """
    Generate concise, investor-grade BRD prompt.

    Focus on substance over word count. Every sentence must add value.
    """
    return f"""Generate an investor-grade Business Requirements Document (BRD) in JSON format.

User's Idea:
{user_idea}

Create a CONCISE but COMPREHENSIVE BRD. Every word must matter. No fluff.

REQUIREMENTS:
- Executive Summary: Clear, compelling, data-driven. Include market size, competitive advantage, ROI.
- Business Context: Market analysis (TAM/SAM/SOM), competitive landscape (3-5 competitors), customer pain points with data.
- Problem Statement: Quantify the problem, identify who's affected, current solution gaps, business impact.
- Objectives: 5-8 SMART objectives with quantifiable KPIs and timelines.
- Scope: 8-12 in-scope features, 5-8 out-of-scope with rationale.
- Stakeholders: 10-15 key roles (CEO, CTO, CPO, CFO, Engineering, Product, Design, QA, Marketing, Sales, Legal, Ops, etc.)
- Success Metrics: 10-15 metrics (revenue, users, engagement, performance, technical).
- Risks: 8-12 risks (technical, market, competitive, regulatory, financial, operational) with mitigation.
- Timeline: 8-12 milestones from planning through scaling.

Return JSON:

{{
  "document_id": "BRD-123456",
  "version": "1.0.0",
  "title": "Strategic title capturing the opportunity",
  "executive_summary": "Market opportunity: [TAM/SAM/SOM with sources]. Problem: [quantified impact]. Solution: [key differentiator]. Business model: [monetization]. Competitive advantage: [moat]. Financial projection: [revenue/users targets]. Strategic importance: [why now].",
  "business_context": "Market Analysis: [specific TAM/SAM/SOM numbers with growth rate]. Competitive Landscape: [3-5 competitors with strengths/weaknesses]. Customer Pain Points: [specific problems with data]. Technology Trends: [relevant shifts]. Opportunity: [why this matters now]. Strategic Fit: [alignment with market].",
  "problem_statement": "Problem: [specific issue]. Affected: [target audience size]. Current solutions: [competitors and their limitations]. Business impact: [cost of not solving]. Opportunity size: [market potential].",
  "objectives": [
    {{
      "objective_id": "OBJ-001",
      "description": "Specific objective with measurable target by date",
      "success_criteria": ["Quantifiable metric 1 with target", "Measurable outcome 2"],
      "business_value": "Revenue/cost/market impact with numbers",
      "priority": "high",
      "kpi_metrics": ["KPI: Target by date", "Metric: % improvement"]
    }}
  ],
  "scope": {{
    "in_scope": ["Feature 1: capability", "Feature 2: capability", "... 8-12 total"],
    "out_of_scope": ["Feature X: defer to v2 because...", "... 5-8 total"]
  }},
  "stakeholders": [
    {{"name": "CEO", "role": "Strategic oversight, investor relations, final decisions", "interest_level": "high", "influence_level": "high"}},
    {{"name": "CTO", "role": "Technical architecture, stack decisions, engineering allocation", "interest_level": "high", "influence_level": "high"}},
    "... 10-15 stakeholders"
  ],
  "success_metrics": [
    "Revenue: $XM ARR within 12 months",
    "Users: X MAU by month 6",
    "Engagement: X% DAU rate",
    "Retention: X% 30-day retention",
    "Performance: <200ms p95 response",
    "... 10-15 metrics"
  ],
  "assumptions": ["Market assumption", "Technical assumption", "... 5-8 total"],
  "constraints": ["Budget: $X", "Timeline: X months", "... 5-8 total"],
  "risks": [
    {{
      "risk_id": "RISK-001",
      "description": "Specific risk with potential impact",
      "impact": "high",
      "probability": "medium",
      "mitigation": "Detailed mitigation strategy"
    }}
  ],
  "timeline": {{
    "milestones": [
      {{"name": "Phase 1: Planning", "target_date": "2025-MM-DD", "deliverables": ["item1", "item2"]}}
    ]
  }}
}}

CRITICAL:
- Be SPECIFIC: Use real numbers, not placeholders
- Be CONCISE: Every sentence must add value
- Be DATA-DRIVEN: Include market sizes, growth rates, targets
- Think STRATEGICALLY: Why now? Why us? What's the moat?
- document_id: "BRD-" + 6 digits
- objective_id: "OBJ-" + 3 digits
- risk_id: "RISK-" + 3 digits
- Return ONLY valid JSON
"""


def get_prd_prompt(user_idea: str, brd_id: Optional[str] = None) -> str:
    """
    Generate concise, implementation-ready PRD prompt.

    Focus on substance over word count. Engineering teams should be able to build from this.
    """
    brd_context = f'\n  "related_brd_id": "{brd_id}",' if brd_id else '\n  "related_brd_id": null,'

    return f"""Generate an implementation-ready Product Requirements Document (PRD) in JSON format.

User's Idea:
{user_idea}

Create a CONCISE but COMPREHENSIVE PRD. Engineering teams must be able to build from this. No fluff.

REQUIREMENTS:
- Product Vision: Long-term vision, market impact, 1yr/3yr/5yr milestones.
- Target Audience: 3-5 personas (demographics, pain points, switching criteria).
- Value Proposition: Core value, differentiation, pricing alignment.
- User Stories: 15-25 stories covering auth, onboarding, core features, settings, admin, edge cases.
- Features: 10-15 major features with detailed descriptions.
- Technical Requirements: 15-20 requirements (architecture, integration, data, infrastructure, security, performance).
- Technology Stack: Specific technologies with versions.
- Architecture: System design, services, data flow, scalability.

Return JSON:

{{{brd_context}
  "document_id": "PRD-654321",
  "version": "1.0.0",
  "product_name": "Clear product name",
  "product_vision": "Vision: [long-term impact]. Market change: [behavior shift]. Differentiation: [key advantages]. Milestones: 1yr [X], 3yr [Y], 5yr [Z]. Why now: [timing rationale].",
  "target_audience": [
    "Persona 1: Demographics [age/income/location]. Behavior: [current tools]. Pain: [specific problems]. Switch if: [benefits]. TAM: X million users.",
    "... 3-5 personas"
  ],
  "value_proposition": "Core value: [specific benefit]. Problems solved: [1, 2, 3]. Differentiation: [vs competitors]. Why users love it: [key reasons]. Monetization: [pricing model]. Virality: [growth mechanism].",
  "user_stories": [
    {{
      "story_id": "US-001",
      "story": "As [persona], I want [action] so that [benefit]",
      "acceptance_criteria": ["Given [context], when [action], then [result]", "Performance: <Xms"],
      "priority": "high",
      "story_points": 5,
      "dependencies": []
    }},
    "... 15-25 stories"
  ],
  "features": [
    {{
      "feature_id": "FEAT-001",
      "name": "Feature name",
      "description": "What it does, why it matters, how users interact, expected outcomes",
      "priority": "high",
      "user_stories": ["US-001"],
      "acceptance_criteria": ["Loads <Xms", "Mobile responsive", "WCAG AA compliant"]
    }},
    "... 10-15 features"
  ],
  "technical_requirements": [
    {{
      "requirement_id": "TR-001",
      "category": "architecture",
      "description": "Microservices: Auth, User, Core, Analytics. REST APIs + message queues. Horizontal scaling.",
      "technology_stack": ["Node.js 20+", "Express", "RabbitMQ"],
      "constraints": ["Scale to X instances", "<100ms inter-service latency"]
    }},
    "... 15-20 requirements"
  ],
  "technology_stack": [
    "Frontend: React 18+, TypeScript, TailwindCSS",
    "Backend: Node.js 20+, Express, Prisma",
    "Database: PostgreSQL 15+, Redis 7+",
    "Infrastructure: AWS (ECS, RDS, S3), Terraform",
    "Auth: Auth0, JWT, OAuth 2.0",
    "Monitoring: DataDog, Sentry, PagerDuty",
    "... 15-20 technologies"
  ],
  "acceptance_criteria": [
    "Signup to value < 5min",
    "X concurrent users, <200ms p95",
    "99.9% uptime",
    "Zero critical security vulnerabilities",
    "... 10-15 criteria"
  ],
  "metrics_and_kpis": [
    "Activation: X% complete onboarding in 24h",
    "Engagement: X% DAU, Y sessions/week",
    "Retention: X% Day 7, Y% Day 30",
    "Revenue: $X MRR in 3mo, Y% conversion",
    "Performance: <200ms p95, <2s load",
    "... 15-20 KPIs"
  ],
  "architecture_overview": "System: [services, gateways, dbs, caching]. Frontend: [SPA, state, routing]. Backend: [service breakdown, communication]. Infrastructure: [cloud, regions, CDN]. Security: [auth, encryption]. Data: [schema, caching, search]. Scalability: [horizontal scaling, sharding].",
  "performance_requirements": [
    "API: p50 <100ms, p95 <200ms",
    "Page load: FCP <1s, TTI <2s",
    "Concurrent: X users per instance",
    "Cache: 90%+ hit rate",
    "... 10-15 requirements"
  ],
  "security_requirements": [
    "Auth: MFA, OAuth 2.0, SAML",
    "Encryption: TLS 1.3, AES-256",
    "API: Rate limiting X req/min",
    "Compliance: GDPR, CCPA, SOC 2",
    "... 10-15 requirements"
  ],
  "dependencies": [
    "Critical: Auth0, Stripe, User API",
    "High: SendGrid, AWS",
    "Medium: Analytics pipeline",
    "... 8-12 dependencies"
  ]
}}

CRITICAL:
- Be IMPLEMENTATION-READY: Engineers can code from this
- Be TECHNICALLY SPECIFIC: Include versions, patterns, architectures
- Be USER-FOCUSED: Tie features to user value
- Include MEASURABLE criteria: Specific numbers
- document_id: "PRD-" + 6 digits
- story_id: "US-" + 3 digits
- Return ONLY valid JSON
"""
