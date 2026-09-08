"""Integration controls for observer, decision receipts and launch reachability."""
from pathlib import Path
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch

import bookkeeping_v2
import coverage
import decision_evidence
import execution
import observe
import preservation
import runner


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def record():
    return {"created_by": None, "use_count": 1, "view_count": 1,
            "last_used_at": "2026-09-07T00:00:00+00:00", "last_viewed_at": None,
            "patch_count": 0, "patch_generation": 0, "last_reused_patch_generation": 0,
            "last_patched_at": None, "created_at": "2026-09-01T00:00:00+00:00",
            "state": "active", "pinned": False, "archived_at": None}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skills = self.base / "skills"; self.skills.mkdir(mode=0o700)
        skill = self.skills / "alpha"; skill.mkdir(); self.instruction = skill / "SKILL.md"
        self.instruction.write_text("strict instruction\n")
        self.memory = self.base / "memory.md"; self.memory.write_text("strict memory\n")
        self.usage = self.skills / ".usage.json"; self.lock = self.skills / ".usage.json.lock"
        self.lock.touch(mode=0o644); self.write_usage(record()); os.chmod(self.usage, 0o600)
        self.policy = bookkeeping_v2.create_policy(
            self.usage, owner_sha256="1"*64, dependency_sha256="2"*64,
            selection_binding={"matrix_sha256":"3"*64,"gate_count":29})

    def write_usage(self, rec):
        self.usage.write_text(json.dumps({"alpha":rec}, sort_keys=True, indent=2)+"\n")

    def replace_usage(self, rec):
        temp = self.skills / ".usage_abc12_3z.tmp"
        temp.write_text(json.dumps({"alpha":rec}, sort_keys=True, indent=2)+"\n")
        os.chmod(temp, 0o600); os.replace(temp, self.usage)


class ObserverControls(Fixture):
    def observed(self, script):
        return observe.run([sys.executable,"-B","-c",script], self.base, self.base/("log-"+str(len(list(self.base.glob('log-*'))))),
                           [self.skills,self.usage,self.lock,self.instruction,self.memory], [], [], [],
                           enumeration_roots=[self.skills], bookkeeping_policy=self.policy, timeout=5)

    def test_real_atomic_write_event_and_metadata_variation_pass(self):
        code=("import json,os;from pathlib import Path;r=Path(%r);p=r/'.usage.json';t=r/'.usage_abc12_3z.tmp';"
              "d=json.loads(p.read_text());d['alpha']['view_count']+=1;t.write_text(json.dumps(d,sort_keys=True,indent=2)+'\\n');"
              "os.chmod(t,0o600);os.replace(t,p)" % str(self.skills))
        result=self.observed(code)
        self.assertEqual(result["wrapper_exit"],0,result)
        self.assertEqual(result["bookkeeping_evaluation"]["OLD_STRICT_PRESERVATION_RESULT"],"OLD_STRICT_REJECT")
        self.assertEqual(result["bookkeeping_evaluation"]["V2_INPUT_INTEGRITY_RESULT"],"PASS")
        self.assertTrue(any(e["category"]=="SCOPED_BOOKKEEPING_EVENT_PENDING_FINAL_EVALUATION" for e in result["events"]))

    def test_strict_instruction_change_prevents_acceptance_despite_rc0(self):
        result=self.observed("from pathlib import Path;Path(%r).write_text('changed')" % str(self.instruction))
        self.assertEqual(result["wrapper_exit"],1)
        self.assertTrue(any(e["category"]=="REJECT_INSTRUCTION_EVENT" for e in result["events"]))

    def test_memory_change_prevents_acceptance_despite_rc0(self):
        result=self.observed("from pathlib import Path;Path(%r).write_text('changed')" % str(self.memory))
        self.assertEqual(result["wrapper_exit"],1)

    def test_temp_name_cannot_authorize_other_skill_write(self):
        code="from pathlib import Path;p=Path(%r);p.write_text('x');p.unlink();Path(%r).write_text('changed')" % (str(self.skills/'.usage_abc12_3z.tmp'),str(self.instruction))
        result=self.observed(code)
        self.assertEqual(result["wrapper_exit"],1)
        self.assertTrue(any(e["category"].startswith("REJECT") for e in result["events"]))

    def test_target_attribute_event_rejects_even_if_mode_restored(self):
        code="import os;from pathlib import Path;p=Path(%r);os.chmod(p,0o644);os.chmod(p,0o600)" % str(self.usage)
        result=self.observed(code)
        self.assertEqual(result["wrapper_exit"],1)
        self.assertTrue(any(e["category"]=="REJECT_BOOKKEEPING_TARGET_ATTRIBUTE_EVENT" for e in result["events"]))

    def test_reserved_temp_cross_boundary_move_rejects(self):
        outside=self.base/"outside.tmp"
        code="import os;from pathlib import Path;p=Path(%r);p.write_text('x');os.chmod(p,0o600);os.replace(p,Path(%r))" % (str(self.skills/'.usage_abc12_3z.tmp'),str(outside))
        result=self.observed(code)
        self.assertEqual(result["wrapper_exit"],1)
        self.assertTrue(any(e["category"]=="REJECT_BOOKKEEPING_TEMP_RENAME_OUTSIDE_TARGET" for e in result["events"]))


