"""Parent preparation only: endpoint probes, executor identity, then supplied disposition."""
from pathlib import Path
import argparse,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'executor'))
import coverage,runner,sequence
from hermes_execute_once import endpoint_checks,RUN_ID

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['endpoints','identity','disposition']);ap.add_argument('--input',type=Path);a=ap.parse_args()
    run=runner.runpath(RUN_ID)
    if any((run/n).exists() for n in ('BASELINE_ATTEMPT.json','LAUNCHER_ATTEMPT.json','baseline.json')):raise RuntimeError('PREPARATION_AFTER_WINDOW_FORBIDDEN')
    if a.phase=='endpoints':
        started=time.time_ns();checks=endpoint_checks()
        result={'result':'PASS','run_id':RUN_ID,'started_ns':started,'finished_ns':time.time_ns(),'checks':checks,
                'scope':'PREPARATION_ENDPOINT_ONLY_NOT_FORMAL_WINDOW_NONWRITING_PROOF'}
        sequence.durable(run/'PREPARED_ENDPOINTS.json',result)
    elif a.phase=='identity':
        q=Path(json.loads((run/'prepare.json').read_text())['qualification']);coverage.qualification_inputs(q)
        basis=runner.executor_identity_basis(q)
        result={'identity_basis':basis,'identity':hashlib.sha256(json.dumps(basis,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
        sequence.durable(runner.EXECUTOR_IDENTITY,result);runner.verify_executor_identity()
    else:
        if a.input is None:ap.error('--input parent-authored disposition JSON is required')
        supplied=json.loads(a.input.read_text());runner.verify_executor_identity()
        required=[ROOT/'WRITER_BRIEF.md',ROOT/'CONTINUATION_AUTHORITY.md',runner.O/'qualification/CONTINUATION_PRESERVATION_CONTRACT.md',runner.O/'inputs/MONITOR_CONTRACT.txt']
        paths=supplied.get('preloaded_instruction_paths',[])
        if not set(map(str,required))<=set(paths):raise RuntimeError('REQUIRED_PRELOADED_INSTRUCTION_PATHS_MISSING')
        result={**supplied,'schema':sequence.SCHEMA,'run_id':RUN_ID,'prepared_ns':time.time_ns(),
                'basis':sequence.basis(run),'instruction_inputs':coverage.seal(paths),
                'instruction_inventory':sequence.instruction_inventory(),
                'parent_input':str(a.input.absolute()),'parent_input_sha256':coverage.digest(a.input)}
        sequence.durable(run/'PREPARATION_DISPOSITION.json',result);sequence.verify(run)
    print(json.dumps({'phase':a.phase,'result':'PASS','run_id':RUN_ID}),flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
