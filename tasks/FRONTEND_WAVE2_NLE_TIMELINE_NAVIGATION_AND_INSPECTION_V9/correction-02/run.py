from pathlib import Path
import os,subprocess,json,time,sys
E=Path(__file__).resolve().parent; W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
name=sys.argv[1]; args=sys.argv[2:]; log=E/(name+'.log'); receipt=E/(name+'.json')
assert not log.exists() and not receipt.exists()
base=['bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(E),str(E),'--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(W/'frontend'),'--']
start=time.time()
with log.open('x') as out:
 p=subprocess.run(base+args,stdout=out,stderr=subprocess.STDOUT,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},timeout=600)
receipt.write_text(json.dumps({'command':args,'containment':base,'exit_code':p.returncode,'elapsed':time.time()-start},indent=2)+'\n')
print(receipt.read_text()); print(log.read_text()[-6500:]);sys.exit(p.returncode)
