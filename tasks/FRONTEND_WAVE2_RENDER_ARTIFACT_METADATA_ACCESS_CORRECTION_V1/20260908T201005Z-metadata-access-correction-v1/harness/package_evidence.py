from pathlib import Path
import json,hashlib,shutil,sys,re,zipfile,collections,datetime
E=Path(__file__).parent;V=E/'final-validation-01';B=E/'browser-prep'/('browser-'+sys.argv[1]);P=E/'LOCAL_REVIEW_PACKAGE';P.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
def obj(p):return json.loads(p.read_text())
def cp(src,dest):
 dest=P/dest;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
def put(name,data):
 p=P/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)+'\n')
tree=(V/'FINAL_TREE.txt').read_text().strip();delta=obj(V/'SOURCE_DELTA.json');counts=obj(V/'TEST_IDENTITY_ACCOUNTING.json')['counts'];gates=[obj(p) for p in sorted((V/'gates').glob('*.json'))];assert len(gates)==7 and all(g['exit_code']==0 and g['implementation_tree']==tree for g in gates)
checks=obj(B/'NATIVE_CHECKS.json');result=obj(B/'RESULT.json');assert result['status']=='PASS' and result['tree']==tree and result['checks']==len(checks) and all(r['passed'] and r['IMPLEMENTATION_TREE']==tree for r in checks)
teardown=obj(B/'TEARDOWN.json');assert not teardown['remaining_ports'] and all(r['exit']==0 for r in teardown['processes'] if r['name'] in ['smoke','chrome'])
served=obj(B/'SERVED_ARTIFACTS.json');assert served['differences']==0 and served['tree']==tree
traffic=obj(B/'APPLICATION_TRAFFIC.json');assert not traffic['forbidden'] and traffic['http_mutations']==0
bm=obj(V/'BUILD_MANIFEST.json');assert bm['implementation_tree']==tree
assert {r['path']:r['sha256'] for r in bm['files']}=={r['path']:r['served_sha256'] for r in served['files']}
for r in bm['files']:assert sha((V/'build'/r['path']).read_bytes())==r['sha256']
for n in ['FINAL_VALIDATION_PLAN.json','SCOPED_DIFF_REVIEW.json','SOURCE_DELTA.json','FINAL_TREE.txt','FINAL_TREE_MANIFEST.txt','TASK_DELTA.patch','PATCH_REPLAY.json','TEST_IDENTITY_ACCOUNTING.json','FULL_UNIT.json','TARGETED_FINAL.json','BUILD_MANIFEST.json','BUILD_MANIFEST.sha256','PRESERVATION_FINAL.json','BUILD_TARGET_PRESERVATION_FINAL.json']:cp(V/n,'validation/'+n)
for p in (V/'gates').iterdir():
 if p.is_file():cp(p,'validation/gates/'+p.name)
for root in ['source','before-source']:
 for p in (V/root).rglob('*'):
  if p.is_file():cp(p,root+'/'+str(p.relative_to(V/root)))
# Explicit support source, no backend or unrelated global inventories.
for rel in ['product/render-browser/source.ts','product/render-browser/fixture.ts','product/render-browser/render-browser.css','foundation/effectiveAccess.tsx','interaction/InteractionDialog.tsx','interaction/SelectionContext.tsx','interaction/model.ts','components/design-system/index.tsx']:
 p=V/'snapshot/frontend/src'/rel;cp(p,'support-source/frontend/src/'+rel)
for n in ['BASELINE_VERIFICATION.json','V7_EVIDENCE_INTAKE.json','V7_ANONYMOUS_MANIFEST_READBACK.json','V7_FULL_UNIT.json','ALLOWLIST.json','EXECUTION_SCOPE.md','EXECUTOR_ROUTE.json','WRITER_HANDOFF.md','writer-native.log','writer-native-02.log','writer-stale-guidance.log']:
 if (E/n).is_file():cp(E/n,'task-records/'+n)
# Select native writer attempts; exclude unscoped writer whole-repository maps/state.
for root in ['writer-attempts','writer-guidance-attempts']:
 if not (E/root).exists():continue
 for p in (E/root).rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(E/root)
  if rel.parts[0] in ['red-01','green-01','green-02','red-source','stale-guidance-red','stale-guidance-green'] or p.name in ['WRITER_HANDOFF.md','test-summary.json']:cp(p,'attempts/'+root+'/'+str(rel))
