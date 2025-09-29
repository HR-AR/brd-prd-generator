#!/usr/bin/env node
import fs from 'fs';
const initPath = 'INITIAL.md';
if (!fs.existsSync(initPath)) {
  console.error('INITIAL.md not found. Create it first.');
  process.exit(2);
}
const init = fs.readFileSync(initPath,'utf8');
const tmpl = fs.readFileSync('docs/prps/prp_template.md','utf8');
const title = (init.match(/^#\s*Request\s*\n([\s\S]*?)\n/m)?.[1]||'New Feature').trim();
const today = new Date().toISOString().slice(0,10);
const slug = s=>s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'');
const out = `docs/prps/PRP-${slug(title)}-${today}.md`;
fs.mkdirSync('docs/prps',{recursive:true});
fs.writeFileSync(out, tmpl.replace('[Feature Name]', title).replace('[Date]', today));
console.log(`✓ Created ${out}`);