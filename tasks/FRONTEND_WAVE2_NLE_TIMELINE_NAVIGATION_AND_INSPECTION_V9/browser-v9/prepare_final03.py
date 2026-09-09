from pathlib import Path
import json,hashlib,shutil,ast
R=Path(__file__).resolve().parent
T='37d003fc4f55faf166cd836a6ea93d77eb8b6a1e'
assert (R.parent/'validation-03/FINAL_TREE.txt').read_text().strip()==T
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):
 return {'root':str(root),'files':[{'path':str(p.relative_to(root)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and 'node_modules' not in p.parts and not p.is_symlink()]}
# Capture pre-existing external artifacts and final authoritative input bytes.
baseline={'tree':T,'source':manifest(R.parent/'validation-03/snapshot'),'ordinary-build':manifest(R.parent/'validation-03/build'),'prior-browser':manifest(R)}
(R/'FINAL03_BEFORE_MANIFEST.json').write_text(json.dumps(baseline,indent=2))
H=R/'fixture-final03';H.mkdir()
for p in (R/'fixture-continuation-01').iterdir():
 if p.name=='node_modules':(H/p.name).symlink_to(p.resolve(),target_is_directory=True)
 elif p.is_file():(H/p.name).write_text(p.read_text().replace('validation-02','validation-03'))
D=R/'runner-final03';D.mkdir()
for name in ['chromium_helpers.py','browser_helpers.py','control.py','server.py']:
 (D/name).write_text((R/name).read_text().replace('a90af5baccf94a437b67e69fb1897328572a0209',T))
s=(R/'run_continuation_01.py').read_text().replace("R=Path(__file__).resolve().parent;", "R=Path(__file__).resolve().parent.parent;")
s=s.replace('build-continuation-01','build-final03').replace('validation-02','validation-03').replace("R/'server.py'","R/'runner-final03/server.py'")
(D/'run.py').write_text(s)
s=(R/'build-continuation-01.mjs').read_text().replace('validation-02','validation-03').replace('fixture-continuation-01','fixture-final03').replace('build-continuation-01','build-final03')
(R/'build-final03.mjs').write_text(s)
s=(R/'build_continuation_02.py').read_text().replace('build-continuation-01.mjs','build-final03.mjs').replace('build-continuation-02.log','build-final03.log').replace('BUILD_CONTINUATION_02_COMMAND.json','BUILD_FINAL03_COMMAND.json').replace('vite-temp','vite-temp-final03')
# The installed dependency temp mount TARGET remains the existing node_modules/.vite-temp.
s=s.replace('node_modules/.vite-temp-final03','node_modules/.vite-temp')
(R/'vite-temp-final03').mkdir()
(R/'build_final03.py').write_text(s)
s=(R/'continuation_tests_04.py').read_text()
addition='''
 check('selected locate explicit non-submit and no default submission','document.querySelectorAll(".ff-navigation-locate button")[1].type==="button" && __submitLog.length===0 && document.querySelector("output").textContent==="1001/30000"')
 typein('.ff-navigation-locate input','1001/30000');check('native Enter input focus before activation','document.activeElement.matches(".ff-navigation-locate input")');b.key('\\ue007')
 check('native Enter implicitly submits Locate time exactly once','__submitLog.length===1 && __submitLog[0].submitter==="Locate time" && __submitLog[0].type==="submit"')
 check('native Enter exact inclusive boundary selects first clip',selected('clip:clip-1')+' && document.querySelector("output").textContent==="1001/30000" && document.body.innerText.includes("Loaded clips at this position: 2")')
 (ROOT/'NATIVE_ENTER_DIAGNOSTIC.json').write_text(json.dumps(b.ev('({selected:__store.getSnapshot().primarySelectedObject?.id,position:document.querySelector("output").textContent,submits:__submitLog,focus:document.activeElement.outerHTML})'),indent=2));snap('native-enter-implicit-submit')
'''
s=s.replace('def keyboard():',addition+'def keyboard():')
(D/'final_tests.py').write_text(s)
def calls(text):
 return [ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='check']
old=calls((R/'continuation_tests_04.py').read_text());new=calls(s)
assert all(x in new for x in old)
assert 'validation-02' not in ''.join(p.read_text() for p in H.iterdir() if p.is_file())+(R/'build-final03.mjs').read_text()+(D/'run.py').read_text()
(R/'FINAL03_ASSERTION_PRESERVATION.json').write_text(json.dumps({'all_original_check_ASTs_preserved':True,'original_check_call_sites':len(old),'final_check_call_sites':len(new),'added_call_sites':len(new)-len(old),'original_sha256':sha(R/'continuation_tests_04.py'),'final_sha256':sha(D/'final_tests.py')},indent=2))
print('FINAL03 prepared; original assertions unchanged; new Enter assertions additive')
