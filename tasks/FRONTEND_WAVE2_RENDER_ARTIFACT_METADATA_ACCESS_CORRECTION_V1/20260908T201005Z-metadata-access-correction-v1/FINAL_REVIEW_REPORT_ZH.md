# Render 逐项产物元数据访问修正报告

## 结论与已知边界
修正前，`artifacts.state=available` 下的每个产物仅按 metadataAccess 改变徽标，名称、ID、类型、可用性、版本、taskId 仍无条件进入 DOM。本次真实 RED 以普通测试字符串复现，非真实数据泄露事件认定。

修正后仅 **inspectable** 在既有外层 EffectiveAccess、宿主绑定、上下文、响应身份与显式关系有效时显示上述元数据；**denied / unknown / unavailable** 只输出相应通用说明；**stale** 只输出元数据过期及重新获取 Render 数据的说明。受限项不会把受保护标识转为 title、aria-label、data-*、链接、隐藏 DOM 或可复制字段。React 内部 key 仅用于更新，不序列化到展示 DOM。任务区与允许产物的 taskId 有独立展示依据，不能将其误判为受限项字段展示。

加载刷新先撤除旧 snapshot；取消、错误、陈旧失败不会补齐缓存。外层访问、账户/principal、tenant、session、Project、来源/绑定或 Selection owner 变化通过既有 key/lifetime 卸载清除视图并 abort；generation、AbortSignal 和 live 检查拒绝旧响应恢复内容。读取刷新不是渲染重试。没有预览、下载、外链或 canonical 写入操作。

真实后端授权和响应裁剪仍未建立。当前前端提案解析器可能收到受限字段；DOM 不显示不构成完整保密边界。FB-GAP-005 明确要求后端/适配器按权限裁剪、约定表示形态，并在未来固定版本联调覆盖混合权限和撤权晚到案例。本次未联调、未修改/运行后端或 EP19。

## 实现与证据身份
- 工作分支：`refs/heads/agent/frontend-wave2-product-ux-v1`
- 基线实际实现树：`414d6ed80f6d4c01699d56403a043b84b390d1e7`
- 最终实际实现树：`c72044119a32be6417ed8d43282f1f37c7f51e00`
- HEAD 与真实 index 保留，未将 HEAD tree 当作工作内容树。1005 个受管路径基线核对无新增漂移。
- [完整 binary-safe 源码补丁](validation/TASK_DELTA.patch)、[逐路径 SHA/模式及分类](validation/SOURCE_DELTA.json)、[独立临时 index 补丁重放](validation/PATCH_REPLAY.json)。before-source/source 保存每个变更端点。

## 测试与七项门禁
原缺陷 RED：41 通过 / 1 失败，保留六类字段的原始 DOM 失败证据；随后范围内 GREEN 与 stale 文案 RED/GREEN 均保留，不计入最终 PASS 分母。
最终聚焦：229/229；全量：845/845。以 V7 原始 789 个结构化身份逐项对账：保留 789，新增 56，移除 0，重复 0，失败 0，跳过 0。
V6→V7 的保留748、移除49、新增41为原历史，不改写为所有旧身份均保留。

七项现行门禁 7/7：聚焦测试、typecheck、Lint、架构守卫、架构控制、完整前端测试、外部输出构建。架构控制 120/120，Lint 0 errors / 46 warnings。原生日志和精确命令在 [validation/gates](validation/gates)，[身份对账](validation/TEST_IDENTITY_ACCOUNTING.json) 含每项保留/新增/移除/重复/失败/跳过及原 reporter。

