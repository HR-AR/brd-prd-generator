#!/usr/bin/env node
// Custom Skill Learning - Auto-generates official Agent Skills from patterns
// EXPERIMENTAL automation layer on official Anthropic Agent Skills
import fs from 'fs';
import crypto from 'crypto';

class SkillLearner {
  constructor() {
    this.patternsFile = '.claude/learning/patterns.json';
    this.skillsDir = '.claude/skills';
    this.threshold = 2;
  }

  loadPatterns() {
    if (!fs.existsSync(this.patternsFile)) return { patterns: [], skills: [] };
    return JSON.parse(fs.readFileSync(this.patternsFile, 'utf8'));
  }

  savePatterns(data) {
    fs.mkdirSync('.claude/learning', { recursive: true });
    fs.writeFileSync(this.patternsFile, JSON.stringify(data, null, 2));
  }

  extractIntent(request) {
    const keywords = {
      validation: ['validate', 'test', 'check', 'verify'],
      implementation: ['implement', 'build', 'create', 'code'],
      api_docs: ['api', 'documentation', 'docs', 'reference'],
      analysis: ['analyze', 'evaluate', 'assess', 'review'],
      debugging: ['debug', 'fix', 'error', 'issue']
    };

    const lower = request.toLowerCase();
    for (const [intent, terms] of Object.entries(keywords)) {
      if (terms.some(term => lower.includes(term))) return intent;
    }
    return 'general';
  }

  createSig(intent, context) {
    const hash = crypto.createHash('md5');
    hash.update(`${intent}:${context.slice(0, 100)}`);
    return hash.digest('hex').slice(0, 12);
  }

  record(userRequest, userInstructions = '') {
    const data = this.loadPatterns();
    const intent = this.extractIntent(userRequest);
    const sig = this.createSig(intent, userInstructions);

    let pattern = data.patterns.find(p => p.signature === sig);
    
    if (pattern) {
      pattern.count++;
      pattern.lastSeen = new Date().toISOString();
      pattern.examples.push({ request: userRequest, instructions: userInstructions });

      if (pattern.count === this.threshold && !pattern.skillCreated) {
        this.generateSkill(pattern);
        pattern.skillCreated = true;
        console.log(`\n🎯 Pattern detected ${this.threshold} times - skill generated!`);
      }
    } else {
      data.patterns.push({
        signature: sig,
        intent,
        count: 1,
        firstSeen: new Date().toISOString(),
        lastSeen: new Date().toISOString(),
        examples: [{ request: userRequest, instructions: userInstructions }],
        skillCreated: false
      });
    }

    this.savePatterns(data);
    const count = data.patterns.find(p => p.signature === sig)?.count || 1;
    console.log(`✅ Pattern tracked: ${intent} (${count}/${this.threshold})`);
    if (count === 1) console.log('💡 One more will auto-generate skill');
  }

  generateSkill(pattern) {
    const { intent, examples, signature } = pattern;
    
    const gerundMap = {
      validation: 'Running Validations',
      implementation: 'Implementing Features',
      api_docs: 'Looking Up API Documentation',
      analysis: 'Analyzing Code',
      debugging: 'Debugging Issues'
    };
    const skillName = gerundMap[intent] || `Processing ${intent}`;
    const skillDir = `${this.skillsDir}/auto-${intent}-${signature}`;
    
    fs.mkdirSync(skillDir, { recursive: true });

    const needsWeb = /api|docs|documentation|latest|current/.test(
      examples.map(e => e.request + e.instructions).join(' ').toLowerCase()
    );

    const triggers = this.extractTriggers(examples);
    const instructions = this.synthInstructions(examples);

    const skillContent = `---
name: ${skillName}
description: Auto-generated ${intent} skill. ${needsWeb ? 'Always searches web for current info. ' : ''}Triggers: ${triggers.join(', ')}.
---

# ${skillName} (Auto-Generated)

⚡ **Created from detected usage pattern**

## When to Use
${triggers.map(t => `- "${t}"`).join('\n')}

## Your Methodology
${instructions}

${needsWeb ? \`## Web Search Enabled
ALWAYS searches for current info via web_search + web_fetch\` : ''}

## Examples
${examples.slice(0, 2).map(e => `- "${e.request}"`).join('\n')}

## Validation
\\`\\`\\`bash
npm run validate
\\`\\`\\`

---
**Generated:** ${new Date().toISOString()}
**From:** ${pattern.count} similar requests
`;

    fs.writeFileSync(`${skillDir}/SKILL.md`, skillContent);
    
    console.log(`\n✅ Skill: ${skillDir}/SKILL.md`);
    console.log(`   Name: ${skillName}`);
    if (needsWeb) console.log('   🌐 Web search enabled');

    data.skills.push({
      name: skillName,
      intent,
      created: new Date().toISOString(),
      fromPattern: signature
    });
    this.savePatterns(data);
  }

  extractTriggers(examples) {
    const triggers = new Set();
    examples.forEach(ex => {
      const words = ex.request.toLowerCase().split(/\s+/);
      ['analyze', 'test', 'build', 'api', 'docs', 'implement'].forEach(key => {
        const idx = words.indexOf(key);
        if (idx >= 0) {
          triggers.add(words.slice(idx, idx + 3).join(' '));
        }
      });
    });
    return Array.from(triggers).slice(0, 3);
  }

  synthInstructions(examples) {
    const detailed = examples
      .map(e => e.instructions)
      .filter(i => i.length > 20)
      .sort((a, b) => b.length - a.length)[0];

    if (!detailed) return '1. Analyze request\n2. Apply methodology\n3. Deliver results';

    const lines = detailed.split('\n').filter(l => l.trim());
    return lines.slice(0, 8).map((l, i) => {
      return l.match(/^\d/) ? l : `${i + 1}. ${l}`;
    }).join('\n');
  }

  list() {
    const data = this.loadPatterns();
    console.log('\n' + '='.repeat(70));
    console.log('📚 AUTO-GENERATED SKILLS');
    console.log('='.repeat(70));
    data.skills.forEach(s => {
      console.log(`  ✅ ${s.name} (${s.intent})`);
    });
    console.log('\n' + '='.repeat(70));
    console.log('📊 TRACKING PATTERNS');
    console.log('='.repeat(70));
    data.patterns.filter(p => !p.skillCreated).forEach(p => {
      console.log(`  🔍 ${p.intent}: ${p.count}/${this.threshold}`);
      if (p.count === this.threshold - 1) console.log('     ⚡ One more will generate!');
    });
    console.log('='.repeat(70));
  }
}

const learner = new SkillLearner();
const cmd = process.argv[2];

if (cmd === 'record' && process.argv[3]) {
  learner.record(process.argv[3], process.argv[4] || '');
} else if (cmd === 'list') {
  learner.list();
} else if (cmd === 'track') {
  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  console.log('\n🎓 Skill Learning Mode\n');
  readline.question('What did you ask for? ', (req) => {
    readline.question('How did you explain to do it? ', (instr) => {
      learner.record(req, instr);
      console.log('\n✅ Pattern recorded!');
      readline.close();
    });
  });
} else {
  console.log(\`Skill Learner (Experimental)

Commands:
  track                    Interactive pattern tracking
  record "req" "method"    Track programmatically  
  list                     Show learned skills

Usage:
  npm run learn:track
  npm run learn:record "implement auth" "use JWT, test with Jest"
  npm run learn:list
\`);
}
