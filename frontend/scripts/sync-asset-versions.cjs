// Run after frontend edits to keep each local module at one browser URL.
const fs=require('node:fs');
const path=require('node:path');
const version=process.argv[2]||'20261027.9';
if(!/^[\w.-]+$/.test(version))throw Error('Invalid asset version');
fs.writeFileSync('js/asset-version.json',JSON.stringify({version})+'\n');
const walk=dir=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?(e.name==='vendor'?[]:walk(path.join(dir,e.name))):[path.join(dir,e.name)]);
for(const file of walk('js').filter(f=>f.endsWith('.js'))){
  const source=fs.readFileSync(file,'utf8');
  const updated=source.replace(/(['"])(\.{1,2}\/[^'"?\s]+\.js)(?:\?v=[^'"]+)?\1/g,(_,quote,url)=>`${quote}${url}?v=${version}${quote}`);
  if(updated!==source)fs.writeFileSync(file,updated);
}
for(const file of fs.readdirSync('.').filter(f=>f.endsWith('.html'))){
  const source=fs.readFileSync(file,'utf8');
  const updated=source.replace(/((?:src|href)="\/(?:js|css)\/[^"?]+\.(?:js|css))(?:\?v=[^"]+)?"/g,`$1?v=${version}"`);
  if(updated!==source)fs.writeFileSync(file,updated);
}
