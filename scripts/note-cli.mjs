#!/usr/bin/env node
import fs from 'fs'; import path from 'path';
const AREAS = ['components','api','tests','database','utils','general'];
const args = Object.fromEntries(process.argv.slice(2)
  .map((v,i,a)=>v.startsWith('--')?[v.slice(2), a[i+1]]:null).filter(Boolean));
const cmd = process.argv[2];
function usage(){ console.log(`note-cli usage:
  add --area <${AREAS.join('|')}> --title "<title>" --content "<markdown>"
  promote --area <area> --title "<pattern-name>" --to examples/<area>/<FileName>.ts[x]
`); process.exit(1);}
if(!cmd) usage();
function appendNote(area, title, content){
  const file = `notes/${area}.md`; fs.mkdirSync('notes',{recursive:true});
  if(!fs.existsSync(file)) fs.writeFileSync(file, `# Notes — ${area}\n\n`);
  const entry = `\n---\n\n### ${title}\n**When to use:**\n**Key concepts:**\n**Why now:**\n\n${content}\n\n**Next Actions**\n- [ ] Convert to example stub when ready\n`;
  fs.appendFileSync(file, entry); console.log(`✓ Appended to ${file}`);
}
function promote(area, title, toPath){
  const out = toPath || `examples/${area}/${title.replace(/\s+/g,'')}.ts`;
  fs.mkdirSync(path.dirname(out), {recursive:true});
  const name = (title.replace(/\W+/g,'') || 'Example');
  const stub = `/**
 * PATTERN: ${title}
 * USE WHEN: (fill from notes)
 * KEY CONCEPTS: (fill from notes)
 * STATUS: STUB — promoted from notes, add real code when ready
 */
// Source: (if any public reference was used)
export const ${name} = () => null;
`;
  fs.writeFileSync(out, stub, 'utf8'); console.log(`✓ Promoted stub -> ${out}`);
}
switch(cmd){
  case 'add': { const {area,title,content}=args;
    if(!AREAS.includes(area)||!title||!content) usage(); appendNote(area,title,content); break; }
  case 'promote': { const {area,title}=args; const to=args.to;
    if(!AREAS.includes(area)||!title) usage(); promote(area,title,to); break; }
  default: usage();
}