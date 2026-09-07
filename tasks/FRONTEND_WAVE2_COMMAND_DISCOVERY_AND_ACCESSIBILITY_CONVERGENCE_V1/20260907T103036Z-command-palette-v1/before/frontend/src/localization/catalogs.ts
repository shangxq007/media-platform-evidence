import { createCatalog, messageAt, type CatalogNamespaces, type LocalizationCatalog, type MessageDefinition, type SupportedLocale, type ValidationResult } from './catalog'
import sourceManifest from './source-manifest.json'

const message = (value: string, params: readonly string[] = []): MessageDefinition => ({ message: value, params })

const englishNamespaces: CatalogNamespaces = {
  common: {
    greeting: message('Hello, {name}', ['name']),
    untitled: message('Untitled'),
    none: message('None'),
    localeSelector: message('Product UI language'),
    localeEnglish: message('English'),
    localeChinese: message('简体中文'),
  },
  shell: {
    brandHome: message('Media Platform home'), brand: message('Media Platform'), creativeWorkspace: message('Creative workspace'),
    globalNavigation: message('Global navigation'), projectNavigation: message('Project navigation'), projectSurfaceSwitcher: message('Project surface switcher'),
    workspace: message('Workspace'), operations: message('Operations'), admin: message('Admin'), developer: message('Developer'),
    overview: message('Overview'), review: message('Review'), production: message('Production'), panelControls: message('Panel controls'),
    navigation: message('Navigation'), navigationDrawerSurfaces: message('Navigation drawer surfaces'), toggleAssetBrowser: message('Toggle asset browser'),
    commands: message('Commands'), skipToMain: message('Skip to main content'), assetBrowser: message('Asset browser'), assets: message('Assets'),
    commandPalette: message('Command palette'), searchCommands: message('Search commands'), typeCommand: message('Type a command…'), noMatchingCommands: message('No matching commands.'),
    commandUnavailable: message('This action is not ready here. A connected, authorized application flow is required.'), technicalDetails: message('Technical details'),
    'command.project.create': message('Create project'), 'command.render.open': message('Open render entry'),
    'command.timeline.operation.apply': message('Apply timeline operation'), 'command.canvas.reference.add': message('Add canvas reference'),
    'command.workflow.invoke': message('Invoke workflow'), 'command.agent.action.authorize': message('Authorize proposed action'),
    'command.review.merge.request': message('Request canonical merge'),
    assetsUnavailable: message('Media browsing is not available yet. No assets have been loaded.'), timelineActivity: message('Timeline / activity'),
    canonicalResults: message('Canonical command results will appear here when integrated.'), activityPanel: message('Activity panel'), activity: message('Activity'),
    activityUnavailable: message('No scoped activity projection is available for this view.'),
  },
  agent: {
    primaryOnly: message("Existing operations affect only the primary object. Other selected objects remain unchanged."),
    canonicalUnavailable: message("This change cannot be applied here yet. A connected server preview and confirmation flow is required; use the existing timeline advanced controls for supported operations."),
    localAxis: message("Local {axis}", ["axis"]),
    placementRange: message("Placement range: −2000 to 2000 local units."),
    simulatedTimeHelp: message("Time uses simulated steps, not decoded media time."),
    simulatedTime: message("{count} simulated steps{range}", ["count", "range"]),
    simulatedRange: message(" · range {range}", ["range"]),
    demonstration: message("Deterministic UX demonstration · no connected Agent planning"),
    localResult: message("Local presentation or read-only request only; no canonical mutation."),
    requestUnavailable: message("This request is unavailable in the current context. Preview again."),
    selectedClips: message("{count} selected clips", ["count"]),
    selectedObjects: message("{count} selected objects", ["count"]),
    adjustAudio: message("Adjust audio (demo)"),
    duplicate: message("Duplicate (demo)"),
    fixtureUnavailable: message("Synthetic fixture only; no connected authorized operation."),
    kindNODE: message("NODE"),
    kindCLIP: message("CLIP"),
    kindLANE: message("LANE"),
    kindLowerNODE: message("node"),
    kindLowerCLIP: message("clip"),
    kindLowerLANE: message("lane"),
    ask: message('Ask Agent'), title: message('Agent conversation'), close: message('Close Agent conversation'), body: message('Agent conversation body'),
    context: message('Agent context'), project: message('Project: {project}', ['project']), surface: message('Surface: {surface}', ['surface']),
    selection: message('Selection: {selection}', ['selection']), time: message('Time: {time}', ['time']), revisionPair: message('Revision pair: {pair}', ['pair']),
    noProject: message('No project selected'), none: message('None'), useCompact: message('Use compact sheet'), expand: message('Expand sheet'),
    details: message('Details and diagnostics'), proposal: message('Synthetic proposal'), syntheticDemo: message('Synthetic demo'),
    understoodRequest: message('Understood request'), noRequest: message('No request entered.'), targets: message('Targets'), proposedChange: message('Proposed change'),
    readOnlyAvailable: message('A read-only comparison can be run; it does not make a canonical change.'),
    localActionAvailable: message('This local presentation action is available now. It is not saved and does not make a canonical change.'),
    proposalUnavailable: message('Apply is unavailable for this proposal. Preview or modify the request; a connected confirmation flow is required before a canonical change.'),
    contextChanged: message('Context changed. Preview again for the current selection and time.'), modify: message('Modify'),
    runReadOnly: message('Run read-only comparison'), openInspector: message('Open Inspector'), applyLocal: message('Apply local presentation'),
    revealLocal: message('Reveal primary locally'), apply: message('Apply'), applyUnavailableA11y: message('Unavailable: this synthetic demo has no connected canonical confirmation flow.'),
    proposalDiagnostics: message('Proposal diagnostics'), userIntent: message('User intent'), intentPlaceholder: message('Try inspect, reveal, or rename to Opening shot'),
    preview: message('Preview'), clearConversation: message('Clear conversation'), composer: message('Agent composer'),
    selectionActions: message('Selection actions'), selectedPrimary: message('{count} selected · primary {kind} · {title}', ['count', 'kind', 'title']),
    singleSelection: message('{kind} · {title}', ['kind', 'title']), hideInspector: message('Hide inspector'), showInspector: message('Show inspector'),
    revealPrimary: message('Reveal primary {kind}', ['kind']), clearSelection: message('Clear selection'), more: message('More'),
    localOnly: message('Local presentation only · not saved'), editProperties: message('Edit local properties'), applyCanonical: message('Apply canonical change'),
    technicalDetails: message('Technical details'), localNodeInspector: message('Local node inspector'), presentationSelection: message('Presentation selection'),
    syntheticFixture: message('Synthetic fixture · no canonical clip geometry.'), localPresentationLifetime: message('Local presentation · changes last until you leave this surface or project.'),
    selectedObject: message('Selected object'), selectedTargets: message('Selected targets'), selectedTrack: message('Selected track'), localTitle: message('Local title'),
    reference: message('Reference'), simulationStep: message('Simulation step'), showPrimaryNode: message('Show primary node'), clearTrackSelection: message('Clear track selection'),
    selectionInspector: message('Selection inspector'), openSelectionProperties: message('Open selection properties'), selectionProperties: message('Selection properties'),
    commandInspect: message('Inspect {target}', ['target']), commandReveal: message('Reveal {target}', ['target']), commandAsk: message('Ask Agent about {target}', ['target']), commandCompare: message('What changed between these revisions?'),
  },
  canvas: {
    selectMode: message("Select"), panMode: message("Pan"),
    pointerHelp: message("Select: drag empty space to select nodes. Drag at least 4 screen pixels with width and height; Ctrl or Meta adds to selection. Pan: drag empty space to move the view. Drag a selected node to move its group locally; release to finish. Escape cancels a gesture. Keyboard and Multi-select controls remain available."),
    dragPreview: message("Local move preview; release to place."), marqueePreview: message("Selection preview; release to select."), panPreview: message("View preview; release to pan."),
    multiSelect: message("Multi-select"),
    done: message("Done"),
    controls: message("Canvas controls · local changes only"),
    keyboardHelp: message("On the canvas, arrows pan and =/− zoom. Tab focuses nodes; Enter or Space selects. Ctrl/Meta click or Enter/Space toggles selection. Multi-select mode toggles with taps; Done returns to single selection. On a node, arrows move only that node 24 local units and preserve selected membership. R reveals the primary. Escape clears selection. Visual guides never create semantic relationships."),
    relationshipUnavailable: message("No canonical relationship command is integrated."),
    relationship: message("Create semantic relationship"),
    untitledNode: message("Untitled local node"),
    noReference: message("No semantic reference"),
    visualOnly: message("visual only"),
    selectionStatus: message("{count} selected · primary: {title}", ["count", "title"]),
    viewportStatus: message("Viewport: {x}, {y}", ["x", "y"]),
    viewportControls: message("Canvas viewport controls"),
    fit: message("Fit canvas"),
    moreViewport: message("More viewport controls"),
    panLeft: message("Pan left"),
    panRight: message("Pan right"),
    panUp: message("Pan up"),
    panDown: message("Pan down"),
    zoomOut: message("Zoom out"),
    zoomIn: message("Zoom in"),
    resetViewport: message("Reset viewport"),
    eyebrow: message('Creative · Canvas'), title: message('Infinite canvas'), description: message('Arrange ideas around your project. Local changes are not saved.'),
    workspace: message('Infinite canvas workspace'), localComposition: message('Local composition'),
  },
  timeline: {
    eyebrow: message('Creative · NLE'), title: message('Timeline editor'), description: message('Explore the timeline and preview changes before applying them.'),
    workspace: message('Timeline workspace'), playbackControls: message('Timeline playback controls'), keyboardControls: message('Timeline keyboard controls'),
  },
  review: {
    eyebrow: message('Review & collaboration'), title: message('Project review'), description: message('Choose two revisions to see what changed. Review does not apply or merge changes.'),
    panel: message('Semantic Changes'), missingInZh: message('English fallback proof'),
  },
  workflow: {},
  render: {},
  settings: {},
  errors: {},
}

