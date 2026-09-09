from pathlib import Path
import subprocess,json,sys
T=Path(__file__).resolve().parent;V=T/'validation-01'
steps=[('targeted',['./node_modules/.bin/vitest','run','src/product/timeline','src/interaction','src/app/routeTree.test.tsx','src/api/app/timeline-query.gateway.test.ts','src/localization','--configLoader','runner','--no-cache','--reporter=json','--outputFile='+str(V/'TARGETED.json')]),('typecheck',['npm','run','typecheck']),('lint',['./node_modules/.bin/eslint','src/**/*.{ts,tsx}','--format','json','--output-file',str(V/'LINT.json')]),('architecture',['node','scripts/frontend-architecture-guard.mjs']),('architecture-controls',['node','scripts/frontend-architecture-guard.test.mjs']),('full',['./node_modules/.bin/vitest','run','--configLoader','runner','--no-cache','--reporter=json','--outputFile='+str(V/'FULL_UNIT.json')]),('build-final',['./node_modules/.bin/vite','build','--configLoader','bundle','--outDir',str(V/'build'),'--manifest','--emptyOutDir'])]
receipts=[]
for name,args in steps:
 p=subprocess.run([sys.executable,str(T/'gate.py'),'validation-01',name,*args]);r=json.loads((V/'gates'/f'{name}.json').read_text());receipts.append(r)
 (V/'REQUIRED_GATE_SUMMARY.json').write_text(json.dumps({'tree':(V/'FINAL_TREE.txt').read_text().strip(),'required':7,'invoked':len(receipts),'passed':sum(r['exit_code']==0 for r in receipts),'results':receipts},indent=2)+'\n')
 if p.returncode:raise SystemExit(p.returncode)
