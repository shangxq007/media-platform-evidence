from pathlib import Path
import os,subprocess,json,time,sys,datetime
C=Path(__file__).resolve().parent;E=C/sys.argv[1];S=E/'snapshot';W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
name=sys.argv[2];args=sys.argv[3:];G=E/'gates';G.mkdir(exist_ok=True)
assert not (G/(name+'.json')).exists() and not (G/(name+'.log')).exists(),'Distinct run required'
base=['bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(E),str(E),'--ro-bind',str(S),str(S),'--ro-bind',str(W/'frontend/node_modules'),str(W/'frontend/node_modules'),'--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(S/'frontend'),'--']
if name.startswith('build-'):
 cache=E/'vite-temp';cache.mkdir(exist_ok=True)
 base[-1:-1]=['--bind',str(cache),str(W/'frontend/node_modules/.vite-temp')]
env={**os.environ,'HOME':str(E),'GIT_OPTIONAL_LOCKS':'0','LANG':'C.UTF-8'}
start=time.time();row={'name':name,'implementation_tree':(E/'FINAL_TREE.txt').read_text().strip(),'command':args,'containment':base,'cwd':str(S/'frontend'),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (G/(name+'.log')).open('x') as out:
 p=subprocess.Popen(base+args,env=env,stdout=out,stderr=subprocess.STDOUT)
 row['pid']=p.pid
 (G/(name+'.started.json')).write_text(json.dumps(row,indent=2)+'\n')
 code=p.wait(timeout=600)
row.update(exit_code=code,elapsed_seconds=time.time()-start,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(G/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row));sys.exit(code)
