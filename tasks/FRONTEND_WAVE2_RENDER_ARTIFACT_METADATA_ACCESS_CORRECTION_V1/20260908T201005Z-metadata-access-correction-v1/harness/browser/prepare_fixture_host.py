"""Preparation only when explicitly invoked. Never runs a build or gate."""
from pathlib import Path
import json, hashlib, re
P=Path(__file__).resolve().parent
V=P.parent/'final-validation-01'
S=V/'snapshot/frontend'
H=P/'fixture-host'
assert S.is_dir(),f'Parent must materialize exact final snapshot: {S}'
tree=(V/'FINAL_TREE.txt').read_text().strip()
assert re.fullmatch(r'[0-9a-f]{40}',tree),'FINAL_TREE.txt must hold exact implementation tree'
assert (S/'node_modules').is_dir(),'Parent must provision snapshot dependencies read-only'
H.mkdir(exist_ok=False)
(H/'node_modules').symlink_to(S/'node_modules',target_is_directory=True)
(H/'entry.tsx').write_text((P/'entry.template.tsx').read_text().replace('SOURCE',str(S/'src')))
html=(S/'index.html').read_text()
assert html.count('/src/main.tsx')==1,'Unexpected ordinary entry, fail closed'
(H/'index.html').write_text(html.replace('/src/main.tsx',str(S/'src/main.tsx')))
(H/'fixture.html').write_text(html.replace('/src/main.tsx','/entry.tsx'))
config="""import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
export default defineConfig({root:HOST,plugins:[react()],publicDir:false,resolve:{alias:{'@':SOURCE}},build:{outDir:BUILD,emptyOutDir:false,sourcemap:false,rollupOptions:{input:{ordinary:INDEX,fixture:FIXTURE}}}})
"""
for key,value in [('HOST',str(H)),('SOURCE',str(S/'src')),('BUILD',str(P/'build')),('INDEX',str(H/'index.html')),('FIXTURE',str(H/'fixture.html'))]:config=config.replace(key,json.dumps(value))
(H/'vite.config.mjs').write_text(config)
files=[]
for f in sorted((S/'src').rglob('*')):
 if f.is_file():files.append({'path':str(f.relative_to(S)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(P/'FIXTURE_HOST_INPUTS.json').write_text(json.dumps({'FINAL_EXACT_IMPLEMENTATION_TREE':tree,'snapshot':str(S),'entry':str(H/'entry.tsx'),'ordinary_entry':str(S/'src/main.tsx'),'files':files,'scope':'External opt-in provider around exact registered routeTree. No product modifications. Build output external. No backend integration.'},indent=2))
catalog=(S/'src/localization/catalogs.ts').read_text()
labels={'en':{},'zh-CN':{}}
for key in ['refresh','retry','inspectNamed','detailClose','loadingTitle','cancel','cancelledTitle','artifactDenied','artifactUnknown','artifactStale','artifactUnavailable','artifactsTitle','failureDeniedTitle','failureUnknownTitle']:
 matches=re.findall(r"'renders\."+key+r"': message\('([^']*)'",catalog)
 assert len(matches)==2,(key,matches)
 for locale,value in zip(labels,matches):labels[locale][key]=value
(P/'browser/LABELS.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2))
print(json.dumps({'host':str(H),'build_command':['node',str(S/'node_modules/vite/bin/vite.js'),'build','--config',str(H/'vite.config.mjs'),'--configLoader','runner'],'build_output':str(P/'build')},indent=2))
