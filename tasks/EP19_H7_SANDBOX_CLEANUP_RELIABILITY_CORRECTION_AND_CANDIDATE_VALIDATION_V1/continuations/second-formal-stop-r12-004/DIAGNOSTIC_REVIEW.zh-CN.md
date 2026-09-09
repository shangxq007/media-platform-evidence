# 诊断入口：第二次正式真实 STOP

此文仅由已保存回执和静态源码生成；未调用policy builder、collector或测试。

## `evidence/implementation-r12/tooling/qualification/policy_builder.py:39-70`

```text
39:     return result
40: 
41: 
42: def validate_provenance(app, private_map, private_inventory, dependency):
43:     import dependency_contract
44:     dependency_contract.validate(dependency, matrix_path=ROOT / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json")
45:     if app.get("private_manifest_sha256") != digest(private_map):
46:         raise RuntimeError("PRIVATE_ELIGIBLE_MAP_PROVENANCE_MISMATCH")
47:     if app.get("private_strict_inventory_sha256") != digest(private_inventory):
48:         raise RuntimeError("PRIVATE_STRICT_INVENTORY_PROVENANCE_MISMATCH")
49:     return True
50: 
51: 
52: def build(applicability, private_map, private_inventory, owner, dependency):
53:     applicability_path, private_path = Path(applicability), Path(private_map)
54:     app = json.loads(applicability_path.read_text())
55:     declared = json.loads(private_path.read_text())
56:     dependency_value = json.loads(Path(dependency).read_text())
57:     validate_provenance(app, private_path, private_inventory, dependency_value)
58:     if declared.get("schema") != "ep19-eligible-package-manifest-candidate-v1":
59:         raise RuntimeError("PRIVATE_ELIGIBLE_MAP_SCHEMA")
60:     packages = eligible_from_applicability(app)
61:     policy = bk.create_policy(
62:         owner_sha256=digest(owner), dependency_sha256=digest(dependency),
63:         eligible_names=packages)
64:     actual = {name: row["manifest"] for name, row in policy["eligible_map"].items()}
65:     if actual != declared.get("eligible_skills"):
66:         raise RuntimeError("PREBOUND_ELIGIBLE_MANIFEST_CHANGED")
67:     policy["applicability_sha256"] = digest(applicability_path)
68:     policy["prebound_eligible_map_sha256"] = digest(private_path)
69:     return policy
70: 
```

## `evidence/implementation-r12/tooling/executor/external29_driver.py:620-690`

```text
620:             result=merge_graph_exception(result,exc,name,transition)
621:             result.setdefault('candidate',runner.SHA);result.setdefault('tree',runner.TREE)
622:             result.setdefault('semantic_success_artifacts_allowed',False)
623:             results[name]=result
624:             stopped=True
625:             exc.runner_gate_receipt=result
626:             exc.graph_failure_results=results
627:             if result.get('diagnostic_persistence_uncertain'):
628:                 result.update(diagnostic_delivery='BEST_EFFORT_STDERR_PENDING',
629:                               diagnostic_stderr_delivered=False,
630:                               diagnostic_stderr_persistence_claim=False)
631:                 try:
632:                     emit_persistence_uncertainty(result)
633:                 except BaseException as diagnostic:
634:                     raise_diagnostic_emission_failure(exc,diagnostic,result,results)
635:                 result.update(diagnostic_delivery='BEST_EFFORT_STDERR_EMITTED_NOT_DURABLE',
636:                               diagnostic_stderr_delivered=True,
637:                               diagnostic_stderr_persistence_claim=False)
638:         results[name]=result
639:         if result.get('result')!='PASS': stopped=True
640:     return results,stopped
641: 
642: def formal(args):
643:     verify_required_runtime_files()
644:     config,coverage,runner,sequence=modules(args.binding,args.binding_sha256);run=runner.runpath(args.run_id)
645:     review=Path(args.review).absolute();binding=Path(args.binding).absolute()
646:     if args.run_id!=config['run_id']: raise RuntimeError('RUN_ID_BINDING_MISMATCH')
647:     decision=load(review)
648:     if decision.get('implementation_review')!='PASS' or decision.get('independent_final_acceptance') not in ('PENDING','REQUIRED'):
649:         raise RuntimeError('PARENT_IMPLEMENTATION_REVIEW_REQUIRED_FINAL_ACCEPTANCE_STAYS_SEPARATE')
650:     attempt=consume_formal(run,binding,review)
651:     applicability=Path(args.applicability).absolute();private_map=Path(args.private_map).absolute()
652:     observer=None;continuous=None;adapter=None;results={};order=load(ROOT/'candidate-inputs-v3/GATE_EXECUTION_MATRIX.json')['order']
653:     primary_error=None;secondary_errors=[];return_code=1;summary=None
654:     try:
655:         from observe import BoundaryObserver
656:         observer=BoundaryObserver(observer_seed(config,applicability))
657:         from policy_builder import build,write_private
658:         private_inventory=Path(args.private_inventory).absolute()
659:         for supplied,key in ((applicability,'applicability'),(private_map,'private_map'),(private_inventory,'private_inventory')):
660:             if str(supplied)!=config[key] or digest(supplied)!=config[key+'_sha256']:
661:                 raise RuntimeError('FORMAL_PRIVATE_INPUT_BINDING_MISMATCH '+key)
662:         policy=build(applicability,private_map,private_inventory,config['owner'],config['dependency'])
663:         observer.bind_policy(policy)
664:         policy_path=run/'bookkeeping-policy-v3.private.json';write_private(policy_path,policy)
665:         from executor_adapter import RunAdapter
666:         expected={'candidate':config['candidate'],'tree':config['tree'],
667:                   'owner_sha256':config['owner_sha256'],'matrix_sha256':config['matrix_sha256']}
668:         adapter=RunAdapter(run,policy,consumed_attempt=attempt,binding=load(binding),expected_binding=expected)
669:         sequence.verify(run)
670:         scope,sealed,continuous=strict_baseline(run,policy,adapter,observer,config,coverage,runner,sequence,review,binding)
671:         engineering_preflight(run,scope,policy,adapter,observer,config,coverage,runner,sequence,continuous)
672:         latching_strict_check(adapter,run,scope,policy,'PRESTART',coverage,continuous);boundary(adapter,observer,'PRESTART',run,continuous=continuous)
673:         runner.put(run/'runtime/START.json',{'time':time.time(),'run_id':run.name,'attempt_id':attempt['attempt_id'],
674:                                              'review':str(review),'review_sha256':digest(review),'sealed_inputs':sealed})
675:         results,stopped=execute_actual_graph(run,scope,{**sealed,str(review):digest(review)},policy,adapter,observer,runner,coverage,continuous)
676:         try:
677:             if stopped:
678:                 raise RuntimeError('FAILURE_LATCH_BLOCKS_SUCCESS_FINAL')
679:             latching_strict_check(adapter,run,scope,policy,'FINAL',coverage,continuous);boundary(adapter,observer,'FINAL',run,continuous=continuous)
680:             boundary(adapter,observer,'COVERAGE',run,continuous=continuous)
681:             boundary(adapter,observer,'SEAL',run,continuous=continuous,finalize_observation=True)
682:         except Exception as exc:
683:             stopped=True
684:             persist_final_boundary_failure(run,runner,exc)
685:         summary={'schema':'ep19-external29-results-v1','result':'FAIL' if stopped else 'PASS','results':results,
686:                  'required_gates':29,'passed_gates':sum(r.get('result')=='PASS' for r in results.values()),
687:                  'failed_gates':sum(r.get('result')=='FAIL' for r in results.values()),
688:                  'not_run_gates':sum(r.get('result')=='NOT_RUN' for r in results.values()),
689:                  'expected_full_backend_identities':8000,'expected_skips':29,'candidate_acceptance':'PENDING_INDEPENDENT_REVIEW',
690:                  'publication':'NOT_PERFORMED'}
```

