# r11 prepare AttributeError：最终静态诊断

## 结论

**已定位源码支持、与实际错误摘要一致的首个故障点：`identity_delta.validate()` 调用不存在的 `binding_contract.path`，发生在 run namespace 创建之前。不是 argparse Namespace 字段缺失，也不是 `runner.prepare` 参数签名不匹配。**

同时发现直接相关的第二层契约错配：当前 binding 的 `reviewed_delta` 是外部执行器 r10→r11 文本 patch，但遗留产品身份校验器把它当作 `ep19-cleanup-identity-delta-v1` JSON 产品来源证据。仅补 `path` 别名不足以闭合准备路径。

J 为本 continuation；以下 E=J/implementation-r11/tooling/executor，W=J/writer-evidence-r11。源码行号以本次静态读取的原 r11 为准。读取的关键源码均与指定 binding 中 source_binding 的对应摘要相符，逐文件值见 STATIC_SOURCE_HASHES.json。

## 证据边界与历史事实

- Parent 提供的实际进程：proc_f7a8bc56f5cf，prepare 退出 1，结构化 AttributeError，reason 未公开；摘要 `97863e69ab6779d2ba89485b262716ae8d167eca604f7e3536880eff0c10a790`。
- Parent 提供的现场读取：`implementation-r11/tooling/outputs/continuation-runs/candidate-formal-002` ABSENT，全部 formal markers ABSENT；formal 未调用，正式预算仍 1/2。本子代理没有重放或独立重新采集这些现场事实。
- 本次实际做了源文件读取、stdlib AST 解析和静态 SHA-256；没有导入/执行被审代码，没有运行 loader、test、prepare、probe、baseline、formal 或产品命令；没有读取共享 ledger/usage/credentials 或绑定的 private map/inventory 正文。
- 写入只在 J/preparation-failure-r11/。没有修改实现、共享 Skill/Memory、历史回执、readiness 清单或绑定。不把静态诊断称为 RED/GREEN、成功 preparation 或独立最终接受。

## 1. 入口到首次 namespace 创建的可达链

| 次序 | 源码 | 实际字段/属性与行为 |
|---|---|---|
| 1 | E/external29_driver.py:837–851 | parser() 注册 command、run_id、binding(Path)、binding_sha256；_dispatch_main 读取 args.command 后走 preparation(args)。prepare 不需要 input/review/qualification Namespace 属性。 |
| 2 | E/external29_driver.py:28–41,813–814 | args.binding / args.binding_sha256 传入 modules；configure 使用 Path.absolute、read_bytes、hashlib.sha256/hexdigest，并设置 os.environ 两项；binding_contract.from_environment 获得 config；导入 coverage、runner、sequence。 |
| 3 | E/binding_contract.py:23–71 | from_environment/load 使用 exact_path、digest/read/require、os.environ.get、Path 路径/文件属性、re.fullmatch、dict/item 集合及 dependency_contract.validate，校验绑定并返回 run_ids。此处没有调用 identity_delta.validate；reviewed_delta 仅检查 path/sha256 字段与字节摘要。 |
| 4 | E/runner.py:6–26,45–50；E/execution.py:4–10 | 导入中 CONFIG 来自同一绑定；runpath(args.run_id) 用 re.fullmatch、binding_contract.from_environment()['run_ids']、p.resolve 校验，返回 Path。源码并非把 argparse Namespace 当作路径。导入期错误在理论上可能更早，但找到的摘要对应的是后续具体缺失属性，而非导入期常量。 |
| 5 | E/external29_driver.py:815–816；E/runner.py:69–70 | 设置 H7_RUN_ID；args.command=='prepare' 调用 runner.prepare(run, Path(config['qualification']))。定义是 prepare(run, qualification=None)，签名完全匹配。首先读取 coverage.qualification_inputs。 |
| 6 | E/coverage.py:115–188 | 当前 q.schema 是 ep19-external29-integration-qualified-v2，执行 q.get、Path/read_text、json.loads、D.rglob/Path过滤、dict/dependencies、check_seal、qualification_contract.REQUIRED_AFFECTED_CONTROLS/validate、sys.executable、process argv/原生日志身份等现有资格校验；成功后在188返回。不会进入189及其后的 legacy extension。 |
| 7 | E/runner.py:71；E/execution.py:12–20 | __import__('execution').verify_object_source()；Path.resolve、git(...).decode/strip/split 校验 tree/parent/base；导入 identity_delta；取 CONFIG['reviewed_delta']['path'/'sha256'] 调用 identity_delta.validate。这些 Git 调用属于原源码路径，本次没有执行它们。 |
| 8 | E/identity_delta.py:105–106 | 函数第一条语句为 p=bc.path(str(evidence))。bc 来源于第7行 import binding_contract as bc；模块没有 path 导出，因此这里立即 AttributeError，后续 digest/read/schema/git/产品证据读取均尚未开始。 |
| 9（未到达） | E/runner.py:72–73 | run.exists() 后 durability.ensure_directory(run,0o700) 才第一次创建 run namespace。第74行之后 runtime 子目录与 namespaces.prepare/parser_tools/Lean 准备均不可能先于第71行完成。 |

