# 脱敏、来源与复核边界

这是仅本地待父任务审查的 evidence-only 衍生候选，不是已发布包，也不是可启动正式任务的分发器。未联网、未访问凭据、未执行测试/probe/collector/prepare/formal。仅写本delivery-candidate；不修改产品、共享Skill/Memory、私有原件或原权威账本。

## 精确白名单与字节关系
- SOURCE_ALLOWLIST.json 在复制前冻结具体源文件，随后仅显式追加独立最终失败审查与loader源码；不按whole-directory复制。
- SOURCE_PROVENANCE.json 每个文件保存原始SHA256/字节数、候选路径与衍生SHA256/字节数。PACKAGE_ALLOWLIST.json 是实际允许交付文件全集；MANIFEST.sha256校验载荷；LOCAL_RECEIPT.json作非循环本地摘要回执。
- 路径文本中本continuation绝对根替换为J，其父任务根为TASK_ROOT，用户home替换为USER_HOME。替换覆盖源码常量、日志、JSON值及键，因此公开源未必可直接运行，也不能用公开文件hash冒充原始执行源hash。
- JSON采用可读缩进重序列化；已有内嵌hash仍指向历史原件，必须通过SOURCE_PROVENANCE映射到脱敏副本。未对旧manifest声称脱敏后仍有效。本地最终manifest只校验此包字节。
- 不复制Owner指令正文；保存自写归纳、来源编号、必要身份摘要及历史公开目录定位。源码中的合成fixture字符串属于测试代码，不是共享真实ledger/usage/指令正文。
- 没有复制Owner原文、任务指令packet、closure-recovery的SOURCE_EXCERPTS、private-r12或其他private目录、真实共享ledger/usage、共享Skill正文、私有清单及指令inventory。独立review只包含必要两条路径/hash摘要，不含内容；此子任务不读取这些共享源文件。

## 有界复核而非运行复现
可核对29门NOT_RUN、qualification身份集合、原生资格日志/结果/进程回执、拒绝谓词及调用者源码、绑定/identity/准备边界、r1-r12报告和失败历史。不得运行本包中的历史执行命令：预算已2/2且没有新授权。
旧r1-r11源码完整树、巨型fixtures、Lean完整运行文件、clone对象库、容器镜像和部分巨大准备collector均不复制；OMITTED_EVIDENCE记录明确文件hash/大小或保存manifest行数，绝不把多revision manifest行数相加冒充唯一文件数。定位J/...可供父任务在已有本地证据中只读查找；这些是本地locator，不假称GitHub可下载或匿名可回读。
HISTORY_R1_R12按12个revision机械聚合报告/矩阵/实际RESULT。旧PASS不标为后继源fresh；RED、失败资格、superseded runs、r11准备失败保留。EARLY_INDEX是打包早期快照，最终事实以FINAL_MACHINE_INDEX为准。
完整后端8000/29只为EXPECTED，实际未执行；unknown discovery/missing等为null，不伪造0缺失。

## 历史公开锚点（本子任务未联网重验）
前序公开证据提交 `a7e2e8de1195ff1dbec75a91d3e7c73d726355d7`，历史manifest摘要 `98d8afbaa2dac1e1d09358594b18584a92675e214b24bfe2b9d2abb0caba4119`。
https://github.com/shangxq007/media-platform-evidence/tree/a7e2e8de1195ff1dbec75a91d3e7c73d726355d7/tasks/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/continuations/approved-bookkeeping-conformance-003/
该锚点只用于旧符合性/first-formal历史，不含本次r1-r12或second-formal，也不替代本次发布后的固定提交匿名逐字节核验。当前候选URL/提交尚为空。
