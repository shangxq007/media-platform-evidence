from pathlib import Path
import json,subprocess
from execution import H

def validate(root,base,tool_root,output):
 argv=['node',str(H/'vite_closure.mjs'),str(root),base,str(tool_root),str(output)]
 with Path(str(output)+'.native.log').open('xb') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError('VITE_CLOSURE_REJECT '+str(output)+'.native.log')
 return json.loads(Path(output).read_text())
