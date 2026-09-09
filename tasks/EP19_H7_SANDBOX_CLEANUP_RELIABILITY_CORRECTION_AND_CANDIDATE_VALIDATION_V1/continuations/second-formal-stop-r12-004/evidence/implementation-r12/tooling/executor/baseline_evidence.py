"""Receipt of the actual baseline predicate inputs; never resample a failed comparison."""
import json,os,sys,time
from pathlib import Path
import bookkeeping_v2 as bk
import decision_evidence as de
import causal
from preservation import FIELDS

class Evidence:
    def __init__(self,run,attempt):
        self.run=run;self.scope=None;self.before={};self.policy=None
        self.r={'schema':'ep19-baseline-capture-evidence-v1','run_id':run.name,'run':str(run),
                'attempt':attempt,'started_ns':time.time_ns(),'ordering':[],
                'policy_identity':None,'policy_target':None,'collector_target':None,
                'capture_errors':[],'observer_errors':[],'observer_rejections':[],
                'exception':None,'evaluation':None,'decision':'REJECT',
                'process_status':'BASELINE_ONLY_NO_PREFLIGHT_OR_GATES_INVOKED',
                'limits':['SEQUENTIAL_ENDPOINTS_NOT_ATOMIC','NO_WRITER_ATTRIBUTION',
                          'NO_LATER_RESAMPLING_AS_COMPARISON_EVIDENCE','NO_EXTERNAL_PROCESS_NONWRITING_PROOF']}
    def mark(self,phase):self.r['ordering'].append({'phase':phase,'time_ns':time.time_ns(),'monotonic_ns':time.monotonic_ns()})
    def bind_summary(self):
        policy=self.policy or {};target=policy.get('target');a={'sha256':policy.get('baseline_raw_sha256'),'metadata':policy.get('baseline_usage_metadata')}
        b=self.before.get(target,{})
        self.r['target_path']=target;self.r['policy_target']=a if target else None
        self.r['collector_target']={k:b.get(k) for k in ('sha256','metadata','kind')} if target in self.before else None
        ma=a.get('metadata') or {};mb=b.get('metadata') or {}
        self.r['binding']={'target_present':target in self.before,'hash_equal':bool(target in self.before and a['sha256']==b.get('sha256')),
                           'metadata_equal':bool(target in self.before and a['metadata']==b.get('metadata')),
                           'metadata_differences':{k:{'policy':ma.get(k),'collector':mb.get(k)} for k in FIELDS if ma.get(k)!=mb.get(k)}}
    def save(self,decision,exception=None):
        self.bind_summary();self.r.update(decision=decision,finished_ns=time.time_ns(),exception=de.error(exception) if exception else None)
        self.mark('EVIDENCE_WRITE')
        private={**self.r,'privacy':'PRIVATE_NOT_FOR_PUBLIC_PACKAGE','before':self.before}
        public={**self.r,'privacy':'SANITIZED_TARGET_SUBSET','omission':{'full_before_map':'PRIVATE_ONLY','omitted_rows':len(self.before)-int(self.r['binding']['target_present']),
                 'bodies_and_record_ids':'OMITTED','error_details':'PRIVATE_ONLY','evaluation_details':'PRIVATE_ONLY'}}
        def clean_error(e):return {'type':e.get('type'),'errno':e.get('errno'),'reason_code':str(e.get('reason','')).split(' ',1)[0]}
        public['exception']=clean_error(self.r['exception']) if self.r['exception'] else None
        for k in ('capture_errors','observer_errors'):
            public[k]=[clean_error(e) if isinstance(e,dict) else {'reason_code':str(e).split(' ',1)[0]} for e in self.r[k]][:32]
            public['omission'][k+'_omitted']=max(0,len(self.r[k])-32)
        public['observer_rejections']=[{'category':e.get('category')} for e in self.r['observer_rejections'][:32]]
        public['omission']['observer_rejections_omitted']=max(0,len(self.r['observer_rejections'])-32)
        if self.r['evaluation'] is not None:
            public['evaluation']={k:v for k,v in self.r['evaluation'].items() if k in ('OLD_STRICT_PRESERVATION_RESULT','V2_INPUT_INTEGRITY_RESULT','V2_BOOKKEEPING_EVALUATION','baseline_raw_sha256','current_raw_sha256','current_usage_metadata','exception')}
            public['evaluation']['reason_codes']=[str(x).split(' ',1)[0] for x in self.r['evaluation'].get('reasons',[])]
            if public['evaluation'].get('exception'):public['evaluation']['exception']=clean_error(public['evaluation']['exception'])
        # Early failures still use only the declared runtime destination, with known inputs excluded.
        scope=self.scope or {'allowed':[str(self.run/'runtime')],'protected':[str(self.run/'BASELINE_ATTEMPT.json')]}
        try:
            de.write_receipt(self.run,scope,self.before,(),private)
            return de.write_receipt(self.run,scope,self.before,(),public)
        except Exception as exc:
            fallback={**public,'decision':'REJECT','evidence_write_error':clean_error(de.error(exc))}
            failure=RuntimeError('BASELINE_EVIDENCE_WRITE_FAILED')
            failure.causal_errors=causal.receipt_rows(
                exc,'evidence-persistence','BASELINE_EVIDENCE_PERSISTENCE')
            try:
                print('BASELINE_EVIDENCE_WRITE_FAILED '+json.dumps(fallback,sort_keys=True),
                      file=sys.stderr,flush=True)
                try:os.fsync(sys.stderr.fileno())
                except (OSError,AttributeError):pass
            except BaseException as diagnostic:
                failure.causal_errors=causal.unique(failure.causal_errors+causal.rows(
                    diagnostic,'diagnostic-stderr-emission','DIAGNOSTIC_STDERR_EMISSION',
                    'secondary-for-baseline-evidence-failure'))
                failure.diagnostic_stderr_delivered=False
                failure.diagnostic_stderr_persistence_claim=False
            raise failure from exc
