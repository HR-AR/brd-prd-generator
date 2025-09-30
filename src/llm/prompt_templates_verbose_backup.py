"""
Correct prompt templates for BRD and PRD generation that match the actual data models.
"""
from datetime import datetime
from typing import Optional


def get_brd_prompt(user_idea: str) -> str:
    """
    Generate ENTERPRISE-GRADE BRD prompt for investor/executive-level documents.

    This creates comprehensive, boardroom-ready Business Requirements Documents
    that would be suitable for presentation to executives like Elon Musk.
    """
    return f"""Generate an ENTERPRISE-GRADE Business Requirements Document (BRD) in JSON format that would be suitable for presentation to C-level executives and investors.

User's Idea:
{user_idea}

Create a comprehensive, investor-ready BRD with the following structure. Be thorough, strategic, and data-driven:

EXECUTIVE SUMMARY (300-500 words):
- Compelling opening that captures the business opportunity
- Market size and growth potential with specific numbers
- Clear problem statement and proposed solution
- Expected ROI and business impact
- Strategic alignment with market trends

BUSINESS CONTEXT (500-1000 words):
- Detailed market analysis with TAM/SAM/SOM breakdown
- Competitive landscape analysis (identify 3-5 key competitors)
- Market trends and technological shifts
- Customer pain points backed by research/data
- Business opportunity and timing rationale

OBJECTIVES (5-8 SMART objectives):
- Each with quantifiable success criteria
- Clear business value proposition
- Measurable KPI metrics with targets
- Timeline for achievement

SCOPE (comprehensive):
- 8-12 in-scope features/capabilities
- 5-8 out-of-scope items with rationale

STAKEHOLDERS (10-15 roles):
- Include: CEO, CTO, CPO, CFO, Engineering Leads, Product Managers, Design Lead, QA Lead, Marketing, Sales, Customer Success, Legal, Compliance, Operations
- Clear responsibilities and involvement level for each

SUCCESS METRICS (10-15 metrics):
- Revenue metrics (ARR, MRR, Customer LTV)
- User metrics (DAU, MAU, retention, churn)
- Product metrics (engagement, feature adoption)
- Business metrics (CAC, gross margin, burn rate)
- Technical metrics (uptime, performance, scalability)

RISKS (8-12 comprehensive risks):
- Technical risks
- Market risks
- Competitive risks
- Regulatory/compliance risks
- Financial risks
- Operational risks
- Each with detailed mitigation strategy

TIMELINE (8-12 milestones):
- MVP launch
- Beta release
- Market launch
- Key feature releases
- Scaling milestones
- Revenue milestones

Return JSON with this EXACT structure:

{{
  "document_id": "BRD-123456",
  "version": "1.0.0",
  "title": "Strategic, compelling title that captures the opportunity",
  "executive_summary": "COMPREHENSIVE 300-500 word executive summary covering market opportunity, problem, solution, business model, competitive advantage, financial projections, and strategic importance. Include specific numbers and data points.",
  "business_context": "DETAILED 500-1000 word context covering: (1) Market analysis with TAM/SAM/SOM, (2) Competitive landscape with 3-5 competitors analyzed, (3) Customer pain points with data, (4) Technology trends, (5) Business opportunity timing and rationale, (6) Strategic fit",
  "problem_statement": "CLEAR 200-300 word problem statement that: (1) Quantifies the problem size, (2) Identifies who is affected, (3) Explains current solutions and their limitations, (4) Articulates the business impact of not solving this",
  "objectives": [
    {{
      "objective_id": "OBJ-001",
      "description": "SMART objective with Specific, Measurable, Achievable, Relevant, Time-bound criteria",
      "success_criteria": ["Quantifiable criterion with target numbers", "Measurable outcome with timeframe", "Specific deliverable or milestone"],
      "business_value": "Detailed business impact: revenue increase, cost reduction, market share, strategic positioning, competitive advantage",
      "priority": "high",
      "kpi_metrics": ["Specific KPI: Target value by date", "Measurable metric: X% improvement in Y timeframe"]
    }},
    "... 5-8 total objectives covering business, product, technical, and strategic goals"
  ],
  "scope": {{
    "in_scope": [
      "Core Feature 1: Detailed description of capability",
      "Core Feature 2: Detailed description of capability",
      "Integration 1: Specific third-party or system integration",
      "Platform: Web/iOS/Android with specific capabilities",
      "Analytics: Comprehensive tracking and reporting",
      "Security: Authentication, authorization, encryption",
      "Scalability: Support for X concurrent users",
      "Performance: Sub-200ms response times",
      "... 8-12 total in-scope items"
    ],
    "out_of_scope": [
      "Advanced Feature X: Rationale for deferring to v2",
      "International expansion: Focus on domestic market first",
      "Hardware integration: Software-only solution for MVP",
      "... 5-8 out-of-scope items with clear rationale"
    ]
  }},
  "stakeholders": [
    {{
      "name": "Chief Executive Officer (CEO)",
      "role": "Strategic oversight, final decision authority, investor relations, sets company vision and ensures alignment with business strategy",
      "interest_level": "high",
      "influence_level": "high"
    }},
    {{
      "name": "Chief Technology Officer (CTO)",
      "role": "Technical architecture decisions, technology stack selection, engineering resource allocation, ensures technical feasibility and scalability",
      "interest_level": "high",
      "influence_level": "high"
    }},
    "... 10-15 stakeholders including CPO, CFO, Engineering Leads, Product, Design, QA, Marketing, Sales, Legal, Ops"
  ],
  "success_metrics": [
    "Revenue: Achieve $XM ARR within 12 months of launch",
    "User Acquisition: Reach X active users by month 6",
    "Engagement: Achieve X% daily active user rate",
    "Retention: Maintain X% 30-day retention rate",
    "Conversion: Achieve X% free-to-paid conversion",
    "Customer LTV: Reach $X average customer lifetime value",
    "CAC Payback: Achieve CAC payback within X months",
    "NPS Score: Maintain Net Promoter Score above X",
    "Performance: Sub-200ms p95 response time",
    "Uptime: Maintain 99.9% availability SLA",
    "... 10-15 comprehensive metrics covering business, product, and technical KPIs"
  ],
  "assumptions": [
    "Market assumptions: Market growth rate, customer willingness to pay",
    "Technical assumptions: Technology capabilities, integration feasibility",
    "Resource assumptions: Team size, budget, timeline",
    "Regulatory assumptions: Compliance requirements, data privacy",
    "... 5-8 key assumptions"
  ],
  "constraints": [
    "Budget constraint: $X total budget with breakdown",
    "Timeline constraint: X month delivery deadline with rationale",
    "Resource constraint: Team size limitations and skills",
    "Technical constraint: Must integrate with existing systems",
    "Regulatory constraint: GDPR/CCPA/SOC2 compliance required",
    "... 5-8 key constraints"
  ],
  "risks": [
    {{
      "risk_id": "RISK-001",
      "description": "Market Risk: Strong competitor launches similar product before our launch. Could capture market share and establish dominant position.",
      "impact": "high",
      "probability": "medium",
      "mitigation": "Accelerate MVP delivery by X weeks, establish strategic partnerships for distribution, focus on differentiated features X and Y, implement aggressive go-to-market strategy"
    }},
    {{
      "risk_id": "RISK-002",
      "description": "Technical Risk: Scalability challenges as user base grows beyond X users. System performance degradation could lead to churn.",
      "impact": "high",
      "probability": "medium",
      "mitigation": "Design with horizontal scalability from day 1, implement comprehensive load testing, establish auto-scaling infrastructure, plan for database sharding at X users"
    }},
    "... 8-12 comprehensive risks covering technical, market, competitive, financial, regulatory, and operational categories"
  ],
  "timeline": {{
    "milestones": [
      {{
        "name": "Phase 1: Discovery & Planning",
        "target_date": "2025-MM-DD",
        "deliverables": ["Technical architecture design", "User research findings", "Competitive analysis", "Resource plan"]
      }},
      {{
        "name": "Phase 2: MVP Development",
        "target_date": "2025-MM-DD",
        "deliverables": ["Core features X, Y, Z", "Basic analytics", "Auth system", "Initial deployment"]
      }},
      {{
        "name": "Phase 3: Beta Launch",
        "target_date": "2025-MM-DD",
        "deliverables": ["100 beta users onboarded", "Feedback collection system", "Bug fixes", "Performance optimization"]
      }},
      {{
        "name": "Phase 4: Public Launch",
        "target_date": "2025-MM-DD",
        "deliverables": ["Marketing campaign launch", "Sales enablement", "Customer support setup", "Full feature set live"]
      }},
      "... 8-12 milestones covering planning, development, testing, launch, growth phases"
    ]
  }}
}}

CRITICAL REQUIREMENTS:
- Make this INVESTOR-GRADE: Include market data, competitive analysis, financial projections
- Be SPECIFIC with numbers: market sizes, user targets, revenue goals, timelines
- Think STRATEGICALLY: Why now? Why us? What's the moat?
- Be COMPREHENSIVE: Cover all aspects of the business opportunity
- Show DEPTH: Each section should demonstrate deep thinking and analysis
- document_id: "BRD-" followed by 6 digits
- objective_id: "OBJ-" followed by 3 digits
- risk_id: "RISK-" followed by 3 digits
- priority/interest_level/influence_level: "high", "medium", or "low"
- Return ONLY valid JSON, no markdown, no explanations
"""