const chineseNamespaces: CatalogNamespaces = {
  common: {
    greeting: message('你好，{name}', ['name']), untitled: message('未命名'), none: message('无'),
    localeSelector: message('产品界面语言'), localeEnglish: message('English'), localeChinese: message('简体中文'),
  },
  shell: {
    brandHome: message('媒体平台首页'), brand: message('媒体平台'), creativeWorkspace: message('创作工作区'),
    globalNavigation: message('全局导航'), projectNavigation: message('项目导航'), projectSurfaceSwitcher: message('项目界面切换'),
    workspace: message('工作区'), operations: message('运营'), admin: message('管理'), developer: message('开发者'), overview: message('概览'), review: message('审阅'),
    production: message('制作'), panelControls: message('面板控件'), navigation: message('导航'), navigationDrawerSurfaces: message('导航抽屉界面'),
    toggleAssetBrowser: message('切换素材浏览器'), commands: message('命令'), skipToMain: message('跳到主要内容'), assetBrowser: message('素材浏览器'),
    commandPalette: message('命令面板'), searchCommands: message('搜索命令'), typeCommand: message('输入命令…'), noMatchingCommands: message('没有匹配的命令。'),
    commandUnavailable: message('此操作尚未就绪，需要已连接且获授权的应用流程。'), technicalDetails: message('技术详情'),
    'command.project.create': message('创建项目'), 'command.render.open': message('打开渲染入口'),
    'command.timeline.operation.apply': message('应用时间线操作'), 'command.canvas.reference.add': message('添加画布引用'),
    'command.workflow.invoke': message('调用工作流'), 'command.agent.action.authorize': message('授权拟议操作'),
    'command.review.merge.request': message('请求规范合并'),
    assets: message('素材'), assetsUnavailable: message('媒体浏览暂不可用。尚未加载素材。'), timelineActivity: message('时间线 / 活动'),
    canonicalResults: message('接入后，规范命令结果将显示在这里。'), activityPanel: message('活动面板'), activity: message('活动'),
    activityUnavailable: message('此视图暂无限定范围的活动投影。'),
  },
  agent: {
    primaryOnly: message("现有操作仅影响主要对象。其他所选对象保持不变。"),
    canonicalUnavailable: message("此处尚无法应用此更改。需要已连接的服务器预览和确认流程。"),
    localAxis: message("本地 {axis}", ["axis"]),
    placementRange: message("放置范围：−2000 至 2000 个本地单位。"),
    simulatedTimeHelp: message("时间使用模拟步骤，并非解码媒体时间。"),
    simulatedTime: message("{count} 个模拟步骤{range}", ["count", "range"]),
    simulatedRange: message(" · 范围 {range}", ["range"]),
    demonstration: message("确定性界面演示 · 未连接 Agent 规划"),
    localResult: message("仅本地呈现或只读请求；无规范更改。"),
    requestUnavailable: message("当前上下文中此请求不可用。请重新预览。"),
    selectedClips: message("已选择的 {count} 个片段", ["count"]),
    selectedObjects: message("已选择的 {count} 个对象", ["count"]),
    adjustAudio: message("调整音频（演示）"),
    duplicate: message("复制（演示）"),
    fixtureUnavailable: message("仅模拟夹具；未连接获授权的操作。"),
    kindNODE: message("节点"),
    kindCLIP: message("片段"),
    kindLANE: message("轨道"),
    kindLowerNODE: message("节点"),
    kindLowerCLIP: message("片段"),
    kindLowerLANE: message("轨道"),
    ask: message('询问 Agent'), title: message('Agent 对话'), close: message('关闭 Agent 对话'), body: message('Agent 对话内容'), context: message('Agent 上下文'),
    project: message('项目：{project}', ['project']), surface: message('界面：{surface}', ['surface']), selection: message('选择：{selection}', ['selection']),
    time: message('时间：{time}', ['time']), revisionPair: message('修订对：{pair}', ['pair']), noProject: message('未选择项目'), none: message('无'),
    useCompact: message('使用紧凑面板'), expand: message('展开面板'), details: message('详情与诊断'), proposal: message('模拟提案'), syntheticDemo: message('模拟演示'),
    understoodRequest: message('已理解的请求'), noRequest: message('未输入请求。'), targets: message('目标'), proposedChange: message('拟议更改'),
    readOnlyAvailable: message('可以运行只读比较；它不会进行规范更改。'), localActionAvailable: message('此本地呈现操作现已可用。它不会保存，也不会进行规范更改。'),
    proposalUnavailable: message('此提案无法应用。请预览或修改请求；规范更改前需要已连接的确认流程。'),
    contextChanged: message('上下文已变化。请针对当前选择和时间重新预览。'), modify: message('修改'), runReadOnly: message('运行只读比较'),
    openInspector: message('打开检查器'), applyLocal: message('应用本地呈现'), revealLocal: message('在本地显示主要对象'), apply: message('应用'),
    applyUnavailableA11y: message('不可用：此模拟演示未连接规范确认流程。'), proposalDiagnostics: message('提案诊断'), userIntent: message('用户意图'),
    intentPlaceholder: message('描述要检查或更改的内容'), preview: message('预览'), clearConversation: message('清除对话'), composer: message('Agent 编辑器'),
    selectionActions: message('选择操作'), selectedPrimary: message('已选择 {count} 个 · 主要 {kind} · {title}', ['count', 'kind', 'title']),
    singleSelection: message('{kind} · {title}', ['kind', 'title']), hideInspector: message('隐藏检查器'), showInspector: message('显示检查器'),
    revealPrimary: message('显示主要{kind}', ['kind']), clearSelection: message('清除选择'), more: message('更多'), localOnly: message('仅本地呈现 · 未保存'),
    editProperties: message('编辑本地属性'), applyCanonical: message('应用规范更改'), technicalDetails: message('技术详情'), localNodeInspector: message('本地节点检查器'),
    presentationSelection: message('呈现选择'), syntheticFixture: message('模拟夹具 · 无规范片段几何信息。'),
    localPresentationLifetime: message('本地呈现 · 离开此界面或项目后更改失效。'), selectedObject: message('所选对象'), selectedTargets: message('所选目标'),
    selectedTrack: message('所选轨道'), localTitle: message('本地标题'), reference: message('引用'), simulationStep: message('模拟步骤'),
    showPrimaryNode: message('显示主要节点'), clearTrackSelection: message('清除轨道选择'), selectionInspector: message('选择检查器'),
    openSelectionProperties: message('打开选择属性'), selectionProperties: message('选择属性'),
    commandInspect: message('检查{target}', ['target']), commandReveal: message('显示{target}', ['target']), commandAsk: message('就{target}询问 Agent', ['target']), commandCompare: message('这些修订之间有什么变化？'),
  },
  canvas: {
    selectMode: message("选择"), panMode: message("平移"),
    pointerHelp: message("选择：在空白处拖动以选择节点。拖动至少 4 个屏幕像素并形成宽和高；Ctrl 或 Meta 添加选择。平移：在空白处拖动以移动视图。拖动已选节点可在本地移动整组；松开完成。Escape 取消手势。仍可使用键盘和多选控件。"),
    dragPreview: message("本地移动预览；松开以放置。"), marqueePreview: message("选择预览；松开以选择。"), panPreview: message("视图预览；松开以平移。"),
    multiSelect: message("多选"),
    done: message("完成"),
    controls: message("画布控件 · 仅本地更改"),
    keyboardHelp: message("在画布上，方向键平移，=/− 缩放。Tab 聚焦节点；Enter 或空格选择。Ctrl/Meta 点击或 Enter/空格切换选择。多选模式下轻点切换选择；完成后恢复单选。节点上的方向键仅移动该节点 24 个本地单位并保留已有选择。R 显示主要对象。Escape 清除选择。视觉辅助线不创建语义关系。"),
    relationshipUnavailable: message("尚未接入规范关系命令。"),
    relationship: message("创建语义关系"),
    untitledNode: message("未命名本地节点"),
    noReference: message("无语义引用"),
    visualOnly: message("仅视觉"),
    selectionStatus: message("已选择 {count} 个 · 主要对象：{title}", ["count", "title"]),
    viewportStatus: message("视口：{x}, {y}", ["x", "y"]),
    viewportControls: message("画布视口控件"),
    fit: message("适应画布"),
    moreViewport: message("更多视口控件"),
    panLeft: message("向左平移"),
    panRight: message("向右平移"),
    panUp: message("向上平移"),
    panDown: message("向下平移"),
    zoomOut: message("缩小"),
    zoomIn: message("放大"),
    resetViewport: message("重置视口"), eyebrow: message('创作 · 画布'), title: message('无限画布'), description: message('排列本地呈现节点，而不更改规范媒体。'), workspace: message('无限画布工作区'), localComposition: message('本地合成') },
  timeline: { eyebrow: message('创作 · 非线性编辑'), title: message('时间线编辑器'), description: message('浏览时间线，并在应用前预览更改。'), workspace: message('时间线工作区'), playbackControls: message('时间线播放控件'), keyboardControls: message('时间线键盘控件') },
  review: { eyebrow: message('创作 · 审阅'), title: message('审阅工作区'), description: message('检查修订证据并留下限定范围的审阅反馈。'), panel: message('修订审阅') },
  workflow: {}, render: {}, settings: {}, errors: {},
}

