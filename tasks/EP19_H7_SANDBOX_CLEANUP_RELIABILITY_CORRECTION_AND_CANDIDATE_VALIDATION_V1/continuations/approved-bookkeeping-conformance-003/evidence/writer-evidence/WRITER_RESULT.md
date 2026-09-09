# Writer 实施与资格结果

结论：Owner 批准的 A/B/C 三组差异已在新的外部 `tooling/` 中实现，当前源码绑定资格为 **GREEN 71/0/0/71，重复 0，复用 0**。Writer 没有修改产品、没有运行产品测试，也没有执行 preparation、真实 baseline、preflight、gate 或第二次正式尝试。

## 已落实内容

- A：仅 exact `.usage.json.lock` 的既存空 regular/nlink=1、九字段及空内容完全相同、`mask==8,cookie==0` 进入 PENDING；在同一边界按实际 capture 裁决。modify、组合/未知 mask、非零 cookie、非空、mode/inode 替换均拒绝。事件始终保留，writer 身份仍为 `NOT_ESTABLISHED`。
- B：usage 由单次同 FD `stat/read/stat` 与 path stat 的真实字节同时生成 hash、metadata、解析值、source ID、capture ID。baseline 使用五条件组合接受；合法四字段变化可以在 `OLD_STRICT_REJECT` 事实保留时通过。成员、字段、类型、严格值、倒退、非法 UTF-8/重复 key、缺失/不稳定或 capture binding 不一致继续拒绝。
- C：ledger 仅接受既存同 inode 的前缀增长，逐边界同时验证 original 与 previous prefix。新增记录严格八字段，只允许 `patch|edit`、`evidence={}`、预绑定单包完整非空且 before/after 深相等 manifest。重复 ID/key、跨包路径、半行、非法编码/时间/schema、缩短、替换、组合事件及无覆盖增长拒绝。
- 同一个 `Engine` 被 `RunAdapter` 的 baseline、preflight、prestart、command、gate、final、coverage、seal 八个入口复用，不存在仅 baseline 特判。
- 失败 namespace 在 baseline 前即 exclusive consume；失败后不能重建 baseline、不能进入 preflight，也不能由新 adapter 复活。
- ledger 只绑定为 `OBSERVATION_INTEGRITY_ONLY`；固定 29 项静态 closure 中 command argv ledger 引用为 0、绑定源码 token 引用为 0、动态 reader 为 0。此结论不扩展到任意未来 plugin/reader。

## RED / GREEN

预实现 RED 在 immutable V2 源上新鲜执行 4 项，实际 4 FAIL：缺少同源 capture API、ledger validator、五条件 baseline acceptance，且 exact lock close 被归类为 `REJECT_INSTRUCTION_EVENT`。原始 RED 已保留。

当前 GREEN 为 `writer-evidence/green-009`：71 个 fresh control、71 unique、0 repeated、0 failure、0 error、0 skip，native exit 0。覆盖真实 disposable filesystem 与 inotify，包括合法 usage、空 lock close、ledger 单/多行、previous prefix、128 条实际边界；负例覆盖 129 条、prefix/inode/size/schema/key/ID/path/manifest、pending/半行、严格正文 write-restore、watch loss/overflow、capture missing/unstable/mismatch、evidence write failure、stale policy/binding、failed namespace。

中间 `green-001..003/005..008` 虽各自 PASS，但源码随后变化，均不作为当前资格；`green-004` 在 69 项 control 全过后因 diff builder 的 generator 切片 TypeError 失败，失败 namespace 和原因已保留，未改写。最终 current binding 只指向 `green-009`。

未复用旧 158 项或 13 项封包结果，也未重复任何产品稳定性测试。旧 H7 33、第一次 29/0/0/29 baseline 失败和 candidate-formal-001 均保持原状。

## 候选与依赖绑定

只读核对得到 candidate SHA `a29864343ed4f630b052c20d86c23b240f13cfd0`、tree `fd37409d0274662abbe86f69e3d963c05b379696`、parent `689ab9456461a8d19a72d059f5157092efc43aff`；parent→candidate binary patch SHA256 为 `bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`。产品 tracked status 无输出；continuation 产品行为变化为 NO。

Parent dependency applicability 显示实际 ledger 6,362,601 bytes、600 行、600 unique ID、0 parse error，低于 64MiB；七个候选包全部 eligible，private map 与 strict inventory 均按摘要绑定。它是 applicability，不是正式 baseline。

当前 executor identity 为 `fdd412063a59cd78c75481347c4751fdffbfcbe7315a58c0223266dd918d1bcd`。最终 candidate binding 为 `CANDIDATE_BINDING_CURRENT.json`；旧 `CANDIDATE_BINDING.json` 与 `CANDIDATE_BINDING_FINAL.json` 因之后源码变化仅保留历史，不是当前 binding。

## 证据限制与交接状态

明确接受的观察限制保留：普通 inotify 加覆盖点 prefix/hash 无法证明两次捕获之间从未发生 overwrite-restore 或 truncate-regrow；资格没有伪造“可检测”通过项。actor 不证明 writer。私有真实共享 raw bytes 没有由 writer 读取或复制；parent applicability 只以摘要和计数消费。

Writer 的实现、资格和候选绑定已完成，但第二次正式尝试当前仍不是 launch-ready：Parent 还需独立评审、把 `RunAdapter`/observer 接入同一长生命周期的新 external gate driver、完成 fresh preparation/private baseline/seal/preflight。旧 runner 未被冒充为已适配。精确顺序与命令见 `PARENT_COMMANDS.md`。

最终状态：`INDEPENDENT_REVIEW=REQUIRED`，`EP19_CLOSED=NO_PENDING_INDEPENDENT_REVIEW`，`PRODUCT_PUBLICATION=NOT_PERFORMED`，`POST_PUBLICATION_SANITY=NOT_RUN`，writer 停止于批准的实施、定向资格与 handoff 边界。
