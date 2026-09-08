# Parent：完整 capsule、准备、preflight 与一次性29-gate启动

这些命令未在本 continuation 执行。它们只写入本 continuation 的新 run namespace；不修改 canonical candidate、历史目录、共享配置、Skills 或 Memory。失败 namespace 不删除、不刷新 baseline、不重试。

```bash
cd /home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/run-output-completeness-20260907T143346Z/bookkeeping-v2-20260908T004809Z
export EP19_V2_ROOT="$PWD"
export EP19_V2_RUN_ID="bookkeeping-v2-formal-001"
export EP19_V2_RUN="$EP19_V2_ROOT/outputs/continuation-runs/$EP19_V2_RUN_ID"
test ! -e "$EP19_V2_RUN"
```

先只读验证 fresh qualification、formal-boundary component reuse 与新 executor identity：

```bash
PYTHONPATH="$EP19_V2_ROOT/executor" python3 -B - <<'PY'
import json
from pathlib import Path
import coverage, runner
q=Path('qualification/QUALIFICATION.json').resolve()
document=json.loads(q.read_text())
assert len(coverage.qualification_inputs(q)) > 0
assert coverage.formal_boundary_qualified(document)
assert document['result']=='PASS' and document['tests']==129
print(runner.verify_executor_identity()['identity'])
PY
```

准备三个彼此独立且从固定 backend candidate 本地复制的 checkout。此步会在新 namespace 内进行非 canonical Git clone/checkout；不要对 TASK_ROOT candidate 或历史目录执行任何 Git 写操作：

```bash
python3 -B executor/runner.py prepare \
  --run-id "$EP19_V2_RUN_ID" \
  --qualification "$EP19_V2_ROOT/qualification/QUALIFICATION.json"
```

在 baseline 前仅把已核验 Lean distribution 复制到 run-local cache。不得加入第二个 Gradle init script：

```bash
export EP19_LEAN_SOURCE="/home/user/Documents/workspace/audit-runs/EP19_H7_PRODUCTION_INPUT_BOUNDARY_CORRECTION_AND_PACK_MONITOR_QUALIFICATION_V1/formal-tools/lean-4.19.0-linux"
test "$(sha256sum "$EP19_LEAN_SOURCE/bin/lean" | awk '{print $1}')" = "92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023"
mkdir -p "$EP19_V2_RUN/runtime/cache/backend/formal-tools"
cp -a -- "$EP19_LEAN_SOURCE" "$EP19_V2_RUN/runtime/cache/backend/formal-tools/lean-4.19.0-linux"
test "$(sha256sum "$EP19_V2_RUN/runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean" | awk '{print $1}')" = "92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023"
test "$(find "$EP19_V2_RUN/runtime/cache/backend/gradle/init.d" -maxdepth 1 -type f -printf '%f\n')" = "ep19-packaging.gradle"
```

历史 full capsule 仅按逐组件适用性复用：A/B/C 的 exact unchanged helpers、`execution.py` 中 `exact`/`frontend_sandbox`/`formal_sandbox` 的 AST 等价、实际 Gradle/frontend/Lean/formal 原生日志与回执，以及 parent-runtime-completion-3 的10份 formal receipt/log 均已单独绑定。启动前仍做当前端点的只读可用性检查；若 permission/socket/image 检查失败，保留错误并停止，不改权限、不切换 profile、不绕路：

```bash
test -x /usr/bin/bwrap
test -x /usr/bin/podman
test -S /run/user/1000/podman/podman.sock
XDG_RUNTIME_DIR=/run/user/1000 CONTAINER_HOST=unix:///run/user/1000/podman/podman.sock \
  podman image inspect docker.io/coqorg/coq@sha256:e50d77c4c5a9aa0d76ae1b343d79c5f922da3a75054b79c5dc635895438e4674 \
  --format '{{.Id}}' | grep -Fx b80d66c91b4da3a1b3c5d3e6672cf8f4ab72ed2f7a6a1f0cf7d3aef747cf6a4b
```

创建一次性的 prospective private policy、eligible IDs/pointers/schema、baseline 与 seal；随后执行完整 preflight：

```bash
python3 -B executor/runner.py baseline --run-id "$EP19_V2_RUN_ID"
python3 -B executor/runner.py preflight --run-id "$EP19_V2_RUN_ID"
```

仅当 preflight 的 `result=ENGINEERING_READY` 且 blockers 为空时，从实际字节创建 launch receipt。保持 independent review=PENDING，不伪造 ACCEPT：

```bash
PYTHONPATH="$EP19_V2_ROOT/executor" python3 -B - <<'PY'
from pathlib import Path
import runner
run=runner.runpath('bookkeeping-v2-formal-001')
p=runner.load(run/'preflight.json')
assert p['result']=='ENGINEERING_READY' and p['engineering_blockers']==[]
executor=runner.verify_executor_identity()
q=Path(runner.load(run/'prepare.json')['qualification'])
policy=run/'bookkeeping-policy-v2.private.json'
receipt={'run_id':run.name,'candidate':runner.SHA,'tree':runner.TREE,'base':runner.BASE,
 'engineering_execution_authorization':'OWNER_AUTHORIZED',
 'owner_decision_sha256':runner.OWNER_SHA256,'owner_contract_version':runner.OWNER_CONTRACT_VERSION,
 'executor_identity':executor['identity'],'bookkeeping_policy_sha256':runner.coverage.digest(policy),
 'qualification_sha256':runner.coverage.digest(q),'independent_review':'PENDING',**runner.REVIEW_STATES,
 'seal_sha256':runner.coverage.digest(run/'seal.json'),'preflight_sha256':runner.coverage.digest(run/'preflight.json')}
runner.put(run/'engineering-launch.json',receipt)
PY
python3 -B executor/runner.py run \
  --run-id "$EP19_V2_RUN_ID" \
  --review "$EP19_V2_RUN/engineering-launch.json"
```

最后一条命令在 current technical preflight 与 PRESTART V2 比较都通过后才写 `runtime/START.json`，随后自动运行固定29-gate graph。任一 required gate、严格保护、capture、evidence-write 或 binding 失败都会停止依赖 gate 并记录剩余 `NOT_RUN`；同一已启动 namespace 禁止重试。成功也不构成产品发布或 EP19 关闭。