def get_prd_prompt(user_idea: str, brd_id: Optional[str] = None) -> str:
    """
    Generate ENTERPRISE-GRADE PRD prompt for engineering/product teams.

    This creates comprehensive, implementation-ready Product Requirements Documents
    that engineering teams can use to build production-grade systems.
    """
    brd_context = f'\n  "related_brd_id": "{brd_id}",' if brd_id else '\n  "related_brd_id": null,'

    return f"""Generate an ENTERPRISE-GRADE Product Requirements Document (PRD) in JSON format that engineering teams can use to build a production-ready system.

User's Idea:
{user_idea}

Create a comprehensive, implementation-ready PRD with the following structure. Be technically detailed, user-focused, and actionable:

PRODUCT VISION (200-300 words):
- Inspiring long-term vision
- How this product changes the market/user behavior
- Differentiation from competitors
- Success looks like what in 1 year, 3 years, 5 years

TARGET AUDIENCE (3-5 detailed personas):
- Demographics, psychographics, behaviors
- Pain points and needs
- Current solutions they use
- What would make them switch

VALUE PROPOSITION (150-200 words):
- Core value delivered
- Why users will love this
- Competitive advantages
- Pricing strategy alignment

USER STORIES (15-25 comprehensive stories):
- Cover all user types and workflows
- Include happy paths and edge cases
- Auth, onboarding, core features, settings, admin
- Each with detailed acceptance criteria

FEATURES (10-15 major features):
- Detailed descriptions
- User value and business value
- Technical complexity
- Dependencies and sequencing

TECHNICAL REQUIREMENTS (15-20 requirements):
- Architecture requirements
- Integration requirements
- Data requirements
- Infrastructure requirements
- Security requirements
- Performance requirements
- Scalability requirements

TECHNOLOGY STACK:
- Frontend: Framework, state management, UI library
- Backend: Language, framework, API design
- Database: Primary DB, caching, search
- Infrastructure: Cloud provider, CDN, monitoring
- DevOps: CI/CD, testing, deployment
- Third-party: Auth, payments, analytics, etc.

Return JSON with this EXACT structure:

{{{brd_context}
  "document_id": "PRD-654321",
  "version": "1.0.0",
  "product_name": "Clear, memorable product name",
  "product_vision": "COMPELLING 200-300 word vision covering: (1) Long-term product vision and market impact, (2) How it changes user behavior, (3) Competitive differentiation, (4) Success milestones at 1yr/3yr/5yr, (5) Why this product matters now",
  "target_audience": [
    "Primary Persona: [Name] - Demographics: age X-Y, income $Z, location. Psychographics: tech-savvy, values efficiency. Current behavior: uses competitor X but frustrated with Y. Pain points: specific problem 1, problem 2. Would switch if: benefit 1, benefit 2. TAM: X million users.",
    "Secondary Persona: [Name] - Similar detailed breakdown covering demographics, behaviors, pain points, switching criteria",
    "... 3-5 total detailed personas"
  ],
  "value_proposition": "CLEAR 150-200 word value proposition explaining: (1) Core value delivered to users, (2) Specific problems solved, (3) Key differentiators vs competitors, (4) Why users will love this, (5) Pricing/monetization alignment, (6) Network effects or virality potential",
  "user_stories": [
    {{
      "story_id": "US-001",
      "story": "As a [specific persona], I want to [specific action with context] so that [specific benefit with measurable outcome]",
      "acceptance_criteria": [
        "Given [context], when [action], then [expected result with specifics]",
        "System validates [specific validation] and shows [specific feedback]",
        "Performance: action completes in < Xms",
        "Error handling: displays [specific error message] when [error condition]"
      ],
      "priority": "high",
      "story_points": 5,
      "dependencies": ["US-XXX for authentication"]
    }},
    "... 15-25 user stories covering: Authentication (signup, login, SSO, password reset), Onboarding (profile setup, tutorial, preferences), Core Features (main workflows, all key capabilities), Settings (account, notifications, privacy), Social (sharing, collaboration, comments), Admin (user management, analytics, moderation), Edge Cases (offline, errors, empty states)"
  ],
  "features": [
    {{
      "feature_id": "FEAT-001",
      "name": "Descriptive feature name",
      "description": "DETAILED 100-200 word description covering: what the feature does, why it matters, how users interact with it, expected outcomes, success metrics. Include wireframe/mockup references if available.",
      "priority": "high",
      "user_stories": ["US-001", "US-002", "US-003"],
      "acceptance_criteria": [
        "Feature is accessible from [location] with [interaction]",
        "Supports [specific capabilities] with [specific constraints]",
        "Performance: loads in < Xms, handles Y concurrent operations",
        "Mobile responsive: works on iOS X+ and Android Y+",
        "Accessibility: WCAG 2.1 AA compliant, keyboard navigable"
      ]
    }},
    "... 10-15 features covering all major product capabilities"
  ],
  "technical_requirements": [
    {{
      "requirement_id": "TR-001",
      "category": "architecture",
      "description": "DETAILED requirement: Microservices architecture with API Gateway pattern. Services: Auth Service, User Service, Core Service, Analytics Service. Communication via REST APIs and message queues. Service mesh for observability.",
      "technology_stack": ["Node.js", "Express", "gRPC", "RabbitMQ", "Istio"],
      "constraints": ["Must support horizontal scaling to X instances", "Sub-100ms inter-service latency", "Graceful degradation on service failures"]
    }},
    {{
      "requirement_id": "TR-002",
      "category": "integration",
      "description": "Third-party integrations: Auth0 for authentication, Stripe for payments, SendGrid for email, Twilio for SMS, Segment for analytics, Sentry for error tracking",
      "technology_stack": ["Auth0 SDK", "Stripe API v2023", "SendGrid API", "Twilio API"],
      "constraints": ["All integrations must have fallback mechanisms", "API rate limits handled gracefully", "PII not sent to third parties except necessary"]
    }},
    {{
      "requirement_id": "TR-003",
      "category": "data",
      "description": "Data layer: PostgreSQL for relational data, Redis for caching and sessions, Elasticsearch for search, S3 for file storage. Database sharding strategy for horizontal scaling at X users.",
      "technology_stack": ["PostgreSQL 15+", "Redis 7+", "Elasticsearch 8+", "AWS S3"],
      "constraints": ["99.99% data durability", "RPO < 1 hour", "RTO < 4 hours", "Automatic backups every 6 hours"]
    }},
    {{
      "requirement_id": "TR-004",
      "category": "infrastructure",
      "description": "Cloud infrastructure: AWS multi-region deployment (primary: us-east-1, DR: us-west-2). Auto-scaling groups, load balancers, CDN for static assets. Infrastructure as code using Terraform.",
      "technology_stack": ["AWS ECS", "Application Load Balancer", "CloudFront", "Terraform", "AWS RDS"],
      "constraints": ["Support X concurrent users", "Auto-scale from Y to Z instances based on CPU/memory", "Multi-AZ deployment for HA"]
    }},
    "... 15-20 technical requirements covering architecture, integration, data, infrastructure, security, performance, scalability, monitoring, DevOps, testing"
  ],
  "technology_stack": [
    "Frontend: React 18+, TypeScript, Redux Toolkit, React Query, TailwindCSS, Vite",
    "Backend: Node.js 20+, Express, TypeScript, Prisma ORM, Jest",
    "Database: PostgreSQL 15+, Redis 7+, Elasticsearch 8+",
    "Infrastructure: AWS (ECS, RDS, S3, CloudFront, Route53), Terraform",
    "Authentication: Auth0, JWT, OAuth 2.0, SAML for enterprise",
    "Payments: Stripe (subscriptions, one-time), Stripe Billing Portal",
    "Email: SendGrid (transactional), Mailchimp (marketing)",
    "Analytics: Segment, Google Analytics 4, Mixpanel, Amplitude",
    "Monitoring: DataDog (APM, logs, metrics), Sentry (errors), PagerDuty (alerts)",
    "DevOps: GitHub Actions (CI/CD), Docker, AWS ECR, Terraform Cloud",
    "Testing: Jest, React Testing Library, Playwright (E2E), k6 (load testing)",
    "... 15-20 specific technologies with versions"
  ],
  "acceptance_criteria": [
    "All core user workflows (signup through first value moment) completable in < 5 minutes",
    "System handles X concurrent users with < 200ms p95 response time",
    "99.9% uptime SLA maintained across all services",
    "Zero critical security vulnerabilities (OWASP Top 10)",
    "Mobile responsive on iOS 15+ and Android 10+ devices",
    "WCAG 2.1 AA accessibility compliance across all features",
    "SEO: Core Web Vitals in green, structured data markup, proper meta tags",
    "Internationalization: Support for 5 languages (EN, ES, FR, DE, JP)",
    "Data privacy: GDPR, CCPA compliant, user data export/deletion APIs",
    "... 10-15 overall acceptance criteria"
  ],
  "metrics_and_kpis": [
    "Activation: X% of signups complete onboarding within 24 hours",
    "Engagement: X% daily active user rate, Y average sessions per week",
    "Retention: X% Day 7 retention, Y% Day 30 retention, Z% monthly churn",
    "Revenue: $X MRR within 3 months, Y% free-to-paid conversion, $Z ARPU",
    "Performance: <200ms p95 API response time, <2s page load time",
    "Quality: <0.1% error rate, <10 P1 bugs per month, >90% test coverage",
    "Scale: Support X concurrent users, Y API requests/sec, Z GB data processed",
    "NPS: Maintain Net Promoter Score >50, CSAT >4.5/5",
    "... 15-20 comprehensive KPIs covering activation, engagement, retention, revenue, performance, quality"
  ],
  "architecture_overview": "COMPREHENSIVE 300-500 word architecture description covering: (1) System architecture: microservices, API gateway, databases, caching layers, (2) Frontend architecture: SPA, state management, routing, API integration, (3) Backend architecture: services breakdown, communication patterns, data flow, (4) Infrastructure: cloud provider, regions, CDN, load balancing, auto-scaling, (5) Security: authentication, authorization, encryption, API security, (6) Data architecture: database schema, caching strategy, search indexing, (7) Integration architecture: third-party services, webhooks, event-driven patterns, (8) Scalability: horizontal scaling strategy, database sharding, caching, CDN",
  "performance_requirements": [
    "API Response Times: p50 < 100ms, p95 < 200ms, p99 < 500ms",
    "Page Load Times: First Contentful Paint < 1s, Time to Interactive < 2s",
    "Database Queries: All queries < 50ms, complex queries < 200ms with proper indexing",
    "Concurrent Users: Support X concurrent users per instance, Y total concurrent users",
    "Throughput: Handle X API requests per second, Y database transactions per second",
    "Caching: 90%+ cache hit rate for read-heavy operations",
    "CDN: Static assets served from CDN with <50ms latency globally",
    "Mobile Performance: <3s load time on 3G networks",
    "... 10-15 specific performance requirements"
  ],
  "security_requirements": [
    "Authentication: Multi-factor authentication, OAuth 2.0, SAML for enterprise",
    "Authorization: Role-based access control (RBAC), attribute-based access control for granular permissions",
    "Encryption: TLS 1.3 for data in transit, AES-256 for data at rest",
    "API Security: Rate limiting (X req/min per user), API key rotation, request validation",
    "Data Privacy: GDPR, CCPA compliance, data minimization, user consent management",
    "Session Management: Secure session tokens, auto-logout after X minutes inactivity",
    "Input Validation: Sanitize all user inputs, parameterized queries, XSS protection",
    "Security Monitoring: Real-time threat detection, automated security scanning, penetration testing quarterly",
    "Compliance: SOC 2 Type II, ISO 27001, HIPAA (if healthcare data)",
    "... 10-15 comprehensive security requirements"
  ],
  "dependencies": [
    "External APIs: Auth0 for authentication (critical), Stripe for payments (critical)",
    "Third-party Services: SendGrid for email (high), Twilio for SMS (medium)",
    "Internal Systems: User Management API (critical), Analytics Pipeline (medium)",
    "Infrastructure: AWS services availability (critical), CDN provider (high)",
    "Data Sources: External data feed X (medium), Partner API Y (low)",
    "... 8-12 dependencies with criticality levels"
  ]
}}

CRITICAL REQUIREMENTS:
- Make this IMPLEMENTATION-READY: Engineering teams should be able to start coding from this
- Be TECHNICALLY DETAILED: Include specific technologies, versions, patterns, architectures
- Think USER-FIRST: Every feature should tie back to user value
- Be COMPREHENSIVE: Cover all aspects needed for production deployment
- Include MEASURABLE criteria: Specific numbers for performance, scale, quality
- document_id: "PRD-" followed by 6 digits
- story_id: "US-" followed by 3 digits
- feature_id: "FEAT-" followed by 3 digits
- requirement_id: "TR-" followed by 3 digits
- priority: "high", "medium", or "low"
- story_points: 1, 2, 3, 5, 8, or 13
- category: "architecture", "integration", "data", or "infrastructure"
- Return ONLY valid JSON, no markdown, no explanations
"""