## 浏览器
最终 Chromium CDP：700 项检查，58 张截图；15 个 emitted/served 文件逐字节核对，差异0。EN桌面1440×1000、EN及中文390×844，覆盖混合集合、同ID撤权、stale/unavailable、打开详情后访问/session改变清除、晚到响应、关闭/Escape焦点返回、无产物链接/下载/HTTP写入。
[浏览器检查原始记录](browser-final/NATIVE_CHECKS.json)、[辅助与模拟披露](browser-final/ASSISTANCE.json)、[流量](browser-final/APPLICATION_TRAFFIC.json)、[served census](browser-final/SERVED_ARTIFACTS.json)、[截图索引](SCREENSHOTS.md)。显式隔离 fixture 围绕最终注册路由；普通未配置入口 unavailable。Native CDP输入结合DOM定位/滚动/locale辅助、fixture来源控制与focus emulation；不是物理移动设备、触摸、IME、虚拟键盘或真实屏幕阅读器证明。浏览器晚到源刻意忽略取消，不是后端行为证明。
构建执行现行产品 Vite 配置并显式验证外部 outDir，双入口共享最终源码。准备工具提供的另一个 fixture-host/vite.config.mjs 未执行；不得将其当成实际构建命令。真实命令在 build-final 门禁记录。[截图人工查看记录](browser-final/VISUAL_REVIEW.json) 披露：截图滚动到产物区，标题/关闭按钮位于上方滚动位置；窄屏任务状态会按字换行，标签偏小。本次不宣称持久标题栏或完整移动UX验收。historical missing /vite.svg 可选 favicon 按旧基线保留，不掩盖必要runtime文件缺失。

## 文档、保全与停止边界
既有审查记录追加缺陷和真实中间结果并保留原文，既有 FB-GAP-005 两处明确集合/逐项含义和后端裁剪义务；没有新权威账本或新受管路径，守卫与历史H4债务不变。V7整体接受仍待独立评审，本次不追改旧V7成已覆盖分支。
[保全](validation/PRESERVATION_FINAL.json) 仅覆盖本前端工作区、真实index/HEAD、V7公共历史和指定构建目标；不要求并行后端或全局动态元数据不变。无Task-issued Skill/Memory写入，无产品commit/freeze/merge/push/publication。

证据包为 sanitized 追加发布候选；固定提交匿名回读、manifest核验和JS分块重组由发布后本地 detached 回执报告，不递归发布回执。推送成功不等于远端验证完成。
**INDEPENDENT_REVIEW=REQUIRED。完成证据交付后停止，不启动 Workflow UX，不关闭 EP19、Slice1C 或发布门禁。**