for attempt in sorted((E/'browser-prep').glob('browser-*')):
 if not attempt.is_dir() or attempt.name in ['browser-prep']:continue
 dest='browser-final' if attempt==B else 'prior-browser-attempts/'+attempt.name
 for p in attempt.iterdir():
  if p.is_file() and p.suffix in ['.json','.jsonl','.png','.log','.txt','.py']:cp(p,dest+'/'+p.name)
for p in (V/'build').rglob('*'):
 if p.is_file():cp(p,'build/'+str(p.relative_to(V/'build')))
for p in (E/'browser-prep/fixture-host').iterdir():
 if p.is_file():cp(p,'fixture-host/'+p.name)
for n in ['FIXTURE_HOST_INPUTS.json','BUILD_BINDING.json','PLAN.json','README.md']:
 if (E/'browser-prep'/n).is_file():cp(E/'browser-prep'/n,'fixture-host/'+n)
for n in ['recover.py','materialize.py','gate.py','prepare_final.py','run_final_gates.py','test_accounting.py','verify_build.py','preservation.py','replay_patch.py','package_evidence.py']:
 cp(E/n,'harness/'+n)
for n in ['prepare_fixture_host.py','bind_build.py','run_browser.py','entry.template.tsx']:
 cp(E/'browser-prep'/n,'harness/browser/'+n)
# UTF-8 boundary review chunks retain original emitted JS bytes.
reconstruction=[]
for p in sorted((P/'build').rglob('*.js')):
 data=p.read_bytes()
 if len(data)<=100000:continue
 parts=[];start=0;i=0
 while start<len(data):
  end=min(start+100000,len(data))
  while end<len(data) and data[end]&0xc0==0x80:end-=1
  part=data[start:end];part.decode('utf-8');name='build-review-chunks/'+p.name+'/'+f'{i:04d}.txt';q=P/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(part)
  parts.append({'path':name,'bytes':len(part),'sha256':sha(part)});start=end;i+=1
 assert b''.join((P/r['path']).read_bytes() for r in parts)==data
 reconstruction.append({'original':str(p.relative_to(P)),'bytes':len(data),'sha256':sha(data),'parts':parts})