所选入口及前创建函数的逐行 AST 属性清单另存 STATIC_AST_FINDINGS.json。清单是词法属性枚举，不是动态 trace；其中 coverage 包含未选 fallback 分支，必须按上表 schema 路由解释。未声称穷举第三方/stdlib 内部所有潜在 AttributeError。对本故障的判断来自缺失模块导出、顺序和绑定 schema，而不是将“所有其他代码都不会失败”当作假设事实。

## 2. 缺失 API 与摘要核对

E/binding_contract.py 全文1–78行提供 `exact_path(value)`（23–26），未定义/导入/赋值 `path`，也没有模块级 __getattr__。AST 顶层导出集及所有 `bc` 属性缺项已保存。

源码推导的 Python 错误文本（UTF-8，无换行）：

```
module 'binding_contract' has no attribute 'path'
```

实际静态计算的 SHA-256：

```
97863e69ab6779d2ba89485b262716ae8d167eca604f7e3536880eff0c10a790
```

与 Parent 给定摘要完全一致。E/causal.py:223–235 从 reason.encode() 生成此类摘要，并明确 reason_exposed=false。

**不确定性说明：** 摘要不能代替原始 traceback，也不能单独定位同一文本的多个调用点。本源码有四个同文本候选：identity_delta.py:61、106；binding_qualification.py:41、45。当前资格 schema 在 coverage.py:188 返回，排除该次 prepare 的 legacy binding_qualification 路径；identity_delta.validate 的106行先于 artifact 的61行调用。因此106行是当前路径中首个可达的匹配故障。结论为“源码与现场摘要一致的高置信根因”，不是宣称拿到了被隐藏的原生堆栈。没有制造异常、导入模块或运行 loader 来取得这个文本。

## 3. 第二层错配：同名 reviewed_delta 已更换含义

- W/RUNTIME_BINDING.candidate-formal-002.r11.final-002.json:55–60 绑定集成资格和 reviewed_delta；绑定实际摘要核对为 `2c0bd9206991c35dd46215f040c627a46079864eeb8a8825e06132a93ff4be9a`。
- reviewed_delta.path 指向 W/IMPLEMENTATION.r10-to-r11.final-002.patch，其第1行是 `diff -ruN ...`，是外部实现差异，不是 JSON。
- E/binding_contract.py:62–65 只核对这个差异文件的 schema形状/path/hash 和实现 source_binding；对“外部实现 patch”的绑定在此可成立。
- E/execution.py:18–20 却仍把同一值交给旧的产品来源验证器。
- E/identity_delta.py:106–108 要 bc.read(JSON)，schema 固定为 ep19-cleanup-identity-delta-v1；107行还要求 trees、parent_diff、canonical_diff、sources、junit 等产品身份字段。

所以只把 bc.path 改为 exact_path，后续将尝试 JSON 解析 diff 文本；这是静态确定的输入类型不兼容，**没有实际执行或报告第二次错误**。修正必须明确区分外部执行器实现差异证据与固定产品身份/测试差异来源证据，保留原来的候选 tree/parent/base/patch、来源及身份校验强度，不能以删除 identity_delta.validate 或直接 return True 作为修复。

其他静态遗留缺项是 binding_qualification.py:52 的 bc.authority 和 identity_delta.py:169 的 bc.OLD_TREE；它们不在本次首次失败位置，不应混称已发生故障。受影响调用链复核应识别其是否仍可达，避免只修一个 AttributeError 后直接正式启动。

## 4. 精确资格缺口及 readiness 更正

**缺口：真实 CLI prepare → runner.prepare → execution.verify_object_source → identity_delta.validate 与当前 runtime binding 的消费者集成未获覆盖。** 这是 Owner 授权第三组 AR007 实际消费者/依赖绑定，以及受影响调用链/真实外层入口资格的遗漏，不是证明现有全部观察器、诊断持久化或29 gate实现失效。

