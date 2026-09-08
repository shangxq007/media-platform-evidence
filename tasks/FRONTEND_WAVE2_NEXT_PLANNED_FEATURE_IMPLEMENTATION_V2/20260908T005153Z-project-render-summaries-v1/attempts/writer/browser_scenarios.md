# Render Browser native browser scenarios — prepared, not run

Use a localhost frontend origin. The only opt-in is the exact, single query pair `rendersFixture=1`. These checks are intentionally prepared for Hermes/native browser execution and were not run by the implementation executor.

## Stable fixture URLs

- Unconfigured: `/operations/renders`
- Standard: `/operations/renders?rendersFixture=1`
- Empty: `/operations/renders?rendersFixture=1&rendersFixtureEmpty=1`
- Limited: `/operations/renders?rendersFixture=1&rendersFixtureLimited=1`
- Initial denied: `/operations/renders?rendersFixture=1&rendersFixtureAccess=denied`
- Initial unknown: `/operations/renders?rendersFixture=1&rendersFixtureAccess=unknown`
- Receipt failures: `/operations/renders?rendersFixture=1&rendersFixtureFailure={unavailable|denied|unknown|unsupported|error}`

Do not substitute a URL Project identifier. `projectId`, repeated `rendersFixture`, and non-localhost origins do not select or authorize a Project. The fixture Project is always `simulated-render-project`.

## Stable English labels and content

- Heading: `Project renders`
- Source scope label/value: `Source Project ID` / `simulated-render-project`
- Search: `Search render summaries`
- Status: `Render status`
- Sort: `Sort render summaries`
- Workflow labels on the same button: `Refresh render summaries`, `Cancel loading`, `Retry loading`
- Detail launcher: `Inspect render render-zeta`
- Dialog: `Render summary details`
- Dialog close: `Close render summary details`
- Fixture literals: `render-zeta`, `timeline-snapshot-zeta`, `Cinema <literal>`, `COMPLETED`

## Pointer checks

1. At the standard URL, verify the simulated-source warning and exact Project ID remain visible above the bounded-result statement.
2. Search for `Cinema <literal>`; verify only `render-zeta` remains and the literal angle brackets are text, not markup.
3. Clear search, choose status `FAILED`, and verify `render-beta`; change sort to `Render ID Z–A`.
4. Search for `no match`, verify `No matching render summaries`, activate `Reset filters`, and verify search/status/sort return to empty/all/`Render ID A–Z`.
5. Activate `Inspect render render-zeta`. Verify exactly the five safe fields (job ID, Project ID, Timeline snapshot ID, profile, status), no canonical controls or links, and literal text rendering. Close with the labelled close button and verify focus returns to the launcher.
6. At the unconfigured, denied, unknown, and receipt-failure URLs, verify no summary card remains and opaque source explanation text is rendered literally where supplied.

## Keyboard checks

1. At the standard URL, use Tab/Shift+Tab only to reach search, status, sort, and `Inspect render render-zeta`; verify visible focus throughout.
2. With `Inspect render render-zeta` focused, press Enter. Verify `Render summary details` opens, focus moves inside the shared dialog, Tab/Shift+Tab remain trapped, and no background control activates.
3. Press Escape. Verify the dialog closes and focus returns to the exact `Inspect render render-zeta` launcher.
4. Focus `Refresh render summaries` and activate it with Enter and Space in separate passes. Verify focus does not jump elsewhere as its label/state updates. The focused component tests provide the deterministic pending/failure/success timing coverage that the immediate browser fixture does not delay.

## Locale and layout checks

1. Switch `Product UI language` to `简体中文`. Stable labels include `项目渲染`, `搜索渲染摘要`, `渲染状态`, `渲染摘要排序`, `检查渲染 render-zeta`, and dialog `渲染摘要详情`. Verify IDs, profile, and status remain opaque source strings.
2. Capture the standard and detail views at a desktop viewport such as 1440×900.
3. Capture the same views at a narrow viewport such as 390×844. Verify the heading/actions and all controls stack without horizontal clipping, long IDs/profiles wrap, the dialog fits the viewport, and touch targets remain usable.
4. At the limited URL verify the text states a limited Project snapshot and makes no global inventory claim. At the empty URL verify the state is distinct from local no matches.