## 精确能证明的事实
- `build()` 先核对私有输入摘要/依赖和schema，调用 `bookkeeping_v3.create_policy`，然后把返回的各包 `manifest` 构成 `actual`，以 Python 深相等比较 `declared.get("eligible_skills")`。拒绝点为 `policy_builder.py:66`，调用点为 `external29_driver.py:662`。
- FORMAL_FAILURE 仅持久化原因/调用栈/29项NOT_RUN；没有保存两侧manifest的完整当时差异。因此不能从原因字符串推出某个文件正文变化，更不能推出writer身份、恶意修改或ledger/usage内容非法。
- `bookkeeping_v3.py`、`capture.py`、`dependency_contract.py`、`external29_driver.py`、`sequence.py`、binding 与资格源码均在公开候选中。完整文件比节选优先；具体采集语义由源码审查确定。
- r12资格179 PASS包含真实外层合成路径和prepare consumer sentinel；并非真实共享树manifest长期静止性证明，也不是Lean preparation或正式29门成功。
- 实际preparation与其200项只读advisory是后续事实；其通过不等于formal policy当前eligible相等。review当时未重新读取private map/inventory语义。

## 已合并独立最终失败审查与仍缺的现场证据
`evidence/second-formal-closeout/independent-failure-review/FINAL_REVIEW.zh-CN.md` 与 `FINDINGS.json` 已真实存在，并核对审查者原manifest后加入。结论 BLOCKED_NO_ENGINEERING_ACCEPTANCE。
审查者对有限7包的事后窄哈希观察为107对107条、2个摘要变化、0新增/0缺失；本打包子任务没有再次读取共享包。更重要的是保存的最终准备disposition已记录这两个新摘要，而旧map/strict inventory仍为旧摘要。prepared_ns早于consumed_ns；这些是保存字段，不是独立写入时间见证。公开两条定位与前后摘要，无指令正文或私有完整清单。
正式时刻actual未保存，不能把当前2条集合冒充正式完整差异集。写入者、精确修改时刻和原因均NOT_ESTABLISHED。两个seal各自摘要正确不等于彼此一致；loader与分项有限advisory PASS不能补足这个跨清单关系。

## 给 ChatGPT 的具体复核问题
1. 比较谓词覆盖哪些 manifest 字段？哪些是被批准的严格字段、元数据或输入定位？失败可能来自采集/预绑定生命周期不一致，还是实际受保护变更？请仅按证据区分，不先归责writer。
2. consume→policy→baseline调用次序与2/2消费是否符合既有预算语义？缺少START为何不能退还预算？
3. r12绑定loader、实际prepare资格sentinel、实际preparation seal与formal policy之间，哪些边界已被真实执行，哪些只属合成或静态证明？是否存在尚未闭合的资格覆盖盲点？
4. 一旦独立匿名差异摘要加入，其来源与时间是否足以解释这次拒绝？哪些“当前比较”仍不能证明失败瞬间？
5. AR001..010逐项资格处置及异常原因/持久化历史是否可保留，哪些结论不得提升为产品通过或独立接受？
6. 在不重跑formal、不改产品、不弱化A/B/C且不公开私人正文的前提下，现有诊断是否足够？若不足，请列最小只读证据缺口，而非建议第三次尝试。
7. EP19关闭应如何分别核对工程、独立接受、原账本、当前候选产品发布及sanity？本包只能交付证据，不能自行补造权威账本或关闭结论。
