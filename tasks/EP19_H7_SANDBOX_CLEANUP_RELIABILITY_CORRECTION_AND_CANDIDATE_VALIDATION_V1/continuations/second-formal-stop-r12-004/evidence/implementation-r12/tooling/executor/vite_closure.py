from pathlib import Path
import json,subprocess
from execution import H
import durability
import causal

class ViteClosureFailure(RuntimeError):
 def __init__(self,label,error,**dimensions):
  super().__init__(label+' '+type(error).__name__+':'+str(error))
  self.failure_dimensions=dimensions
  self.causal_errors=causal.rows(error,'primary',label,'vite-closure-wrapper')

def validate(root,base,tool_root,output):
 argv=['node',str(H/'vite_closure.mjs'),str(root),base,str(tool_root),str(output)]
 try:
  with durability.exclusive_stream(Path(str(output)+'.native.log'),0o400) as log:
   try:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
   except (OSError,subprocess.SubprocessError) as error:
    raise ViteClosureFailure('VITE_CLOSURE_ENVIRONMENT_FAILURE',error,wrapper_or_environment_failure=True) from error
   if r.returncode:
    error=RuntimeError('exit='+str(r.returncode))
    raise ViteClosureFailure('VITE_CLOSURE_REJECT_HELPER_PROCESS_FAILURE',error,parser_helper_process_failure=True) from error
 except ViteClosureFailure:raise
 except OSError as error:
  raise ViteClosureFailure('VITE_CLOSURE_LOG_PERSISTENCE_FAILURE',error,evidence_persistence_failure=True) from error
 try:
  durability.sync_existing_file(output)
  return json.loads(Path(output).read_text())
 except OSError as error:
  raise ViteClosureFailure('VITE_CLOSURE_OUTPUT_PERSISTENCE_FAILURE',error,evidence_persistence_failure=True) from error
 except (UnicodeError,json.JSONDecodeError,ValueError,KeyError,TypeError) as error:
  raise ViteClosureFailure('VITE_CLOSURE_ASSERTION_FAILURE',error,product_assertion_failure=True) from error
