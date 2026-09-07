import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const [rootArg,baseArg,toolsArg,output]=process.argv.slice(2);
const root=path.resolve(rootArg),req=createRequire(path.join(path.resolve(toolsArg),'package.json'));
const acorn=req('acorn'),postcss=req('postcss'),valueParser=req('postcss-value-parser');
const parse5=await import(pathToFileURL(req.resolve('parse5')).href);
const inventory={},edges=[],ignored=[];
function fail(s){throw Error(s)}
function crawl(dir){for(const n of fs.readdirSync(dir).sort()){const p=path.join(dir,n),s=fs.lstatSync(p);if(s.isSymbolicLink()||(!s.isFile()&&!s.isDirectory()))fail('VITE_LINK_OR_SPECIAL');if(s.isDirectory())crawl(p);else {if(s.nlink!==1)fail('VITE_HARDLINK');const b=fs.readFileSync(p);inventory[path.relative(root,p).split(path.sep).join('/') ]={size:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex')};}}}
if(fs.realpathSync(root)!==root)fail('VITE_ROOT_LINK');crawl(root);
if(!inventory['index.html']||!inventory['.vite/manifest.json'])fail('VITE_REQUIRED_ENTRY_OR_MANIFEST');
function external(s,{data=false}={}){
 // Browser URL parsing removes embedded ASCII controls; reject before classification.
 if(/[\x00-\x1f\x7f]/.test(s))fail('VITE_URL_CONTROL');
 const scheme=/^([a-z][a-z\d+.-]*):/i.exec(s)?.[1].toLowerCase();
 if(scheme==='data'&&data)return true;
 if(scheme&&!['http','https'].includes(scheme))fail('VITE_UNSUPPORTED_SCHEME '+scheme);
 if(scheme||s.startsWith('//')){
  if(/[\x00-\x20\x7f\\]/.test(s))fail('VITE_URL_CONTROL');
  if(scheme&&!/^https?:\/\//i.test(s))fail('VITE_UNSUPPORTED_SCHEME nonhierarchical');
  let url;try{url=new URL(s.startsWith('//')?'https:'+s:s);}catch{fail('VITE_UNSUPPORTED_SCHEME malformed URL')}
  if(!url.hostname)fail('VITE_UNSUPPORTED_SCHEME missing authority');
  return true;
 }
 return false;
}
const base=external(baseArg)?new URL(baseArg.startsWith('//')?'https:'+baseArg:baseArg).pathname:baseArg;
if(!base.startsWith('/')&&base!==''&&base!=='./')fail('VITE_UNSUPPORTED_BASE');
function ref(from,raw,kind,rootRelative=false){
 if(typeof raw!=='string'||!raw.trim())fail('VITE_EMPTY_REFERENCE');raw=raw.trim();
 if(external(baseArg)&&raw.startsWith(baseArg)){raw=raw.slice(baseArg.length);rootRelative=true;}
 if(external(raw,{data:!kind.startsWith('manifest ')})||raw.startsWith('#')){ignored.push({from,raw,kind,reason:'external/data/fragment'});return;}
 let clean;try{clean=decodeURIComponent(raw.split(/[?#]/)[0]);}catch{fail('VITE_BAD_ENCODING')}
 if(clean.includes('\\')||clean.includes('\0'))fail('VITE_PATH_ESCAPE');
 let parts=[];
 if(clean.startsWith('/')) {if(base.startsWith('/')&&base!=='/'&&clean.startsWith(base.endsWith('/')?base:base+'/'))clean=clean.slice(base.length);else if(base.startsWith('/')&&base!=='/')fail('VITE_BASE_ESCAPE '+raw);clean=clean.replace(/^\/+/, '');}
 else if(!rootRelative)parts=path.posix.dirname(from).split('/').filter(x=>x!=='.');
 for(const p of clean.split('/')){if(!p||p==='.')continue;if(p==='..'){if(!parts.length)fail('VITE_PATH_ESCAPE '+raw);parts.pop();}else parts.push(p);}
 const target=parts.join('/');if(!inventory[target])fail('VITE_UNRESOLVED '+from+' -> '+raw+' ['+target+']');edges.push({from,raw,kind,target});return target;
}
function literal(n){return n?.type==='Literal'&&typeof n.value==='string'?n.value:n?.type==='TemplateLiteral'&&n.expressions.length===0?n.quasis[0].value.cooked:null;}
function js(text,from){
 const ast=acorn.parse(text,{ecmaVersion:'latest',sourceType:'module',allowHashBang:true});
 function walk(n){if(!n||typeof n!=='object')return;
  if(['ImportDeclaration','ExportNamedDeclaration','ExportAllDeclaration'].includes(n.type)&&n.source)ref(from,n.source.value,'js import');
  if(n.type==='ImportExpression'){let s=literal(n.source);if(s===null)fail('VITE_UNRESOLVED_DYNAMIC_IMPORT '+from);ref(from,s,'js dynamic import');}
  if(n.type==='NewExpression'&&n.callee.type==='Identifier'&&n.callee.name==='URL'){
   const b=n.arguments[1];const isMeta=b?.type==='MemberExpression'&&b.object?.type==='MetaProperty'&&b.object.meta.name==='import'&&b.object.property.name==='meta'&&b.property.name==='url';
   let s=literal(n.arguments[0]);
   if(s===null)fail('VITE_UNRESOLVED_NEW_URL '+from);
   if(external(s,{data:true}))ref(from,s,'js new URL');
   else if(isMeta)ref(from,s,'js new URL');
   else if(s.startsWith('/'))ref(from,s,'js absolute new URL');
   else if(literal(b)&&external(literal(b)))ignored.push({from,raw:s,kind:'js new URL',reason:'explicit external URL base'});
   else fail('VITE_UNRESOLVED_NEW_URL_BASE '+from);
  }
  for(const v of Object.values(n))if(Array.isArray(v))v.forEach(walk);else if(v&&typeof v==='object')walk(v);
 }walk(ast);
}
function css(text,from){
 const ast=postcss.parse(text,{from});
 function values(text){valueParser(text).walk(n=>{if(n.type==='function'&&n.value.toLowerCase()==='url'){const a=n.nodes.filter(x=>x.type!=='space'&&x.type!=='comment');if(a.length!==1||!['word','string'].includes(a[0].type))fail('VITE_UNSUPPORTED_CSS_URL');ref(from,a[0].value,'css url');return false;}});}
 ast.walkDecls(d=>values(d.value));ast.walkAtRules(a=>{if(a.name.toLowerCase()==='import'){const n=valueParser(a.params).nodes.find(n=>n.type!=='space'&&n.type!=='comment');if(n?.type==='string')ref(from,n.value,'css import');else if(n?.type!=='function'||n.value.toLowerCase()!=='url')fail('VITE_UNSUPPORTED_CSS_IMPORT');}values(a.params);});
}
function html(text,from){
 const doc=parse5.parse(text);function walk(n){
  const a=Object.fromEntries((n.attrs||[]).map(a=>[a.name,a.value])),tag=n.tagName;
  if(tag==='base')fail('VITE_HTML_BASE_ELEMENT_REQUIRES_EXPLICIT_RESOLUTION');
  if(tag==='script'){if(a.src)ref(from,a.src,'html script');else if(!a.type||['module','text/javascript','application/javascript'].includes(a.type))js((n.childNodes||[]).map(n=>n.value||'').join(''),from);}
  if(tag==='link'&&a.href&&['stylesheet','preload','modulepreload','icon','manifest'].some(r=>(a.rel||'').toLowerCase().split(/\s+/).includes(r)))ref(from,a.href,'html link');
  if(['img','source','video','audio','track','embed','input'].includes(tag)&&a.src)ref(from,a.src,'html asset');
  if(tag==='video'&&a.poster)ref(from,a.poster,'html poster');
  if(a.srcset)fail('VITE_SRCSET_REQUIRES_EXPLICIT_PARSER');
  if(a.style)css('x{'+a.style+'}',from);if(tag==='style')css((n.childNodes||[]).map(n=>n.value||'').join(''),from);
  // Anchor/form routes are navigation, never build artifacts.
  if(['a','form'].includes(tag))ignored.push({from,raw:a.href||a.action||'',reason:'application route'});
  (n.childNodes||[]).forEach(walk);if(n.content)walk(n.content);
 }walk(doc);
}
const manifest=JSON.parse(fs.readFileSync(path.join(root,'.vite/manifest.json'),'utf8'));
if(!Object.values(manifest).some(r=>r.isEntry))fail('VITE_MANIFEST_NO_ENTRY');
for(const [key,row] of Object.entries(manifest)){
 const from='.vite/manifest.json';if(typeof row.file!=='string')fail('VITE_MANIFEST_FILE');ref(from,row.file,'manifest file',true);
 for(const field of ['imports','dynamicImports'])for(const target of row[field]||[]){if(!manifest[target])fail('VITE_MANIFEST_MISSING_CHUNK '+target);edges.push({from:key,raw:target,kind:'manifest '+field,target:manifest[target].file});}
 for(const field of ['css','assets'])for(const target of row[field]||[])ref(from,target,'manifest '+field,true);
 // src/name are original source identifiers, not emitted asset references.
}
for(const name of Object.keys(inventory)){const text=()=>fs.readFileSync(path.join(root,name),'utf8');if(/\.html?$/.test(name))html(text(),name);else if(/\.(?:m?js|cjs)$/.test(name))js(text(),name);else if(name.endsWith('.css'))css(text(),name);}
const result={result:'PASS',root,base:baseArg,inventory,edges,ignored,parsers:['acorn','postcss','postcss-value-parser','parse5'],external_output_consumed_by_bootJar:false};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
