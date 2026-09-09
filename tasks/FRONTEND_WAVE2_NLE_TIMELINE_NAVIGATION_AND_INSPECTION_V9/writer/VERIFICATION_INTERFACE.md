# Stable V9 verification interfaces

This is a fixture-host recipe, not browser adaptation or real integration. Parent runs final browser gates after consuming the tested interfaces.

## Existing route and providers

- Existing entry: `/w/$workspaceId/projects/$projectId/edit`; `NlePage` still wraps `ProjectFrame surfaceId="nle"`.
- `NleWorkspace` retains `queryGateway?: TimelineQueryGateway`, `commandGateway?: OperationGateway`, `sourceGateway?: AssetGateway`, `capabilityGateway?: CapabilityGateway`. Adds `navigationSource?: TimelineNavigationSource`.
- Exported `TimelineNavigationProvider({source,children})` from `frontend/src/product/timeline/TimelineNavigation.tsx` can wrap the actual router in an isolated host. A directly supplied `navigationSource` wins. Ordinary production entry supplies neither; no environment/URL switch, fixture toggle or default geometry source exists.
- An isolated host must explicitly stub the existing query gateway independently. Tracks/clips never establish HEAD. Successful `getHead` and history establish the displayed HEAD; explicit selected history detail changes the inspected revision. For historical revisions, HEAD contentHash is omitted rather than assigned to that revision. The default gateway's Project==Timeline mapping is historical behavior, not independent identity evidence.

## Source schema (frontend-local, no HTTP)

See exported types in `frontend/src/product/timeline/navigation.ts`.

```ts
const source: TimelineNavigationSource = {
  scope: {
    principalId: 'verification-principal', tenantId: 'tenant-1',
    sessionId: 'verification-session', workspaceId: 'workspace-1',
    projectId: 'project-1',
  },
  accessBinding: { kind: 'TEST_ONLY_UNAGREED', key: 'test-navigation' },
  access: {
    key: 'test-navigation', source: 'SERVER', status: 'AVAILABLE',
    reasonCode: 'ISOLATED_VERIFICATION_ONLY', explanation: 'Simulated read access',
    factors: {
      capability: 'SATISFIED', runtime: 'NOT_APPLICABLE',
      entitlement: 'SATISFIED', policy: 'SATISFIED', quota: 'NOT_APPLICABLE',
    },
  },
  adapter: {
    origin: 'isolated-verification',
    async read(request, signal) {
      // Honor signal in the host; the consumer also isolates late completions.
      return {
        ...request,
        status: 'ok', completeness: 'complete', timeBasis: 'exact-seconds',
        bounds: { start: '0', end: '2' },
        tracks: [
          { id: 'video-1', name: 'Picture', type: 'video', clips: [
            { id: 'clip-1', trackId: 'video-1', name: 'Opening', type: 'video',
              timelineRange: { start: '0', end: '1001/30000' },
              source: { mediaAssetId: 'asset-1', mediaStreamId: 'stream-1' } },
          ] },
          { id: 'audio-1', name: 'Audio', type: 'audio', clips: [] },
        ],
      }
    },
  },
}
```

`SERVER` in this recipe is explicitly a simulated EffectiveAccessEntry; it never grants actual access. The key is test-local, not an invented server permission. The injected host owns reactive identity changes and must replace scope/access/adapter when appropriate. Source scope must match host Workspace, tenant and Project, and the queried target Project. The shared Selection owner and existing OIDC shell subscription govern local retirement; fixture scope is not compared to live backend credentials or accepted as identity authority.

Request is `{scope,target,requestId}`. Target is `{projectId,timelineId,revisionId,contentHash?}`. Response echoes all three exact request fields. Success adds `{status:'ok',completeness:'complete'|'bounded',timeBasis:'exact-seconds'|'unknown',bounds?:{start,end},tracks}`. Failure is only `{...request,status:'unavailable'|'error'|'stale'|'restricted'}`; throw to exercise a read error. Unknown envelope fields fail strict validation. Omit success fields on failure. Keep the adapter object stable to test equal rerenders; replacing it intentionally resets navigation. observedAt and access explanation are not owner identity.