## 机器字段
```json
{
  "TASK": "FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1",
  "LANE": "FRONTEND",
  "FRONTEND_BRANCH": "refs/heads/agent/frontend-wave2-product-ux-v1",
  "BASELINE_IMPLEMENTATION_TREE": "414d6ed80f6d4c01699d56403a043b84b390d1e7",
  "FINAL_IMPLEMENTATION_TREE": "c72044119a32be6417ed8d43282f1f37c7f51e00",
  "PRODUCT_CHANGED_PATHS": [
    "frontend/src/localization/catalogs.ts",
    "frontend/src/product/render-browser/RenderBrowser.test.tsx",
    "frontend/src/product/render-browser/RenderBrowser.tsx",
    "frontend/src/product/render-browser/source.test.ts"
  ],
  "DOCUMENTATION_CHANGED_PATHS": [
    "docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md",
    "frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv",
    "frontend/governance/UX_WAVE_1_REVIEW.md"
  ],
  "ORIGINAL_FINDING_REPRODUCED": {
    "result": "YES",
    "red_total": 42,
    "red_passed": 41,
    "red_failed": 1,
    "original_component_sha256": "68dc8548f7c0d4342965dbfb3f2f226145856ff07937d9e200963063efe46aaa"
  },
  "ITEM_LEVEL_METADATA_ACCESS_RESULT": "PASS — inspectable only; denied/unknown/unavailable/stale generic localized placeholders, stale read-refresh guidance",
  "MIXED_COLLECTION_RESULT": "PASS — available collection retains allowed metadata and suppresses restricted item fields",
  "ACCESS_TRANSITION_AND_STALE_RESPONSE_RESULT": "PASS — generation/AbortSignal and keyed source/owner cleanup; no old response restoration",
  "DOM_AND_ACCESSIBILITY_NONDISCLOSURE_RESULT": "PASS — complete serialized artifact DOM attributes/text tested; not OS screenreader or JS-memory confidentiality proof",
  "COLLECTION_LEVEL_REGRESSION_RESULT": "PASS — original and added collection-state cases preserved",
  "TARGETED_TEST_RESULTS": {
    "numTotalTests": 229,
    "numPassedTests": 229,
    "numFailedTests": 0,
    "numPendingTests": 0
  },
  "FULL_TEST_IDENTITY_ACCOUNTING": {
    "baseline": 789,
    "final": 845,
    "files": 38,
    "passed": 845,
    "failures": 0,
    "skips": 0,
    "added": 56,
    "removed": 0,
    "duplicates": 0,
    "retained": 789
  },
  "REQUIRED_FRONTEND_GATE_RESULTS": {
    "required": 7,
    "passed": 7,
    "commands": [
      {
        "name": "architecture-controls",
        "implementation_tree": "c72044119a32be6417ed8d43282f1f37c7f51e00",
        "command": [
          "node",
          "scripts/frontend-architecture-guard.test.mjs"
        ],
        "containment": [
          "bwrap",
          "--die-with-parent",
          "--ro-bind",
          "/",
          "/",
          "--bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "--ro-bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "--ro-bind",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "--proc",
          "/proc",
          "--dev",
          "/dev",
          "--tmpfs",
          "/tmp",
          "--chdir",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend",
          "--"
        ],
        "exit_code": 0,
        "elapsed_seconds": 2.1721889972686768
      },
      {
        "name": "architecture",
        "implementation_tree": "c72044119a32be6417ed8d43282f1f37c7f51e00",
        "command": [
          "node",
          "scripts/frontend-architecture-guard.mjs"
        ],
        "containment": [
          "bwrap",
          "--die-with-parent",
          "--ro-bind",
          "/",
          "/",
          "--bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "--ro-bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "--ro-bind",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "--proc",
          "/proc",
          "--dev",
          "/dev",
          "--tmpfs",
          "/tmp",
          "--chdir",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend",
          "--"
        ],
        "exit_code": 0,
        "elapsed_seconds": 1.5700364112854004
      },
      {
        "name": "build-final",
        "implementation_tree": "c72044119a32be6417ed8d43282f1f37c7f51e00",
        "command": [
          "node",
          "--input-type=module",
          "-e",
          "import {build,resolveConfig} from 'vite';import path from 'node:path';import fs from 'node:fs';const output=\"/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/build\";if(fs.existsSync(output))throw Error('External output must be new');const opts={configLoader:'bundle',build:{outDir:output,emptyOutDir:false,manifest:true,rollupOptions:{input:{application:\"/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend/index.html\",fixture:\"/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/fixture-host/entry.tsx\"}}}};const c=await resolveConfig(opts,'build');if(path.resolve(c.root,c.build.outDir)!==output)throw Error('Unexpected effective output');console.log('EFFECTIVE_EXTERNAL_OUTPUT='+output);await build(opts);const manifest=JSON.parse(fs.readFileSync(path.join(output,'.vite/manifest.json'),'utf8'));const fixture=Object.values(manifest).find(x=>x.isEntry&&x.name==='fixture');if(!fixture)throw Error('Missing explicit fixture entry');const html=fs.readFileSync(path.join(output,'index.html'),'utf8');const fixtureHtml=html.replace(/(<script[^>]+src=\")([^\"]+)(\")/,(_,a,b,c)=>a+'/'+fixture.file+c);if(fixtureHtml===html)throw Error('Missing standard module entry');fs.writeFileSync(path.join(output,'fixture.html'),fixtureHtml);console.log('EXPLICIT_FIXTURE_ENTRY='+fixture.file);"
        ],
        "containment": [
          "bwrap",
          "--die-with-parent",
          "--ro-bind",
          "/",
          "/",
          "--bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "--ro-bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "--ro-bind",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "--proc",
          "/proc",
          "--dev",
          "/dev",
          "--tmpfs",
          "/tmp",
          "--chdir",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend",
          "--bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/vite-temp",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules/.vite-temp",
          "--"
        ],
        "exit_code": 0,
        "elapsed_seconds": 6.135356426239014
      },
      {
        "name": "full-frontend-final",
        "implementation_tree": "c72044119a32be6417ed8d43282f1f37c7f51e00",
        "command": [
          "./node_modules/.bin/vitest",
          "run",
          "--configLoader",
          "runner",
          "--no-cache",
          "--reporter=json",
          "--outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/FULL_UNIT.json"
        ],
        "containment": [
          "bwrap",
          "--die-with-parent",
          "--ro-bind",
          "/",
          "/",
          "--bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "--ro-bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "--ro-bind",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "--proc",
          "/proc",
          "--dev",
          "/dev",
          "--tmpfs",
          "/tmp",
          "--chdir",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend",
          "--"
        ],
        "exit_code": 0,
        "elapsed_seconds": 9.55063009262085
      },
      {
        "name": "lint",
        "implementation_tree": "c72044119a32be6417ed8d43282f1f37c7f51e00",
        "command": [
          "./node_modules/.bin/eslint",
          "src/**/*.{ts,tsx}"
        ],
        "containment": [
          "bwrap",
          "--die-with-parent",
          "--ro-bind",
          "/",
          "/",
          "--bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "--ro-bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "--ro-bind",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "--proc",
          "/proc",
          "--dev",
          "/dev",
          "--tmpfs",
          "/tmp",
          "--chdir",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend",
          "--"
        ],
        "exit_code": 0,
        "elapsed_seconds": 5.583914279937744
      },
      {
        "name": "targeted-final",
        "implementation_tree": "c72044119a32be6417ed8d43282f1f37c7f51e00",
        "command": [
          "./node_modules/.bin/vitest",
          "run",
          "src/product/render-browser",
          "src/components/app-shell/AppShell.test.tsx",
          "src/interaction",
          "src/localization/localization.test.tsx",
          "src/app/routeTree.test.tsx",
          "--configLoader",
          "runner",
          "--no-cache",
          "--reporter=json",
          "--outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/TARGETED_FINAL.json"
        ],
        "containment": [
          "bwrap",
          "--die-with-parent",
          "--ro-bind",
          "/",
          "/",
          "--bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "--ro-bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "--ro-bind",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "--proc",
          "/proc",
          "--dev",
          "/dev",
          "--tmpfs",
          "/tmp",
          "--chdir",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend",
          "--"
        ],
        "exit_code": 0,
        "elapsed_seconds": 7.843107223510742
      },
      {
        "name": "type-policy",
        "implementation_tree": "c72044119a32be6417ed8d43282f1f37c7f51e00",
        "command": [
          "npm",
          "run",
          "typecheck"
        ],
        "containment": [
          "bwrap",
          "--die-with-parent",
          "--ro-bind",
          "/",
          "/",
          "--bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01",
          "--ro-bind",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot",
          "--ro-bind",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules",
          "--proc",
          "/proc",
          "--dev",
          "/dev",
          "--tmpfs",
          "/tmp",
          "--chdir",
          "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend",
          "--"
        ],
        "exit_code": 0,
        "elapsed_seconds": 11.402835607528687
      }
    ],
    "architecture_controls": {
      "tests": 120,
      "pass": 120,
      "fail": 0,
      "skipped": 0
    },
    "lint": {
      "problems": 46,
      "errors": 0,
      "warnings": 46
    }
  },
  "FOCUSED_BROWSER_RESULTS": {
    "checks": 700,
    "passed": 700,
    "failed": 0,
    "screenshots": 58,
    "served_files": 15,
    "served_hash_differences": 0,
    "http_mutations": 0,
    "assistance": {
      "tree": "c72044119a32be6417ed8d43282f1f37c7f51e00",
      "native": "Real Chromium CDP pointer and Escape; DOM locators scroll and mark targets; locale helper dispatches input/change (not native locale input).",
      "fixture": "Opt-in simulated adapter controls outcomes/context and delayed response; no backend permission/auth proof. No render retry/execution. Inert localStorage auth marker in isolated disposable profile.",
      "focus_emulation": true,
      "viewports": [
        [
          1440,
          1000
        ],
        [
          390,
          844
        ]
      ],
      "limits": [
        "Desktop headless viewport emulation, not physical mobile/touch/IME/screenreader acceptance",
        "Shared task-courtyard has independent task/attempt basis outside artifact subtree; mixed allowed item independently permits its task link; restricted item subtrees exclude taskId and all-restricted artifact section excludes taskId",
        "DOM includes raw attributes/title/aria/data/hidden/links; React internal JS props are not DOM disclosure",
        "Independent final review and parent-owned gates remain required"
      ]
    },
    "native_exits": {
      "processes": [
        {
          "name": "smoke",
          "pid": 570470,
          "exit": 0,
          "terminated_by_task": false
        },
        {
          "name": "chrome",
          "pid": 570319,
          "exit": 0,
          "terminated_by_task": false
        },
        {
          "name": "fixture",
          "pid": 570300,
          "exit": -15,
          "terminated_by_task": true
        }
      ],
      "remaining_ports": []
    }
  },
  "BUILD_MANIFEST_SHA256": "dff4f85d1ce316987cc919ce9dc9c35ce5d1b98032baa2e7a99c58c31b57e2a0",
  "BACKEND_REQUIREMENTS_UPDATED": "YES — existing FB-GAP-005; no new requirement ID; real transport/permission contract unestablished",
  "BACKEND_CHANGES": 0,
  "TRACKED_DIST_CHANGES": 0,
  "BACKEND_STATIC_CHANGES": 0,
  "REAL_INTEGRATION_PERFORMED": "NOT_PERFORMED",
  "BOUNDED_PRESERVATION_RESULT": {
    "head": "f5e19cf53fd010eea2935dd29557e82a879e042c",
    "branch": "refs/heads/agent/frontend-wave2-product-ux-v1",
    "final_tree": "c72044119a32be6417ed8d43282f1f37c7f51e00",
    "real_index_unchanged": true,
    "final_scoped_paths": 1005,
    "final_bytes_modes_membership_match": true,
    "unchanged_baseline_paths_outside_allowlist": 994,
    "bounded_historical_and_dist_files": 564,
    "bounded_preservation_differences": [],
    "product_git_mutations": 0,
    "backend_task_checks": 0,
    "scope": "Named frontend worktree and task-recorded predecessor public/build/receipt plus tracked frontend dist. No parallel backend or whole-system stationarity claim."
  },
  "HISTORICAL_REPORTS_PRESERVED": "YES",
  "PRODUCT_COMMIT_FREEZE_MERGE_PUSH": "NOT_PERFORMED",
  "PRODUCT_PUBLICATION": "NOT_PERFORMED",
  "EVIDENCE_DELIVERY_STATUS": "LOCAL_VERIFIED_PREPUBLICATION — detached post-publication receipt authoritative",
  "EVIDENCE_COMMIT_SHA": "NOT_ESTABLISHED_AT_PACKAGE_SEAL",
  "REVIEW_INDEX_URL": "REVIEW_INDEX.md",
  "RAW_REVIEW_INDEX_URL": "REVIEW_INDEX.md",
  "MACHINE_INDEX_URL": "REVIEW_INDEX.json",
  "PUBLIC_MANIFEST_SHA256": "Detached receipt; no self-referential digest",
  "REMOTE_VERIFICATION": "PENDING_AT_PACKAGE_SEAL",
  "INDEPENDENT_REVIEW": "REQUIRED",
  "STOP": "YES — after evidence delivery, independent review required; no Workflow UX or EP19/Slice1C/release closure"
}
```
