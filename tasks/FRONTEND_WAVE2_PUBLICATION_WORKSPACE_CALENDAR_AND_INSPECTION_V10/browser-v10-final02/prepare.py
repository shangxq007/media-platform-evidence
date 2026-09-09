from pathlib import Path
import json,hashlib,ast
R=Path(__file__).resolve().parent; B=R.parent; old=B/'browser-v10'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):return [{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink() and 'node_modules' not in p.parts]
def save(n,d):(R/n).write_text(json.dumps(d,indent=2))
assert (B/'validation-02/FINAL_TREE.txt').read_text().strip()=='afc966ad4872e6dd65997281c75fe49e7aaed376'
save('INPUT_BINDING.json',{'tree':'afc966ad4872e6dd65997281c75fe49e7aaed376','source':manifest(B/'validation-02/snapshot'),'ordinary':manifest(B/'validation-02/build'),'old_browser':manifest(old)})
for folder in ['runner','fixture','vite-temp']:(R/folder).mkdir(exist_ok=True)
for p in list((old/'runner').glob('*.py'))+list((old/'fixture').glob('*'))+[old/'build.mjs',old/'build_run.py']:
 if not p.is_file():continue
 dst=R/p.relative_to(old);text=p.read_text().replace('/browser-v10/','/browser-v10-final02/').replace('validation-01','validation-02').replace('ea4798924207d4004c92910815a42753e4ab9724','afc966ad4872e6dd65997281c75fe49e7aaed376');dst.write_text(text)
# External opt-in only: auth/Project context without Publication provider.
p=R/'fixture/entry.tsx';s=p.read_text().replace("new URLSearchParams(location.search).get('publicationFixture')!=='1'","!['1','project-only'].includes(new URLSearchParams(location.search).get('publicationFixture')||'')")
s=s.replace('return <PublicationSourceProvider source={s}>','if(new URLSearchParams(location.search).get("publicationFixture")==="project-only")return <><aside>ISOLATED PROJECT CONTEXT — explicit auth/Project fixture; PublicationSourceProvider absent; NOT real integration</aside><RouterProvider router={router}/></>;return <PublicationSourceProvider source={s}>');p.write_text(s)
p=R/'fixture/sdk.ts';s=p.read_text().replace("new URLSearchParams(location.search).get('publicationFixture')!=='1'","!['1','project-only'].includes(new URLSearchParams(location.search).get('publicationFixture')||'')");p.write_text(s)
p=R/'runner/server.py';p.write_text(p.read_text().replace("urllib.parse.parse_qs(u.query).get('publicationFixture')!=['1']","urllib.parse.parse_qs(u.query).get('publicationFixture') not in [['1'],['project-only']]"))
# Preserve original function bodies/assertions; combine supplements without duplicate network scenarios.
s=(R/'runner/tests.py').read_text().split('\ntry:\n')[0]
for name,funcs in [('supplemental.py',['bilingualCalendar','preserve','dismiss']),('restricted-corrected.py',['restrictedMetadata']),('overflow.py',['overflowCalendar'])]:
 text=(R/'runner'/name).read_text();tree=ast.parse(text)
 for node in tree.body:
  if isinstance(node,ast.FunctionDef) and node.name in funcs:s+='\n'+'\n'.join(text.splitlines()[node.lineno-1:node.end_lineno])+'\n'
(R/'runner/combined-base.py').write_text(s)
save('PREPARATION.json',{'instruction_conflict':'Root candidate commit freeze superseded by explicit no product or commit changes; immutable supplied actual tree used. No governance edits.','source':str(B/'validation-02/snapshot'),'react_dedupe':True,'old_results_not_reused':True})
print('PREPARED')