Track: `{id,name?,type?,clips}`. Clip: `{id,trackId,name?,type?,version?,timelineRange?,sourceRange?,source?}`. Source: `{mediaAssetId,mediaStreamId?,artifactId?,contentDigest?}`. All references are logical text; no media URL/path exists in the schema. IDs use existing 1–64 safe logical-ID validation, names/types max1000, maximum100 tracks and500 total clips. Duplicate track/clip IDs, wrong parent/receipt/target, malformed ranges and clip ranges outside supplied bounds fail closed. Source range and timeline range remain distinct; no temporal mapping or source-vs-timeline duration equivalence is inferred.

## Time and navigation

Exact time input accepts existing bounded integer/rational text (64 chars, positive denominator), never decimals or exponent notation. UI location rejects negatives and values outside supplied optional inclusive bounds. Without bounds, nonnegative exact positions are valid and no total duration is invented. All comparison/difference uses BigInt rational arithmetic; no Number conversion, assumed FPS or frame step.

Authored `MediaClip.TimeRange.contains` is inclusive at both ends, so a shared boundary may match multiple clips, and a zero-length range matches its sole point. Location reports the number of loaded matches and selects the first loaded match. `Locate selected clip` keeps the explicit clip selected even at overlapping boundaries, clears a hiding filter and reveals it. Unknown time basis disables both location buttons/input and derived duration. Raw supplied ranges remain labeled metadata. Position is local navigation, never playhead/progress/audio/frame state. No zoom implementation; scrolling is an internally bounded structured list.

## Stable UI selectors and behavior

| English accessible label/text | Chinese accessible label/text | Behavior |
|---|---|---|
| Timeline navigation | 时间线导航 | Main region, focus fallback |
| Track and clip projection unavailable | 轨道和片段投影不可用 | Ordinary absent source or missing queried target |
| Loaded tracks and clips | 已加载轨道和片段 | Internal scroll container |
| Filter loaded tracks and clips | 筛选已加载轨道和片段 | Loaded name/type/ID filter |
| Exact time (integer or fraction) | 精确时间（整数或分数） | Exact input |
| Locate time | 定位时间 | Set local position, report matches |
| Locate selected clip | 定位选中片段 | Reveal explicit clip |
| Local navigation position | 本地导航位置 | Output, no clock |
| Inspect selected metadata | 检查选中对象元数据 | Open full dialog |
| Timeline object metadata | 时间线对象元数据 | InteractionDialog name |
| Close timeline metadata | 关闭时间线元数据 | Close/Escape restores launcher |
| Clear navigation selection | 清除导航选择 | Shared LOCAL_EPHEMERAL clear |
| Refresh loaded projection | 刷新已加载投影 | Withdraw old snapshot, read again |
| Retry timeline projection | 重试时间线投影 | Typed failure retry |

Buttons have `data-navigation-object="track:<id>"` or `"clip:<id>"`, full title text in accessible name/title, and `aria-pressed`. Selection IDs are presentation-only and have no canonical authority. Track types are supplied literal metadata. Long button names truncate visually, full metadata wraps in the dialog; mobile rules collapse detail property columns. CSS uses current theme tokens.

Tab/Enter/Space use native button semantics. Up/Down/Home/End within the list focus/select another loaded object; modified/composing keys are untouched. I selects and inspects the focused loaded object. Escape in the list clears selection. Dialog uses existing focus trap and Escape/backdrop/close restoration. Removed detail target falls back to the navigation region. Shared Hide/Show inspector retains position/selection/list scroll. Equal source scope, semantic access and queried target preserve the mounted session; equal timestamp/explanation rerenders do not reread or reset. Explicit same-target refresh restores still-existing selection and scroll; unknown/invalid new time bounds clear an invalid position. Actual context/adapter/owner changes retire old state and reads.

Existing history, advanced controls and revision comparison remain collapsed details. Original Operation identifiers remain `timeline.media-clip.add`, presentation `1.0`, and `ADD_MEDIA_CLIP_V1`; the navigation source never calls preview/apply or media access. Existing asset/capability boundary queries on NleWorkspace mount are separate from navigation.
