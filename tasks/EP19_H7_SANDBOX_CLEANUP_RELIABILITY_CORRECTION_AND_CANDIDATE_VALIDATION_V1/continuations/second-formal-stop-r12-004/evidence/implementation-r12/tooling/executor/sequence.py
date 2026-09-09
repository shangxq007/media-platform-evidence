"""Prepared instruction boundary and durable one-shot claims; no tool invocation."""
import json,os,time,uuid
from pathlib import Path
import coverage
from execution import D
from preservation import Collector,INSTRUCTIONS,parent_fd
import durability

SCHEMA='ep19-preloaded-preparation-disposition-v1'
PREPARATION=('prepare.json','bindings.json','lean-materialization.json','preparation-collector.json',
             'PREPARATION_COMPATIBILITY.json','PREPARATION_REVALIDATION.json','PREPARED_ENDPOINTS.json')

def durable(path,value,mode=0o400):
    payload=(json.dumps(value,indent=2,ensure_ascii=True)+'\n').encode()
    durability.exclusive_bytes(path,payload,mode)

def consume(run,kind,launcher_attempt=None):
    launch=run/'LAUNCHER_ATTEMPT.json'
    if kind=='baseline' and launch.exists():
        if not launcher_attempt or json.loads(launch.read_text()).get('attempt_id')!=launcher_attempt:
            raise RuntimeError('ONE_SHOT_NAMESPACE_ALREADY_CONSUMED')
    if any((run/p).exists() for p in ('baseline.json','seal.json','runtime/START.json')):
        raise RuntimeError('ONE_SHOT_NAMESPACE_ALREADY_CONSUMED')
    value={'schema':'ep19-one-shot-attempt-v1','attempt_id':uuid.uuid4().hex,'run_id':run.name,
           'run':str(run),'kind':kind,'pid':os.getpid(),'consumed_ns':time.time_ns(),
           'retry_authorized':False,'state':'CONSUMED_BEFORE_BASELINE'}
    try:durable(run/('BASELINE_ATTEMPT.json' if kind=='baseline' else 'LAUNCHER_ATTEMPT.json'),value)
    except FileExistsError as exc:raise RuntimeError('ONE_SHOT_NAMESPACE_ALREADY_CONSUMED') from exc
    return value

def instruction_inventory():
    r=Collector(roots=INSTRUCTIONS,expected_nonempty=INSTRUCTIONS).capture()
    if r['result']!='COMPLETE':raise RuntimeError('PRELOADED_INSTRUCTION_CAPTURE_INCOMPLETE')
    # Runtime bookkeeping remains subject to the unchanged V2 predicates.
    return {p:row['sha256'] for p,row in r['entries'].items() if 'sha256' in row
            and Path(p).name not in ('.usage.json','.usage.json.lock','.curator_ledger.jsonl')
            and not __import__('bookkeeping_v2').is_reserved_temp(p)}

def basis(run):
    config=json.loads((run/'prepare.json').read_text())
    paths=[run/n for n in PREPARATION]
    paths += [D.parent/'evidence/EXECUTOR_IDENTITY.json',Path(config['qualification'])]
    paths += [p for folder in ('executor','tools','candidate-inputs-v3','qualification') for p in (D/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += __import__('binding_contract').closure()
    return coverage.seal(paths)

def verify(run):
    disposition=json.loads((run/'PREPARATION_DISPOSITION.json').read_text())
    if (disposition.get('schema')!=SCHEMA or disposition.get('run_id')!=run.name or disposition.get('result')!='READY'
        or any(disposition.get(k) is not True for k in ('instructions_preloaded','no_governance_during_window','no_unrelated_activity_during_window'))
        or disposition.get('pending_required_instructions')!=[] or disposition.get('new_required_instruction_action')!='STOP'
        or disposition.get('external_process_nonwriting')!='NOT_ESTABLISHED'):
        raise RuntimeError('PREPARATION_DISPOSITION_REJECT')
    if disposition.get('basis')!=basis(run):raise RuntimeError('PREPARATION_DISPOSITION_INPUT_CHANGED')
    if not disposition.get('instruction_inputs'):raise RuntimeError('PRELOADED_INSTRUCTIONS_MISSING')
    coverage.check_seal(disposition['instruction_inputs'])
    if disposition.get('instruction_inventory')!=instruction_inventory():raise RuntimeError('NEW_OR_CHANGED_REQUIRED_INSTRUCTION_STOP')
    endpoints=json.loads((run/'PREPARED_ENDPOINTS.json').read_text())
    if endpoints.get('result')!='PASS' or endpoints.get('run_id')!=run.name or endpoints.get('checks',{}).get('result')!='PASS':
        raise RuntimeError('PREPARED_ENDPOINTS_REQUIRED')
    if not 0<endpoints.get('finished_ns',0)<disposition.get('prepared_ns',0)<=time.time_ns():
        raise RuntimeError('PREPARATION_ORDER_REJECT')
    return disposition,endpoints['checks']