const bundledCatalogs = {
  en: createCatalog('en', englishNamespaces),
  'zh-CN': createCatalog('zh-CN', chineseNamespaces),
} as const

export class BundledCatalogProvider {
  getCatalog(locale: SupportedLocale): LocalizationCatalog {
    return bundledCatalogs[locale]
  }

  getSourceCatalog(): LocalizationCatalog {
    return bundledCatalogs.en
  }
}

export const defaultBundledCatalogProvider = new BundledCatalogProvider()

function sameParameters(actual: readonly string[], expected: readonly string[]): boolean {
  const left = [...actual].sort()
  const right = [...expected].sort()
  return left.length === right.length && left.every((parameter, index) => parameter === right[index])
}

export function validatePlatformCatalogContract(catalog: LocalizationCatalog): ValidationResult<LocalizationCatalog> {
  const source = defaultBundledCatalogProvider.getSourceCatalog()
  for (const [namespace, messages] of Object.entries(catalog.namespaces)) {
    for (const [key, definition] of Object.entries(messages)) {
      const fullKey = `${namespace}.${key}`
      const sourceDefinition = messageAt(source, fullKey)
      if (!sourceDefinition) return { ok: false, error: `${fullKey}: key is not platform owned` }
      if (!sameParameters(definition.params, sourceDefinition.params)) return { ok: false, error: `${fullKey}: parameter contract differs from platform source` }
    }
  }
  return { ok: true, value: catalog }
}

