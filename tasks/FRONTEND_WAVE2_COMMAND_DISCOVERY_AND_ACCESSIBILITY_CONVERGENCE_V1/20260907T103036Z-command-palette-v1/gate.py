from pathlib import Path
import os,subprocess,json,time,sys
E=Path(__file__).resolve().parent;S=E/'snapshot';W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
name=sys.argv[1];args=sys.argv[2:];G=E/'gates';G.mkdir(exist_ok=True)
assert not (G/(name+'.json')).exists(), 'Use distinct attempt names; do not overwrite history'
base=['bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(E),str(E),'--ro-bind',str(S),str(S),'--ro-bind',str(W/'frontend/node_modules'),str(W/'frontend/node_modules'),'--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(S/'frontend'),'--']
if name.startswith('build-'):
 cache=E/'vite-temp';cache.mkdir(exist_ok=True)
 assert (W/'frontend/node_modules/.vite-temp').is_dir()
 base[-1:-1]=['--bind',str(cache),str(W/'frontend/node_modules/.vite-temp')]
env={**os.environ,'HOME':str(E),'GIT_OPTIONAL_LOCKS':'0','LANG':'C.UTF-8'}
start=time.time()
with (G/(name+'.log')).open('w') as out:
 p=subprocess.run(base+args,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=600)
row={'name':name,'command':args,'containment':base,'exit_code':p.returncode,'elapsed_seconds':time.time()-start}
(G/(name+'.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row));sys.exit(p.returncode)
