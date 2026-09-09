from pathlib import Path
import subprocess,json,datetime,sys,hashlib
R=Path(__file__).resolve().parent
cmd=['bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(R),str(R),'--bind','/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/browser-v10-final02/vite-temp','/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules/.vite-temp','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(R),'--','/usr/bin/node',str(R/'build.mjs')]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (R/'build.log').open('w') as f: p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
(R/'BUILD_FINAL03_COMMAND.json').write_text(json.dumps({'argv':cmd,'start':start,'end':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':p.returncode},indent=2))
sys.exit(p.returncode)
