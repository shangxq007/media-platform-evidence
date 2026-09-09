from pathlib import Path
import json, hashlib, shutil, os, re
R=Path(__file__).resolve().parent.parent
E=Path(__file__).resolve().parent
P=E/'LOCAL_REVIEW_PACKAGE'
P.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
omissions=[]; copied=[]
def put(n,data):
 p=P/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
def jout(n,d):put(n,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def copy(p,n=None):
 assert p.is_file() and not p.is_symlink(),str(p)
 n=n or str(p.relative_to(R));b=p.read_bytes();put(n,b);copied.append({'source':str(p),'payload':n,'bytes':len(b),'sha256':sha(b)})
def omit(p,why):
 omissions.append({'source':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'reason':why})
def tree(d):
 for root,ds,fs in os.walk(R/d,followlinks=False):
  ds[:]=[s for s in ds if s not in ['node_modules','__pycache__','.git'] and not any(t in s.lower() for t in ['profile','cache','home','vite-temp']) and not (Path(root)/s).is_symlink()]
  for f in fs:
   p=Path(root)/f
   if p.is_file() and not p.is_symlink():copy(p)
for n in ['WRITER_BRIEF.md','BASELINE_CONTRACT_REVIEW.md','PRIOR_PUBLIC_INTAKE.json','PRIOR_HISTORY_SHA256.json','STATUS_AT_START.txt','TOOLCHAIN_VERIFICATION.json','CONTROL_PLANE_STATUS.json','WRITER_NATIVE.log','CORRECTION_01.md','CORRECTION_02.md','CORRECTION_03.md','CORRECTION_01_HANDOFF.md','IMPLEMENTATION_REVIEW_01.md','CORRECTION_01_NATIVE.log','CORRECTION_02_NATIVE.log','CORRECTION_03_NATIVE.log','FINAL_GATES_NATIVE.log','FINAL_GATES_02_NATIVE.log','FINAL_GATES_03_NATIVE.log','gate.py','test_accounting.py','capture_final.py','capture_final_02.py','run_gates.py','run_gates_02.py','run_gates_03.py','BROWSER_PARENT_VERIFICATION.json']:copy(R/n)
for d in ['writer','correction-01','correction-02','correction-03']:
 for p in (R/d).iterdir():
  if not p.is_file():continue
  if p.stat().st_size>1000000 or p.name in ['before-sha256.json','v9-tracked.diff','v9-complete.patch']:
   omit(p,'重复全树/历史清单或已被最终完整补丁替代；原件保留，不纳入小包');continue
  copy(p)
 for sub in ['before-source','red-source','source']:
  if (R/d/sub).exists():tree(d+'/'+sub)
for p in (R/'validation-03').iterdir():
 if p.is_file():
  if p.suffix=='.index' or p.name=='FINAL_TREE_MANIFEST.txt':omit(p,'Git 索引或全仓清单；完整最终 delta/endpoints 与小范围绑定已包含')
  else:copy(p)
for d in ['validation-03/source','validation-03/before-source','validation-03/gates','validation-03/build']:tree(d)
for n in ['REQUIRED_GATE_SUMMARY.json']:
 copy(R/'validation-01'/n);copy(R/'validation-02'/n)
# Keep native initial architecture failure, not just its summarized history.
for p in (R/'validation-01/gates').glob('architecture*'):copy(p)
context=['AGENTS.md','frontend/package.json','frontend/package-lock.json','frontend/vite.config.ts','frontend/tsconfig.json','frontend/tsconfig.app.json','frontend/tsconfig.node.json','frontend/src/product/timeline/gateways.ts','frontend/src/product/timeline/types.ts','frontend/src/product/timeline/editor-state.ts','frontend/src/api/app/timeline-query.gateway.ts','frontend/src/api/app/asset.gateway.ts','frontend/src/api/app/capability.gateway.ts','frontend/src/interaction/SelectionContext.tsx','frontend/src/interaction/model.ts','frontend/src/interaction/InteractionDialog.tsx','frontend/src/foundation/effectiveAccess.tsx','frontend/src/foundation/projectContext.tsx','frontend/src/foundation/platformClient.ts','frontend/src/app/routeTree.tsx','frontend/src/auth/oidcClient.ts','frontend/src/auth/oidcConfig.ts','frontend/src/components/design-system/index.tsx','frontend/src/components/app-shell/AppShell.tsx']
for n in context:
 p=R/'validation-03/snapshot'/n
 if p.exists():copy(p,'context-source/'+n)
 else:omissions.append({'source':'validation-03/snapshot/'+n,'reason':'候选上下文路径不存在，未虚构'})
# Include the actual authored time contract as read-only context, no unrelated backend inventory.
for p in (R/'validation-03/snapshot').glob('*/src/main/java/**/MediaClip.java'):copy(p,'context-source/'+str(p.relative_to(R/'validation-03/snapshot')))
for p in (R/'validation-03/snapshot').glob('shared-kernel/src/main/java/**/MediaTime.java'):copy(p,'context-source/'+str(p.relative_to(R/'validation-03/snapshot')))
B=R/'browser-v9'
for p in B.iterdir():
 if not p.is_file():continue
 if p.name in ['FINAL03_BEFORE_MANIFEST.json','ARTIFACT_MANIFEST.json','CONTINUATION_HASH_BINDING.json']:
  omit(p,'历史/重复广泛源码清单；保留其原件摘要及最终 frontend 子集');continue
 if p.name=='FINAL03_HASH_BINDING.json':
  d=json.loads(p.read_text()); rows=d['source']['files'];print('source rows type',type(rows).__name__)
  if isinstance(rows,dict): d['source']['files']={k:v for k,v in rows.items() if k.startswith('frontend/')}
  else:d['source']['files']=[x for x in rows if x.get('path','').startswith('frontend/')]
  d['source']['selection_note']='仅 frontend 行；非前端全树行省略。其他 build/fixture/runner/served 绑定原样保留。'
  d['original_evidence']={'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'original_source_count':len(rows),'retained_source_count':len(d['source']['files'])}
  jout('browser-v9/FINAL03_HASH_BINDING_FRONTEND_SUBSET.json',d);omit(p,'以明确标注的 frontend 子集代替原始广泛源码清单');continue
 copy(p)
for d in ['fixture-final03','runner-final03','build-final03','final03-run-01','final03-run-02','failures','probe-01']:tree('browser-v9/'+d)
# Original native RED locator proof; avoid thirty repeated old screenshots.
for d in ['continuation-run-04','continuation-run-05']:
 for p in (B/d).iterdir():
  if p.is_file() and (p.suffix!='.png' or (d=='continuation-run-05' and p.name=='V9-02-failure.png')):copy(p)
# Preserve V8 package scheme itself as provenance, not prior result evidence.
v8=R.parent/'FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/package.py'
copy(v8,'provenance/V8_package.py')
chunks=[]
for root in [P/'validation-03/build',P/'browser-v9/build-final03']:
 for p in sorted(root.rglob('*.js')):
  if p.stat().st_size<=96000:continue
  data=p.read_bytes();parts=[];start=0
  while start<len(data):
   end=min(start+96000,len(data))
   while True:
    try:data[start:end].decode('utf-8');break
    except UnicodeDecodeError:end-=1
   part=data[start:end];n='build-chunks/'+str(p.relative_to(P)).replace('/','__')+f'.part{len(parts):03d}.txt';put(n,part)
   parts.append({'order':len(parts),'path':n,'bytes':len(part),'sha256':sha(part)});start=end
  chunks.append({'original':str(p.relative_to(P)),'bytes':len(data),'sha256':sha(data),'parts':parts,'original_included':True})
jout('BUILD_CHUNK_RECONSTRUCTION.json',chunks)
for c in chunks:
 b=b''.join((P/x['path']).read_bytes() for x in c['parts']);assert sha(b)==c['sha256'] and b==(P/c['original']).read_bytes()
D=json.loads((R/'validation-03/SOURCE_DELTA.json').read_text())
for x in D['paths']:
 assert sha((P/'validation-03/source'/x['path']).read_bytes())==x['after_sha256']
 if x['before_sha256']:assert sha((P/'validation-03/before-source'/x['path']).read_bytes())==x['before_sha256']
A=json.loads((R/'validation-03/TEST_IDENTITY_ACCOUNTING.json').read_text())
G=json.loads((R/'validation-03/REQUIRED_GATE_SUMMARY.json').read_text())
assert G['required']==G['invoked']==G['passed']==7
screens=list((P/'browser-v9/final03-run-01').glob('*.png'))+list((P/'browser-v9/final03-run-02').glob('*.png'));assert len(screens)==32
for run in ['final03-run-01','final03-run-02']:
 checks=json.loads((P/'browser-v9'/run/'NATIVE_CHECKS.json').read_text());sc=json.loads((P/'browser-v9'/run/'SCENARIO_RESULTS.json').read_text());assert len(checks)==89 and all(x['passed'] for x in checks);assert len(sc)==15 and all(x['status']=='PASS' for x in sc)
idx={
'TASK':R.name,'LANE':'FRONTEND','FRONTEND_BRANCH':'refs/heads/agent/frontend-wave2-product-ux-v1',
'PRIOR_V8_REVIEW_ADOPTION_RECORDED':{'status':'YES_BOUNDED','source':'validation-03/source/frontend/governance/UX_WAVE_1_REVIEW.md','limits':'可信且足够稳定 SDK session 正常续期保留 draft/editor；真实上下文退休；可归属旧 reads/notifications/unmount 隔离；标题仅桌面/窄屏有限检查。missing sid/unknown validity 可清理，未标记旧 invalidation、旧 SDK storage overwrite 不保证全面隔离；无真实 IdP/backend/session/access 集成。'},
'PLAN_SOURCE_AND_ITEM':{'source':'validation-03/source/docs/architecture/governance/frontend-product-information-architecture-v1.md','priority_line':486,'structured_list_lines':'344-346','current_authorization_lines':'516-522','priority':'Scene/Shot discovery and inspection > Render observability > Workflow UX > bounded NLE editing > Agent-assisted creative','item':'现有 NLE 优先项中的 navigation/inspection 与 structured list alternative；非 canonical editing/Agent 授权','preimplementation_scope':'writer/SCOPE_AND_CONTRACT.md'},
'BASELINE_IMPLEMENTATION_TREE':D['baseline_tree'],'FINAL_IMPLEMENTATION_TREE':D['final_tree'],
'USER_VISIBLE_OUTCOME':'现有 Project NLE 入口诚实展示 Project/Timeline/Revision 与未配置边界。显式 isolated-verification source 下完成结构化轨道/片段发现、过滤、精确定位、选择、元数据检查、关闭及继续；普通入口没有真实 loaded geometry，不能称真实集成 NLE 已加载。',
'REUSED_NLE_SURFACES_AND_TIMELINE_GATEWAY':'复用 NleWorkspace/ProjectFrame/routeTree、TimelineQueryGateway HEAD/history/detail/compare、Selection owner/LOCAL_EPHEMERAL dispatcher、SelectionInspector/InteractionDialog；未新增服务端读写端点。',
'TIMELINE_SOURCE_AND_REVISION_BOUNDARIES':'网关只有元数据；productId 历史上映射 Project==Timeline，history limit50 非完整历史。摘要/变更计数不能重建轨道。显式前端 source 验证 request/scope/target/revision echo、唯一性、轨道关系、time bounds、simulated access；历史 revision 不复用 HEAD digest。默认 absent=unavailable 非空。',
'TIME_MODEL_AND_NAVIGATION_BEHAVIOR':'ExactMediaTime integer/rational string，正分母、最多64字符、非负导航；BigInt 精确比较/差值。MediaClip authored TimeRange 为双端 inclusive，包括零长度点与共享边界多匹配；按 loaded 次序选择首项，Locate selected 保留显式目标。未知单位禁用相关定位/时长，不猜 FPS/总时长；局部 position 非播放。没有新增 zoom；检查/equal refresh 保留 list scroll。',
'SELECTION_INSPECTION_AND_FOCUS_RESULT':'单一 owner、LOCAL_EPHEMERAL；仅 supplied identity/name/type/version/source logical refs 和 exact ranges。无媒体链接。鼠标/键盘/中文英文/窄屏，metadata/mobile dialog occurrence 绑定 target/lifetime/store；失效不自动复活，焦点回 connected launcher 或受限 fallback。',
'CONTEXT_AND_STALE_RESULT_HANDLING':'真实 Project/Timeline/Revision/identity/access/source/store 变化退休 selection/detail，abort/隔离迟到结果及 retained toolbar/modal callbacks；equal timestamps/可信正常续期不重置。非全平台/所有未知 SDK 陈旧事件保证。',
'OPERATION_AND_PERMISSION_BOUNDARIES':'现有 Operation preview→frozen confirmation→apply→authoritative readback 及 IDs 保留；导航不写 canonical、不执行媒体访问。既有 asset/capability mount 读取独立。timeline.operation.apply 仅用于 access retirement observation，非新增授权。无伪造 permission/DTO/server authority。',
'PRODUCT_CHANGED_PATHS':[x['path'] for x in D['paths'] if x['path'].startswith(('frontend/src/','frontend/scripts/'))],
'DOCUMENTATION_CHANGED_PATHS':[x['path'] for x in D['paths'] if not x['path'].startswith(('frontend/src/','frontend/scripts/'))],
'TARGETED_TEST_RESULTS':{'passed':241,'failed':0,'source':'validation-03/TARGETED.json'},
'FULL_TEST_IDENTITY_ACCOUNTING':{'counts':A['counts'],'source':'validation-03/TEST_IDENTITY_ACCOUNTING.json','removed_expectations':'writer/expectation-mapping.json','identity':'[frontend-relative file, ancestorTitles array, exact title]'},
'REQUIRED_FRONTEND_GATE_RESULTS':{'required':7,'passed':7,'source':'validation-03/REQUIRED_GATE_SUMMARY.json','gates':[{'name':x['name'],'exit_code':x.get('exit_code',x.get('exit'))} for x in G['results']],'lint':'46 prior/46 retained/46 final warnings; added0 removed0 errors0; LINT_ACCOUNTING.json'},
'FOCUSED_BROWSER_SCENARIOS_AND_CHECK_COUNTS':{'runs':2,'scenarios_per_run':15,'assertions_per_run':89,'unique_scenarios':15,'scenario_executions':30,'assertion_executions':178,'distinct_assertions':89,'repeat_assertions':89,'final_screenshots':32,'source':'browser-v9/BROWSER_FINAL_GREEN_OR_BLOCKED_HANDOFF.md','parent_record':'BROWSER_PARENT_VERIFICATION.json','visual_scope':'父记录仅6张代表图实际视觉检查，不声称全部32张；本包装者未做独立视觉验收'},
'MOCK_AND_REAL_DATA_BOUNDARIES':'native Chromium + 实际产品 UI/SDK User/oidcClient 包装器；geometry/workspace/access/SDK transport/events 均 synthetic isolated fixture。真实 gateway GET 只到 loopback receiver、不转发后端。普通 native 路径 Workspace context unavailable(503)。保留 programmatic retained React callback/late-result probes 与 native Input 操作区别。无物理键盘/IME/screen-reader/真实授权/IdP/backend。',
'BUILD_MANIFEST_SHA256':sha((R/'validation-03/BUILD_MANIFEST.sha256').read_bytes()),
'BACKEND_REQUIREMENTS_UPDATED':'YES_EXISTING_LEDGERS_ONLY','NEW_BACKEND_REQUIREMENTS':'没有新台账/端点/权限；既有 UXW1-003/004 与 FB-GAP-001/002/003 记录 geometry/time/identity/access/version/failure 缺口。未来仅固定版本单 Project/Timeline/Revision 只读集成，允许/拒绝身份、完整/有界结果与 stale/failure/retirement、零写入约束。','BACKEND_CHANGES':'NONE','TRACKED_DIST_CHANGES':'NONE','BACKEND_STATIC_CHANGES':'NONE','REAL_INTEGRATION_PERFORMED':'NO',
'BOUNDED_PRESERVATION_RESULT':{'source':'validation-03/PRESERVATION.json','patch_replay':'validation-03/PATCH_REPLAY.json','historical_records':'writer/PRESERVATION.json; correction-01/02/03 PRESERVATION.json; browser-v9/FINAL03_PRESERVATION.json','limit':'本包装只验证所选文件复制/端点/ZIP一致性，不代替产品独立验收；未改原始记录/旧归档。'},
'PRODUCT_COMMIT_FREEZE_MERGE_PUSH':'NOT_PERFORMED','PRODUCT_PUBLICATION':'NOT_PERFORMED','EVIDENCE_DELIVERY_STATUS':'NOT_YET_PUBLISHED','EVIDENCE_COMMIT_SHA':'NOT_YET_PUBLISHED','REVIEW_INDEX_URL':'NOT_YET_PUBLISHED','MACHINE_INDEX_URL':'NOT_YET_PUBLISHED','PUBLIC_MANIFEST_SHA256':'NOT_YET_PUBLISHED','REMOTE_VERIFICATION':'NOT_YET_PUBLISHED','INDEPENDENT_REVIEW':'REQUIRED','STOP':'YES_LOCAL_PACKAGING_ONLY',
'FAILURE_AND_AUTHORIZATION_HISTORY':'保留 writer 原生 RED/typecheck/lint/异步测试失败；validation-01 architecture RED→correction01 控制 RED/GREEN；IR01 生命周期 correction02 RED/GREEN；browser 原 BLOCKED tool consent denial 未越过，随后 parent-approved retrigger 见历史 handoff；continuation04/05 selected-clip submit RED 保留；correction03 两个 RED 回归→type=button 修复→final03 两次 scoped GREEN。历史失败不重标 GREEN；最终 phase 无新 denial。',
'LOCAL_REPORT':'REVIEW_REPORT_ZH.md','LOCAL_MANIFEST':'MANIFEST.sha256','SOURCE_ENDPOINTS':'validation-03/SOURCE_DELTA.json','COMPLETE_DELTA':'validation-03/TASK_DELTA.patch','CHUNKS':'BUILD_CHUNK_RECONSTRUCTION.json','OMISSIONS':'OMISSIONS.json'}
jout('REVIEW_INDEX.json',idx)
report='# V9 小型本地评审包（中文）\n\n**结论边界：这是已存在证据的打包与本地完整性核验，不是独立产品验收。INDEPENDENT_REVIEW=REQUIRED；PRODUCT_PUBLICATION=NOT_PERFORMED；所有外部证据发布字段封包时为 NOT_YET_PUBLISHED。** 后续发布 SHA/URL/远端验证由父代理提供 detached delivery，不猜测未来 SHA、不递归改写本清单。\n\n最终实现树 `'+D['final_tree']+'`；源自基线 `'+D['baseline_tree']+'`。产品源文件、完整 delta 与 before/after endpoints 已包含。原始 writer 手册中的早期路径/计数/待验状态属历史；最终20路径以 SOURCE_DELTA.json 为准，最终 gates/browser 以 validation-03/final03 为准。\n\n## 核心审查入口\n\n- [完整补丁](validation-03/TASK_DELTA.patch)、[精确端点](validation-03/SOURCE_DELTA.json)、[已有补丁重放凭据](validation-03/PATCH_REPLAY.json)\n- [七项原生 gate](validation-03/REQUIRED_GATE_SUMMARY.json)、[身份账本](validation-03/TEST_IDENTITY_ACCOUNTING.json)、[lint账本](validation-03/LINT_ACCOUNTING.json)\n- [最终 browser handoff](browser-v9/BROWSER_FINAL_GREEN_OR_BLOCKED_HANDOFF.md)、[父记录](BROWSER_PARENT_VERIFICATION.json)、[受限 frontend/完整 build served绑定](browser-v9/FINAL03_HASH_BINDING_FRONTEND_SUBSET.json)\n- [历史 BLOCKED](browser-v9/BROWSER_FINAL_HANDOFF.md)、[历史 RED 与获准重触发](browser-v9/BROWSER_CONTINUATION_HANDOFF.md)、[原 run05 locator](browser-v9/continuation-run-05/LOCATE_SELECTED_DIAGNOSTIC.json)\n\n## 用户要求字段（全部）\n\n'
for k,v in idx.items():
 report+='### '+k+'\n\n'+(v if isinstance(v,str) else '```json\n'+json.dumps(v,ensure_ascii=False,indent=2)+'\n```')+'\n\n'
report+='## 封包、重建和省略\n\n使用 V8 相同 UTF-8 96000-byte 上限分块与顺序拼接方案；每部分增加显式 order 与 SHA256，记录原始 SHA256，原 JS 保留供逐字节对照。打包核验重建与原字节完全一致。BUILD_CHUNK_RECONSTRUCTION.json 是实际顺序。provenance/V8_package.py 仅方案来源，勿直接执行旧路径脚本。\n\n不包含 node_modules、browser HOME/profile/cache、Git objects/index、完整 snapshots、无关历史 bulk 或重复广泛源码清单。OMISSIONS.json 记录被替换清单的原件摘要及选择理由；最终 binding 只裁剪 source 部分，ordinary/injected build、fixture、runner、served 原生绑定保持。源文件/旧归档只读保留。\n\nMANIFEST.sha256 覆盖全部 payload 文件（自身除外）。ZIP 逐项与本地文件和清单核对；核验回执 PACKAGE_VERIFICATION.json 在 payload 外，避免自引用。扫描仅所选公开字节的 credential-shaped/private-key 特征，不访问凭据、不做全局扫描；不等同于证明任意秘密绝不存在。最终32张截图均入包，另含1张历史 RED 截图；父代理仅实际审阅6张代表图，仍保留极长名称导致桌面 inspector 很高的限制。\n'
put('REVIEW_REPORT_ZH.md',report.encode())
put('REVIEW_INDEX.md',('# V9 local review index\n\n[中文报告](REVIEW_REPORT_ZH.md) · [全部用户字段 / machine index](REVIEW_INDEX.json) · [SHA256清单](MANIFEST.sha256)\n\n最终树 `'+D['final_tree']+'`。7/7 frontend gates；targeted241；full918=884保留+34新增，baseline890中移除6（显式映射）。final03两次各15场景/89断言，共32截图。普通路径仅 workspace unavailable；loaded导航为隔离注入验证，不是后端真实集成。\n\n[源码delta](validation-03/SOURCE_DELTA.json) · [完整补丁](validation-03/TASK_DELTA.patch) · [测试身份](validation-03/TEST_IDENTITY_ACCOUNTING.json) · [最终浏览器](browser-v9/BROWSER_FINAL_GREEN_OR_BLOCKED_HANDOFF.md) · [父代表图检查](BROWSER_PARENT_VERIFICATION.json) · [分块顺序及原SHA](BUILD_CHUNK_RECONSTRUCTION.json) · [省略说明](OMISSIONS.json)\n\nINDEPENDENT_REVIEW=REQUIRED；PRODUCT_PUBLICATION=NOT_PERFORMED；EVIDENCE_DELIVERY_STATUS/EVIDENCE_COMMIT_SHA/REVIEW_INDEX_URL/MACHINE_INDEX_URL/PUBLIC_MANIFEST_SHA256/REMOTE_VERIFICATION=NOT_YET_PUBLISHED。后续 detached publication receipt 另交付；本包 STOP=YES_LOCAL_PACKAGING_ONLY。\n').encode())
jout('OMISSIONS.json',{'policy':'SMALL selected review payload, no snapshots/dependencies/profiles/caches/Git objects/index/unrelated history. Original task files and old archives remain unchanged. Source binding subset is explicitly marked, never passed off as original.','specific_omissions':omissions})
jout('SELECTED_ORIGINALS.json',copied)
print(json.dumps({'created_payload':str(P),'selected_originals':len(copied),'payload_files':sum(p.is_file() for p in P.rglob('*')),'chunks':len(chunks),'source_paths':len(D['paths']),'final_screenshots':len(screens)},indent=2))
