#!/usr/bin/env node
import fs from 'fs'; import path from 'path';
const args = Object.fromEntries(process.argv.slice(2)
  .map((v,i,a)=>v.startsWith('--')?[v.slice(2), a[i+1]]:null).filter(Boolean));
const from = args.from || 'docs/prd/PRD.md';      // For new projects we scout from PRD
const stackFrom = args.stackFrom || 'CLAUDE.md';
const out = args.out;
const read = p => fs.existsSync(p) ? fs.readFileSync(p,'utf8') : '';
const text = read(from); if(!text){ console.error(`✖ Could not read: ${from}`); process.exit(2); }
const title = (text.match(/^#\s*(Idea|Request)\s*\n([\s\S]*?)\n/m)?.[2] || 'New Project').trim();
const stackMd = read(stackFrom);
const techStack = (stackMd.match(/##\s*Tech Stack[\s\S]*/)?.[0] || '[stack not found]').slice(0,1200);
const intent = `Project: ${title}\n\nContext (excerpt):\n` + text.slice(0,1200);
const prompt = `You are my Context Engineering scout.

Here is the project intent (from PRD):
---
${intent}
---

Our stack (from CLAUDE.md):
---
${techStack}
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
`;
const slug = title.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'') || 'project';
const outPath = out || `docs/prompts/SCOUT-from-PRD-${slug}.md`;
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, prompt);
console.log(`✓ Wrote scout prompt: ${outPath}`);
console.log('Next: open that file and paste its content into Gemini/Claude/ChatGPT.');