export function validatePlatformParameterContracts(contracts: Readonly<Record<string, readonly string[]>>): ValidationResult<Readonly<Record<string, readonly string[]>>> {
  const source = defaultBundledCatalogProvider.getSourceCatalog()
  for (const [fullKey, parameters] of Object.entries(contracts)) {
    const sourceDefinition = messageAt(source, fullKey)
    if (!sourceDefinition) return { ok: false, error: `${fullKey}: parameter contract key is not platform owned` }
    if (!sameParameters(parameters, sourceDefinition.params)) return { ok: false, error: `${fullKey}: parameter contract differs from platform source` }
  }
  return { ok: true, value: contracts }
}

export const requiredSourceKeys = sourceManifest.requiredSourceKeys

export function validateRequiredSourceKeys(keys: readonly string[]): { ok: true } | { ok: false; missing: string[] } {
  const missing = keys.filter(key => !messageAt(defaultBundledCatalogProvider.getSourceCatalog(), key))
  return missing.length ? { ok: false, missing } : { ok: true }
}

const requiredSourceValidation = validateRequiredSourceKeys(requiredSourceKeys)
if (!requiredSourceValidation.ok) throw new Error(`Bundled English catalog is missing required source keys: ${requiredSourceValidation.missing.join(', ')}`)