put('BUILD_CHUNK_RECONSTRUCTION.json',reconstruction)
product=[r['path'] for r in delta['paths'] if r['path'].startswith('frontend/src/')];docs=[r['path'] for r in delta['paths'] if r['path'] not in product]
target=obj(V/'TARGETED_FINAL.json');targetcounts={k:target[k] for k in ['numTotalTests','numPassedTests','numFailedTests','numPendingTests']}
red=obj(E/'writer-attempts/red-01/tests.json');assert red['numFailedTests']==1
controls=(V/'gates/architecture-controls.log').read_text();controlcounts={k:int(re.search(r'# '+k+r' (\d+)',controls).group(1)) for k in ['tests','pass','fail','skipped']}
lint=(V/'gates/lint.log').read_text();lm=re.search(r'(\d+) problems? \((\d+) errors?, (\d+) warnings?\)',lint);lintcounts={'problems':int(lm[1]),'errors':int(lm[2]),'warnings':int(lm[3])} if lm else {'problems':0,'errors':0,'warnings':0}
fields={'TASK':E.name,'LANE':'FRONTEND','FRONTEND_BRANCH':'refs/heads/agent/frontend-wave2-product-ux-v1','BASELINE_IMPLEMENTATION_TREE':delta['baseline_tree'],'FINAL_IMPLEMENTATION_TREE':tree,'PRODUCT_CHANGED_PATHS':product,'DOCUMENTATION_CHANGED_PATHS':docs,'ORIGINAL_FINDING_REPRODUCED':{'result':'YES','red_total':red['numTotalTests'],'red_passed':red['numPassedTests'],'red_failed':1,'original_component_sha256':sha((E/'writer-attempts/red-source/frontend/src/product/render-browser/RenderBrowser.tsx').read_bytes())},'ITEM_LEVEL_METADATA_ACCESS_RESULT':'PASS — inspectable only; denied/unknown/unavailable/stale generic localized placeholders, stale read-refresh guidance','MIXED_COLLECTION_RESULT':'PASS — available collection retains allowed metadata and suppresses restricted item fields','ACCESS_TRANSITION_AND_STALE_RESPONSE_RESULT':'PASS — generation/AbortSignal and keyed source/owner cleanup; no old response restoration','DOM_AND_ACCESSIBILITY_NONDISCLOSURE_RESULT':'PASS — complete serialized artifact DOM attributes/text tested; not OS screenreader or JS-memory confidentiality proof','COLLECTION_LEVEL_REGRESSION_RESULT':'PASS — original and added collection-state cases preserved','TARGETED_TEST_RESULTS':targetcounts,'FULL_TEST_IDENTITY_ACCOUNTING':counts,'REQUIRED_FRONTEND_GATE_RESULTS':{'required':len(gates),'passed':sum(g['exit_code']==0 for g in gates),'commands':gates,'architecture_controls':controlcounts,'lint':lintcounts},'FOCUSED_BROWSER_RESULTS':{'checks':len(checks),'passed':sum(r['passed'] for r in checks),'failed':sum(not r['passed'] for r in checks),'screenshots':len(list(B.glob('*.png'))),'served_files':len(served['files']),'served_hash_differences':0,'http_mutations':traffic['http_mutations'],'assistance':obj(B/'ASSISTANCE.json'),'native_exits':teardown},'BUILD_MANIFEST_SHA256':sha((V/'BUILD_MANIFEST.json').read_bytes()),'BACKEND_REQUIREMENTS_UPDATED':'YES — existing FB-GAP-005; no new requirement ID; real transport/permission contract unestablished','BACKEND_CHANGES':0,'TRACKED_DIST_CHANGES':0,'BACKEND_STATIC_CHANGES':0,'REAL_INTEGRATION_PERFORMED':'NOT_PERFORMED','BOUNDED_PRESERVATION_RESULT':obj(V/'PRESERVATION_FINAL.json'),'HISTORICAL_REPORTS_PRESERVED':'YES','PRODUCT_COMMIT_FREEZE_MERGE_PUSH':'NOT_PERFORMED','PRODUCT_PUBLICATION':'NOT_PERFORMED','EVIDENCE_DELIVERY_STATUS':'LOCAL_VERIFIED_PREPUBLICATION — detached post-publication receipt authoritative','EVIDENCE_COMMIT_SHA':'NOT_ESTABLISHED_AT_PACKAGE_SEAL','REVIEW_INDEX_URL':'REVIEW_INDEX.md','RAW_REVIEW_INDEX_URL':'REVIEW_INDEX.md','MACHINE_INDEX_URL':'REVIEW_INDEX.json','PUBLIC_MANIFEST_SHA256':'Detached receipt; no self-referential digest','REMOTE_VERIFICATION':'PENDING_AT_PACKAGE_SEAL','INDEPENDENT_REVIEW':'REQUIRED','STOP':'YES — after evidence delivery, independent review required; no Workflow UX or EP19/Slice1C/release closure'}
put('REVIEW_INDEX.json',fields)
report=f'''# Render 逐项产物元数据访问修正报告

## 结论与已知边界
修正前，`artifacts.state=available` 下的每个产物仅按 metadataAccess 改变徽标，名称、ID、类型、可用性、版本、taskId 仍无条件进入 DOM。本次真实 RED 以普通测试字符串复现，非真实数据泄露事件认定。

修正后仅 **inspectable** 在既有外层 EffectiveAccess、宿主绑定、上下文、响应身份与显式关系有效时显示上述元数据；**denied / unknown / unavailable** 只输出相应通用说明；**stale** 只输出元数据过期及重新获取 Render 数据的说明。受限项不会把受保护标识转为 title、aria-label、data-*、链接、隐藏 DOM 或可复制字段。React 内部 key 仅用于更新，不序列化到展示 DOM。任务区与允许产物的 taskId 有独立展示依据，不能将其误判为受限项字段展示。

加载刷新先撤除旧 snapshot；取消、错误、陈旧失败不会补齐缓存。外层访问、账户/principal、tenant、session、Project、来源/绑定或 Selection owner 变化通过既有 key/lifetime 卸载清除视图并 abort；generation、AbortSignal 和 live 检查拒绝旧响应恢复内容。读取刷新不是渲染重试。没有预览、下载、外链或 canonical 写入操作。

真实后端授权和响应裁剪仍未建立。当前前端提案解析器可能收到受限字段；DOM 不显示不构成完整保密边界。FB-GAP-005 明确要求后端/适配器按权限裁剪、约定表示形态，并在未来固定版本联调覆盖混合权限和撤权晚到案例。本次未联调、未修改/运行后端或 EP19。

## 实现与证据身份
- 工作分支：`{fields['FRONTEND_BRANCH']}`
- 基线实际实现树：`{delta['baseline_tree']}`
- 最终实际实现树：`{tree}`
- HEAD 与真实 index 保留，未将 HEAD tree 当作工作内容树。1005 个受管路径基线核对无新增漂移。
- [完整 binary-safe 源码补丁](validation/TASK_DELTA.patch)、[逐路径 SHA/模式及分类](validation/SOURCE_DELTA.json)、[独立临时 index 补丁重放](validation/PATCH_REPLAY.json)。before-source/source 保存每个变更端点。

## 测试与七项门禁
原缺陷 RED：{red['numPassedTests']} 通过 / 1 失败，保留六类字段的原始 DOM 失败证据；随后范围内 GREEN 与 stale 文案 RED/GREEN 均保留，不计入最终 PASS 分母。
最终聚焦：{target['numPassedTests']}/{target['numTotalTests']}；全量：{counts['passed']}/{counts['final']}。以 V7 原始 789 个结构化身份逐项对账：保留 {counts['retained']}，新增 {counts['added']}，移除 {counts['removed']}，重复 {counts['duplicates']}，失败 {counts['failures']}，跳过 {counts['skips']}。
V6→V7 的保留748、移除49、新增41为原历史，不改写为所有旧身份均保留。

七项现行门禁 {len(gates)}/{len(gates)}：聚焦测试、typecheck、Lint、架构守卫、架构控制、完整前端测试、外部输出构建。架构控制 {controlcounts['pass']}/{controlcounts['tests']}，Lint {lintcounts['errors']} errors / {lintcounts['warnings']} warnings。原生日志和精确命令在 [validation/gates](validation/gates)，[身份对账](validation/TEST_IDENTITY_ACCOUNTING.json) 含每项保留/新增/移除/重复/失败/跳过及原 reporter。

## 浏览器
最终 Chromium CDP：{len(checks)} 项检查，{len(list(B.glob('*.png')))} 张截图；{len(served['files'])} 个 emitted/served 文件逐字节核对，差异0。EN桌面1440×1000、EN及中文390×844，覆盖混合集合、同ID撤权、stale/unavailable、打开详情后访问/session改变清除、晚到响应、关闭/Escape焦点返回、无产物链接/下载/HTTP写入。
[浏览器检查原始记录](browser-final/NATIVE_CHECKS.json)、[辅助与模拟披露](browser-final/ASSISTANCE.json)、[流量](browser-final/APPLICATION_TRAFFIC.json)、[served census](browser-final/SERVED_ARTIFACTS.json)、[截图索引](SCREENSHOTS.md)。显式隔离 fixture 围绕最终注册路由；普通未配置入口 unavailable。Native CDP输入结合DOM定位/滚动/locale辅助、fixture来源控制与focus emulation；不是物理移动设备、触摸、IME、虚拟键盘或真实屏幕阅读器证明。浏览器晚到源刻意忽略取消，不是后端行为证明。
构建执行现行产品 Vite 配置并显式验证外部 outDir，双入口共享最终源码。准备工具提供的另一个 fixture-host/vite.config.mjs 未执行；不得将其当成实际构建命令。真实命令在 build-final 门禁记录。[截图人工查看记录](browser-final/VISUAL_REVIEW.json) 披露：截图滚动到产物区，标题/关闭按钮位于上方滚动位置；窄屏任务状态会按字换行，标签偏小。本次不宣称持久标题栏或完整移动UX验收。historical missing /vite.svg 可选 favicon 按旧基线保留，不掩盖必要runtime文件缺失。

## 文档、保全与停止边界
既有审查记录追加缺陷和真实中间结果并保留原文，既有 FB-GAP-005 两处明确集合/逐项含义和后端裁剪义务；没有新权威账本或新受管路径，守卫与历史H4债务不变。V7整体接受仍待独立评审，本次不追改旧V7成已覆盖分支。
[保全](validation/PRESERVATION_FINAL.json) 仅覆盖本前端工作区、真实index/HEAD、V7公共历史和指定构建目标；不要求并行后端或全局动态元数据不变。无Task-issued Skill/Memory写入，无产品commit/freeze/merge/push/publication。

证据包为 sanitized 追加发布候选；固定提交匿名回读、manifest核验和JS分块重组由发布后本地 detached 回执报告，不递归发布回执。推送成功不等于远端验证完成。
**INDEPENDENT_REVIEW=REQUIRED。完成证据交付后停止，不启动 Workflow UX，不关闭 EP19、Slice1C 或发布门禁。**

## 机器字段
```json
{json.dumps(fields,ensure_ascii=False,indent=2)}
```
'''
put('FINAL_REVIEW_REPORT_ZH.md',report)
shots=sorted((P/'browser-final').glob('*.png'));put('SCREENSHOTS.md','# 关键截图与完整画廊\n\n显式模拟数据、viewport仿真；非真实后端或物理设备。\n\n'+'\n\n'.join(f'## {p.stem}\n![{p.stem}](browser-final/{p.name})' for p in shots))
put('REVIEW_INDEX.md',f'''# {E.name}

状态：修正和最终工程/浏览器验证已完成；独立评审 REQUIRED。产品未提交/冻结/合并/发布。V7历史审查整体接受不追改。

- [中文完整报告](FINAL_REVIEW_REPORT_ZH.md)
- [机器索引](REVIEW_INDEX.json)
- [完整源码 diff](validation/TASK_DELTA.patch)
- [变更路径与before/final哈希](validation/SOURCE_DELTA.json)
- [逐项测试身份对账](validation/TEST_IDENTITY_ACCOUNTING.json)
- [七项门禁原始命令](validation/FINAL_VALIDATION_PLAN.json)
- [构建 manifest](validation/BUILD_MANIFEST.json)
- [浏览器检查](browser-final/NATIVE_CHECKS.json)
- [截图](SCREENSHOTS.md)
- [JS分块重组](BUILD_CHUNK_RECONSTRUCTION.json)
- [包manifest](MANIFEST.sha256)

最终实际实现树 `{tree}`。后端/静态产物改动0，真实联调未执行。模拟、DOM辅助、焦点与viewport仿真及未测试范围详见完整报告。发布时身份与匿名回读结果在 detached 本地回执，不放置自引用摘要。
''')
# No credentials, raw environment or unrelated inventories are published.
patterns=[rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{40,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
files={str(p.relative_to(P)):p.read_bytes() for p in P.rglob('*') if p.is_file()}
for n,b in files.items():
 assert not any(re.search(pattern,b) for pattern in patterns), 'credential-shaped payload '+n
put('SANITIZATION.json',{'files_scanned':len(files),'credential_shaped_findings':0,'scope':'Known credential shapes; ordinary test strings retained; no runtime JS-memory secrecy claim. Unscoped writer whole-repository maps and profile files omitted.'})
files={str(p.relative_to(P)):p.read_bytes() for p in P.rglob('*') if p.is_file()}
manifest=''.join(sha(files[n])+'  '+n+'\n' for n in sorted(files,key=lambda n:n.encode()));put('MANIFEST.sha256',manifest)
files['MANIFEST.sha256']=manifest.encode();archive=E/'LOCAL_REVIEW_PACKAGE.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for n in sorted(files):z.writestr(n,files[n])
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(files) and len(z.namelist())==len(files)
 for n,data in files.items():assert z.read(n)==data
verification={'manifest_sha256':sha(manifest.encode()),'archive_sha256':sha(archive.read_bytes()),'archive_entries':len(files),'manifest_entries':len(files)-1,'full_local_bytes_verified':True,'build_manifest_sha256':sha((V/'BUILD_MANIFEST.json').read_bytes()),'final_tree':tree}
(E/'LOCAL_PACKAGE_VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n')
(E/'LOCAL_RESULT_FIELDS.json').write_text(json.dumps(fields,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(verification,indent=2))
