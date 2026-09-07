from pathlib import Path
import subprocess,os,json,time,sys,shutil
R=Path(__file__).resolve().parents[1];S=R/'snapshot';P=Path('[LOCAL_FRONTEND_WORKTREE]')
name=sys.argv[1];args=sys.argv[2:];assert not (R/'gates'/f'{name}.json').exists()
for f in ['WorkspaceCanvas.tsx','WorkspaceCanvas.test.tsx']:shutil.copyfile(P/'frontend/src/product/canvas'/f,S/'frontend/src/product/canvas'/f)
base=['bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(R),str(R),'--ro-bind',str(S),str(S),'--bind',str(S/'frontend/node_modules'),str(S/'frontend/node_modules'),'--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(S/'frontend'),'--']
cmd=base+args;env={'PATH':os.environ['PATH'],'HOME':str(R),'LANG':'C.UTF-8','GIT_OPTIONAL_LOCKS':'0'}
(R/'gates'/f'{name}.plan.json').write_text(json.dumps({'command':cmd,'expected_exit':1 if name=='red' else 0,'source_mount':'read-only','output_root':str(R)},indent=2));t=time.time()
with (R/'gates'/f'{name}.log').open('w') as out:p=subprocess.run(cmd,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=500)
result={'name':name,'command':args,'exit':p.returncode,'seconds':time.time()-t};(R/'gates'/f'{name}.json').write_text(json.dumps(result,indent=2));print(result)