class DecisionReceiptControls(Fixture):
    def setUp(self):
        super().setUp()
        self.run=self.base/"run"; (self.run/"runtime").mkdir(parents=True)
        self.policy_path=self.run/"bookkeeping-policy-v2.private.json";put(self.policy_path,self.policy)
        paths=[self.skills,self.usage,self.lock,self.instruction,self.memory]
        baseline=preservation.capture_files(paths)
        put(self.run/"baseline.json",{"result":"COMPLETE","entries":baseline})
        self.scope={"protected":list(map(str,paths)),"sealed_inputs":[],"frozen_roots":[],"enumeration_roots":[str(self.skills)],
                    "repositories":[],"metadata_roots":[],"expected_missing":[],"allowed":[str(self.run/"runtime")],
                    "bookkeeping_policy":str(self.policy_path)}
        put(self.run/"scope.json",self.scope)
        self.source=self.base/"executor-source.py";self.source.write_text("fixed\n")

    def compare(self):
        return decision_evidence.compare(self.run,{},phase="CONTROL",gate=None,scope_override=None,sealed={},
                                         source_paths=[self.source],candidate=execution.SHA,base=execution.BASE,
                                         tree=execution.TREE,exact=lambda root:None)

    def test_actual_receipt_uses_captured_values_and_preserves_old_reject(self):
        changed=record();changed["use_count"]=2;self.replace_usage(changed)
        saved=self.compare();receipt=json.loads(saved.read_text())
        self.assertEqual(receipt["decision"],"PASS")
        self.assertEqual(receipt["OLD_STRICT_PRESERVATION_RESULT"],"OLD_STRICT_REJECT")
        self.assertEqual(receipt["V2_INPUT_INTEGRITY_RESULT"],"PASS")
        self.assertEqual(receipt["bookkeeping_evaluation"]["current_raw_sha256"],receipt["current"][str(self.usage)]["sha256"])

    def test_strict_violation_writes_rejection_receipt_and_raises(self):
        self.memory.write_text("changed\n")
        with self.assertRaisesRegex(RuntimeError,"FROZEN_BASELINE_DRIFT"):
            self.compare()
        receipts=list((self.run/"runtime/decision-evidence").glob("*.json"))
        self.assertEqual(len(receipts),1)
        self.assertEqual(json.loads(receipts[0].read_text())["decision"],"REJECT")

    def test_evidence_write_failure_fails_closed(self):
        with patch.object(decision_evidence.os,"write",side_effect=PermissionError(13,"INJECTED_EVIDENCE_DENIED")):
            with self.assertRaisesRegex(RuntimeError,"DECISION_EVIDENCE_WRITE_FAILED"):
                self.compare()


class LaunchPathControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"));self.addCleanup(self.temp.cleanup)
        self.run=Path(self.temp.name)/"run"; (self.run/"runtime").mkdir(parents=True)
        order=["G%02d"%i for i in range(29)]
        put(self.run/"bindings.json",{"order":order,"gates":{n:{} for n in order}})
        put(self.run/"seal.json",{"files":{},"run_id":self.run.name,"candidate":execution.SHA,"tree":execution.TREE,"base":execution.BASE})
        put(self.run/"preflight.json",{"result":"ENGINEERING_READY","engineering_blockers":[],"run_id":self.run.name,
                                        "candidate":execution.SHA,"tree":execution.TREE,"base":execution.BASE})
        self.q=Path(self.temp.name)/"qualification.json";put(self.q,{"fixture":True})
        self.policy=self.run/"bookkeeping-policy-v2.private.json";put(self.policy,{"fixture":True})
        put(self.run/"prepare.json",{"qualification":str(self.q)})
        self.review=Path(self.temp.name)/"review.json"
        self.decision={"engineering_execution_authorization":"OWNER_AUTHORIZED","owner_decision_sha256":runner.OWNER_SHA256,
                       "owner_contract_version":runner.OWNER_CONTRACT_VERSION,"independent_review":"PENDING",**runner.REVIEW_STATES,
                       "run_id":self.run.name,"candidate":execution.SHA,"tree":execution.TREE,"base":execution.BASE,
                       "executor_identity":"synthetic-executor","bookkeeping_policy_sha256":coverage.digest(self.policy),
                       "qualification_sha256":coverage.digest(self.q),
                       "seal_sha256":coverage.digest(self.run/"seal.json"),"preflight_sha256":coverage.digest(self.run/"preflight.json")}
        put(self.review,self.decision);self.calls=[]
        self.ready={"result":"ENGINEERING_READY","engineering_blockers":[],"run_id":self.run.name,
                    "candidate":execution.SHA,"tree":execution.TREE,"base":execution.BASE}

    def patches(self, compare=lambda *a,**k:None):
        def gate(name,m,run,scope,sealed,results):
            self.calls.append(name);return {"gate":name,"result":"PASS","native_exit":0,"wrapper_exit":0,
                                             "run_id":run.name,"candidate":execution.SHA,"tree":execution.TREE}
        return [patch.object(runner,"owner_authorization",lambda:None),patch.object(runner,"check_execution_seal",lambda *a:None),
                patch.object(runner,"preflight",lambda *a,**k:self.ready),patch.object(runner,"compare_baseline",compare),
                patch.object(runner,"run_gate",gate),patch.object(runner,"repos",lambda run:[]),
                patch.object(runner,"load",side_effect=lambda p: self.scope_load(p)),
                patch.object(runner,"verify_executor_identity",lambda *a:{"identity":"synthetic-executor"}),
                patch.object(runner.freshness,"dependency",lambda *a:None)]

    def scope_load(self,path):
        path=Path(path)
        if path==self.run/"scope.json":return {"protected":[],"allowed":[str(self.run/"runtime")]}
        if path==self.run/"bookkeeping-policy-v2.private.json":return json.loads(self.policy.read_text())
        return json.loads(path.read_text())

    def test_genuine_v2_acceptance_reaches_all_29_mocked_expensive_gates(self):
        put(self.run/"scope.json",{"protected":[],"allowed":[str(self.run/"runtime")]})
        with ExitStack() as stack:
            for item in self.patches():stack.enter_context(item)
            self.assertEqual(runner.run_all(self.run,self.review),0)
        self.assertEqual(len(self.calls),29)
        self.assertTrue((self.run/"runtime/START.json").is_file())

    def test_prestart_strict_violation_prevents_launch_despite_native_rc0(self):
        put(self.run/"scope.json",{"protected":[],"allowed":[str(self.run/"runtime")]})
        def reject(*args,**kwargs):raise RuntimeError("INJECTED_STRICT_INPUT_VIOLATION_NATIVE_RC_0")
        with ExitStack() as stack:
            for item in self.patches(reject):stack.enter_context(item)
            with self.assertRaisesRegex(RuntimeError,"STRICT_INPUT_VIOLATION"):
                runner.run_all(self.run,self.review)
        self.assertEqual(self.calls,[]);self.assertFalse((self.run/"runtime/START.json").exists())

    def test_stale_owner_and_launch_bindings_reject(self):
        bad=Path(self.temp.name)/"owner.txt";bad.write_text("changed")
        with patch.object(runner,"OWNER_AUTHORIZATION",bad):
            with self.assertRaisesRegex(RuntimeError,"AUTHORIZATION_MISSING_OR_CHANGED"):runner.owner_authorization()
        self.decision["seal_sha256"]="0"*64;put(self.review,self.decision)
        with self.assertRaisesRegex(RuntimeError,"UNBOUND_ENGINEERING_LAUNCH_RECEIPT"):
            with patch.object(runner,"owner_authorization",lambda:None),patch.object(runner,"check_execution_seal",lambda *a:None),patch.object(runner,"verify_executor_identity",lambda *a:{"identity":"synthetic-executor"}):
                runner.run_all(self.run,self.review)


class BindingControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"));self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.run=self.root/"run";self.run.mkdir()
        init=self.run/"runtime/cache/backend/gradle/init.d";init.mkdir(parents=True)
        shutil.copyfile(execution.H/"packaging.init.gradle",init/"ep19-packaging.gradle")
        self.policy=self.run/"bookkeeping-policy-v2.private.json"
        put(self.policy,{"schema":bookkeeping_v2.SCHEMA,"contract_version":runner.OWNER_CONTRACT_VERSION,
                         "owner_authorization_sha256":runner.OWNER_SHA256})
        self.identity=self.root/"identity.json";put(self.identity,{"fixture":True})
        self.files=coverage.seal(coverage.local_imports()[0]+[runner.OWNER_AUTHORIZATION,self.policy,self.identity])

    def check(self,files):
        with patch.object(runner,"EXECUTOR_IDENTITY",self.identity),patch.object(runner,"verify_executor_identity",lambda *a:{"identity":"fixture"}):
            return runner.check_execution_seal(self.run,files)

    def test_current_executor_policy_owner_seal_binding_passes(self):
        self.check(self.files)

    def test_stale_executor_identity_and_policy_reject(self):
        stale=dict(self.files);stale[str(coverage.local_imports()[0][0])]="0"*64
        with self.assertRaisesRegex(RuntimeError,"FROZEN_INPUT_CHANGED"):self.check(stale)
        policy=json.loads(self.policy.read_text());policy["contract_version"]="V1";put_path=self.policy
        put_path.write_text(json.dumps(policy)+"\n");current=dict(self.files);current[str(self.policy)]=coverage.digest(self.policy)
        with self.assertRaisesRegex(RuntimeError,"VERSION_MISMATCH"):self.check(current)

    def qualification(self):
        files=[]
        for name,content in (("program.py","# fixture\n"),("raw.log","ok\n"),("red.log","red\n"),("green.log","green\n")):
            p=self.root/name;p.write_text(content);files.append(p)
        process=self.root/"process.json";put(process,{"native_exit":0,"log_sha256":coverage.digest(self.root/"raw.log")});files.append(process)
        result=self.root/"result.json";put(result,{"result":"PASS","tests":1,"failures":0,"errors":0});files.append(result)
        matrix=self.root/"matrix.json";put(matrix,{"result":"PASS"});files.append(matrix)
        reuse=self.root/"reuse.json";put(reuse,{"result":"PASS"});files.append(reuse)
        helpers=coverage.seal(coverage.local_imports()[0]);deps={**helpers,**coverage.seal(files)}
        q=self.root/"qualification.json"
        areas=("bookkeeping_parser","bookkeeping_metadata","observer_reducer","decision_evidence","baseline_seal",
               "preflight","prestart","command_boundary","final_acceptance","launch_reachability","strict_scope",
               "evidence_write_failure","identity_binding")
        put(q,{"schema":"ep19-bookkeeping-v2-qualified-v1","result":"PASS","helpers":helpers,"dependencies":deps,
               "qualification_program":str(self.root/"program.py"),"raw_log":str(self.root/"raw.log"),
               "process_receipt":str(process),"result_receipt":str(result),"red_log":str(self.root/"red.log"),
               "green_log":str(self.root/"green.log"),"qualification_matrix":str(matrix),"reuse_ledger":str(reuse),
               "product_gate_execution":False,**{a:"PASS" for a in areas}})
        return q

    def test_complete_and_incomplete_qualification_closure(self):
        q=self.qualification()
        with patch.object(coverage,"full_capsule_reuse_qualified",return_value=True):self.assertTrue(coverage.qualification_inputs(q))
        data=json.loads(q.read_text());data["prestart"]="NOT_RUN";q.write_text(json.dumps(data)+"\n")
        with self.assertRaisesRegex(RuntimeError,"V2_QUALIFICATION_AREA_NOT_PASS"):coverage.qualification_inputs(q)

    def test_old_helper_identity_rejects(self):
        q=self.qualification();data=json.loads(q.read_text());key=next(iter(data["helpers"]));data["helpers"][key]="0"*64;q.write_text(json.dumps(data)+"\n")
        with self.assertRaisesRegex(RuntimeError,"QUALIFICATION_HELPER_BINDING"):coverage.qualification_inputs(q)


if __name__=="__main__":unittest.main(verbosity=2)