1. W/validate_runtime_binding_r11.py:17–33 读取 binding、coverage.qualification_inputs、dependency.validate，检查 required_runtime_files，再做独立 Git HEAD/tree/parent/patch/status 核对。**没有调用 runner.prepare、execution.verify_object_source 或 identity_delta.validate。** W/runtime-loader-final-002/NATIVE.log:1 保存 PASS 且 formal_namespace_created=false/shared_preparation=false。保留它为窄范围真实 loader PASS，不改写为 CLI准备 PASS，也不反向说它是伪造结果。
2. tooling/qualification/test_external29_integration.py:14–22 运行的是 fixture 子命令或 --help；E/external29_driver.py:744–745 明说 fixture 从不导入产品 runner。它证明真实进程/observer fixture路径，不证明 prepare integration。
3. tooling/qualification/build_integration_qualification.py:33–36 只 discovery qualification/test_*.py 并核对 REQUIRED_AFFECTED_CONTROLS；68–79产出集成资格并明确 formal_preparation=false。E/qualification_contract.py:4–98 必需集合没有当前 prepare API/输入含义的控制身份。已有身份总数闭合不等于这个缺失 seam 已被测试。
4. J/preparation-readiness-r11/OPERATIONAL_CHECKLIST.zh-CN.md:7、99 的“剩余仅 parent记录/实际回执、无需实现修复”判断需追加更正：静态文件/hash完整确实不解决接口和证据语义不兼容；46行 prepare摘要漏掉了69–71行前创建验证调用。该清单的边界声明与消费规则保留，不能把本次发现回填为它已经发现。
5. W/PARENT_HANDOFF_COMMANDS.r11.final-002.md:1、7、19明确 writer 未执行真实 prepare。今后的 handoff 应以私有准确入口资格支撑，而不是重新解释旧 PASS 为更宽保证。

## 5. 连续授权修正建议（本次未实施）

Owner OWNER_AUTHORIZATION.verbatim.txt:12–14、65–75、234–246 已授权范围内外部实现及必要直接调用点修正、私有合成 fixture、受影响回归与复核；不因阶段报告再次请求同范围 Owner 授权。261–279仍要求真实资格/依赖/绑定/准备全部闭合，consume记账不可按 START 判断。

建议 Parent 启动新外部版本，保留原 r11、失败 stderr/进程事实、已有资格和本报告：

- 先修复前创建消费者 API 和 reviewed_delta 双重语义，明确固定产品证据来源，不改产品候选或批准契约，不弱化 path/hash/identity 检查。
- 在任务私有隔离 fixture 中增加**同一解释器、同一 prepare 子命令/参数形状、真实 parser→modules→runpath→runner.prepare→verify_object_source→身份消费者**的 RED/GREEN；只能通过显式 fixture路径映射将所有读写限制到任务私域。不得把 modules/runner.prepare/verify_object_source stub 成成功而声称覆盖本缺陷，不读取共享私有树或消耗真实 candidate-formal-002 namespace。
- 负控覆盖缺失 API、外部 patch错当产品JSON、正确路径但错误schema/hash、固定候选身份错误、已有 namespace拒绝；确认拒绝发生在新 namespace 创建前。正控必须实际跨过修正后的前创建链并回读私有准备产物，且 formal markers及产品gate调用始终为零。完整准备还涉及clone/parser/Lean，应分清哪些环节真实覆盖、哪些外部fixture边界替代，不扩大宣称。
- 新测试加入必需身份集合；重新运行受影响资格、依赖/来源/消费者绑定和限定独立复核，保留未受影响历史适用范围。修正后的 source/binding/qualification/consumer hashes 必须重新一致，不把 r11结果追认成新版运行结果。
- 修正后的 parent readiness 才考虑是否按既有规则进行真正 prepare；本报告不提供或授权重放失败命令。formal仍待全部既有条件，不能把“目录不存在”普遍当作预算返还规则。

本子代理没有消费任何正式预算。实际 formal 未调用、run/markers不存在和预算1/2仍以 Parent 提供观察为依据；本次是前 namespace 的外部准备失败，不是第二次正式 baseline 失败，也不改变历史 candidate-formal-001结果。

## 交付文件

本目录保存 EARLY_STATIC_REPORT.md、EARLY_ROOT_CAUSE.md、FINAL_STATIC_REPORT.zh-CN.md、STATIC_AST_FINDINGS.json、STATIC_SOURCE_HASHES.json。前两份作为调查过程早期证据保留，不覆盖。未另写共享 Skill，遵守本任务限定写域。
