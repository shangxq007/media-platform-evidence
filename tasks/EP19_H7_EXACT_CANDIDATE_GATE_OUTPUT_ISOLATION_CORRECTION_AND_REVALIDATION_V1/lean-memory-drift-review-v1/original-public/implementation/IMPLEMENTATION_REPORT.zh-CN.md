# Lean 工具链物化纠正与重新准备报告

本 continuation 已完成边界内准备，未创建 formal baseline、seal、preflight 或 `runtime/START.json`，也未执行任何正式 product gate/graph。

固定候选仍为 commit `689ab9456461a8d19a72d059f5157092efc43aff`、tree `6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6`、base `86d6aef94fd5e58da552e97c11473cff6eca734e`。三个 run-local checkout（backend、candidate-frontend、SHADOW）均从固定 backend candidate 用原算法独立复制；没有 alternates、共享 Git metadata 或共享 object inode。未读取、运行或要求 `refs/heads/agent/frontend-wave2-product-ux-v1` 静止。

## Lean 纠正结果

选用历史已物化源 `owner-clarified-execution-20260907T1120Z/prepared-tools/lean-4.19.0-linux`。历史 `4617` 的计数方法已恢复：只统计 manifest 的逻辑文件路径，不含 root 和目录。当前源与历史 4617 条路径/摘要逐项一致；完整当前检查记录 4617 个 regular files、449 个目录（包含 root）、0 symlink、0 special、0 inode alias。模式、uid/gid、权限、长度与摘要均已记录并与 raw pinned tree 对照。

raw tree 没有以“已知 12 条”为枚举假设；代码先枚举所有当前 link，再逐 component 解析链，拒绝 cycle、missing、outside、special。实际发现 12 条且全部在 root 内解析为 regular file，包含 `libc++abi.so -> libc++abi.so.1 -> libc++abi.so.1.0` 与 `libunwind.so -> libunwind.so.1 -> libunwind.so.1.0` 两级链。raw 的全 membership/hash/mode/ownership 与 preferred source 一致。

实际 run-local destination 以逐文件 read/write 创建独立 regular files并逐项恢复 mode，没有 blind follow 或 broad chmod。复制后再次验证 4617 files、449 directories、0 symlink、0 special、0 alias，并确认 preferred/raw/destination 三组交叉 shared inode 均为 0。root 与全部 ancestor 必须解析为原路径；外部 hardlink 也会因 `nlink != 1` 拒绝。未弱化 `preservation.Collector`；其 module SHA256 仍为 `cfdc63fde7be1a5d3634d9425e35198ec3f9c4060b1d09197e3ad9e2c48f87a7`。最终 helper revalidation 使用同一 strict Collector 捕获完整工具输入集合：4617 个 Lean 文件、1 个 Gradle init 输入及 baseline 同方法解析出的 9 个 unique runtime binaries，共 `COMPLETE/4627`。早期 Lean-only preparation receipt 被该最终 revalidation 明确补充，不作为 full strict set 的最终声明。

真实 Lean preparation probe 使用绝对 run-local binary、显式 `LEAN_PATH` 和 `LD_LIBRARY_PATH`，在原 formal sandbox 算法内完成 `--version`、`--print-prefix`、`import Lean` + theorem compile/proof，native exits 为 0/0/0；prefix 精确指向 run-local distribution，没有 system Lean fallback。该 probe 不是 candidate FORMAL gate。

## 资格与保留边界

affected-only fresh qualification 为 19 PASS / 0 FAIL / 0 ERROR / 0 SKIP，19 unique、0 duplicate。历史 V2 129 controls 仅按原 receipt、dependency hashes、formal/full-capsule applicability 复用，不称为 fresh 129。A/B/C helper bytes、`exact`/`frontend_sandbox`/`formal_sandbox` AST、V2 四字段 policy、actual-decision capture、OLD_STRICT 独立诊断与 strict Collector 均保留。native probe 的异常、timeout 或 nonzero 路径会在抛错前先写 process receipt。

历史 V2 `STOP_INCOMPLETE_STRICT_INPUT_CAPTURE`、29 NOT_RUN 及所有更早 5/1/23、ARCHITECTURE、FAIL_PRESERVATION、command-gap drift、unknown writer/missing coverage 与 `PACK_HISTORICAL_BYTE_IMMUTABILITY=NOT_RECOVERABLE` 保持原判，未回溯重分类。

新 executor identity 为 `e4631b979d1b96dd40f852011d450878876838266710e4413241ab6b720e374c`；independent review 保持 `PENDING`。Parent 的本地 authority verification 与此前 fresh anonymous remote verification 回执已按原字节复制并绑定；它们验证的是此前证据 commit `5c1ffa64115707affc0628523c710855f3625bb2`，不伪装为本 continuation 的发布结果。Hermes 的只读审查和一次性 baseline→seal→preflight→conditional launch 命令见 `PARENT_COMMANDS.md`。post-run finalizer 会产生中文报告、机器字段与逐文件 hash 验证的 sanitized public package；它不会发布产品或证据，不包含私有 Skill/Memory 正文、私有 policy 或凭据。
