"""Final-tree Render browser: actual registered route, explicit simulated host."""
from pathlib import Path
import json,time,traceback
from chromium_helpers import Browser
from control import T,now
R=Path(__file__).parent;b=Browser();BASE='/operations/renders';FIXTURE=BASE+'?v7Fixture=1'
ESC='\ue00c';TAB='\ue004';ENTER='\ue007';DOWN='\ue015'
def text(s):return json.dumps(s,ensure_ascii=False)
def body_has(s):return 'document.body.innerText.includes('+text(s)+')'
def locate(selector,label=None,index=None):
 expr='(()=>{let es=[...document.querySelectorAll('+text(selector)+')].filter(e=>e.getClientRects().length'+(' && (e.getAttribute("aria-label")=== '+text(label)+' || e.textContent.trim()=== '+text(label)+')' if label else '')+');'+('es=[es['+str(index)+']];' if index is not None else '')+'if(es.length!==1||!es[0])throw Error("target count "+es.length);document.querySelectorAll("[data-native-target]").forEach(e=>e.removeAttribute("data-native-target"));es[0].dataset.nativeTarget="yes";es[0].scrollIntoView({block:"center"});})()'
 b.ev(expr);return '[data-native-target="yes"]'
def button(label):b.click(locate('.ff-render-browser button,[role=dialog] button',label))
def input_text(value):
 b.click(locate('.ff-render-browser input[type=search]'))
 for typ in ['keyDown','keyUp']:b.raw('Input.dispatchKeyEvent',{'type':typ,'key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2})
 b.raw('Input.insertText',{'text':value});time.sleep(.2)
def mode(value):b.ev('window.__V7Fixture.setOutcome('+text(value)+')')
def wait_button(label):b.wait('[...document.querySelectorAll(".ff-render-browser button")].some(e=>e.getAttribute("aria-label")==='+text(label)+'||e.textContent.trim()==='+text(label)+')')
def shot(name):b.shot(name)
def top():b.ev('document.querySelector(".ff-render-browser").scrollIntoView({block:"start"})')
def refresh():button('Refresh renders')
def normal():
 mode('normal');button('Retry loading');wait_button('Inspect render Courtyard <final>')
def inspect(name):
 button('Inspect render '+name);b.wait('!!document.querySelector("[role=dialog]")')
def dialog_has(s):return 'document.querySelector("[role=dialog]").innerText.includes('+text(s)+')'
try:
 b.viewport(1440,1000);b.raw('Page.navigate',{'url':'http://127.0.0.1:4198/'});time.sleep(.4)
 b.ev('localStorage.setItem("dev_access_token","SIMULATED_LOCAL_ONLY_NOT_A_CREDENTIAL")')
 b.nav(BASE);b.locale('en');b.wait(body_has('Render observability unavailable'))
 b.check('Ordinary final application is unavailable without a Render source',body_has('Render observability unavailable')+' && !window.__V7Fixture && !document.querySelector("[data-v7-host]")');top();shot('01-ordinary-unavailable-en')
 b.nav(FIXTURE);b.locale('en');wait_button('Inspect render Courtyard <final>')
 b.check('Explicit host discloses simulated Render identity and data',body_has('SIMULATED RENDER DATA')+' && !!document.querySelector("[data-v7-host]")')
 b.check('Supplied literal unknown status and valid progress are visible',body_has('VENDOR_WARMING')+' && '+body_has('3 of 8 shots · 37.5%')+' && !document.querySelector(".ff-render-browser final")')
 b.check('Fetch time is distinct from source update time',body_has('Last successful frontend fetch:')+' && '+body_has('Source update time: 2026-09-08T02:02:00Z'))
 top();shot('02-desktop-list-en')
 input_text('Courtyard');b.check('Native name search filters the supplied snapshot','document.querySelectorAll(".ff-render-browser-list > li").length===1')
 b.click(locate('.ff-render-controls select',index=0));b.key(DOWN);b.key(ENTER)
 b.click(locate('.ff-render-controls select',index=1));b.key(DOWN);b.key(ENTER)
 b.check('Native source status filter and stable local sort are selected','document.querySelectorAll(".ff-render-controls select")[0].value==="VENDOR_WARMING" && document.querySelectorAll(".ff-render-controls select")[1].value==="name-desc"')
 inspect('Courtyard <final>')
 b.check('Detail includes explicit task version attempt and bounded Artifact metadata',dialog_has('task-courtyard')+' && '+dialog_has('task-v3')+' && '+dialog_has('attempt-courtyard-1')+' && '+dialog_has('artifact-courtyard-preview')+' && '+dialog_has('more may exist'))
 b.check('Unknown artifact availability is literal and no Artifact open or download is enabled',dialog_has('PROCESSING?')+' && !document.querySelector("[role=dialog] a[href],[role=dialog] [download]")')
 shot('03-desktop-detail-en')
 b.ev('document.querySelector(".ff-render-artifacts").scrollIntoView({block:"center"})');time.sleep(.15)
 b.check('Supplied Artifact metadata is visually reachable inside detail','(()=>{const r=document.querySelector(".ff-render-artifacts").getBoundingClientRect();return r.top>=0 && r.top<innerHeight && r.bottom<=innerHeight})()');shot('03b-desktop-artifact-metadata-en');b.key(ESC)
 b.check('Native Escape closes detail and returns to the initiating task launcher','!document.querySelector("[role=dialog]") && document.activeElement.getAttribute("aria-label")==="Inspect render Courtyard <final>"')
 b.check('Return preserves populated query filter and sort','document.querySelector(".ff-render-browser input[type=search]").value==="Courtyard" && document.querySelectorAll(".ff-render-controls select")[0].value==="VENDOR_WARMING" && document.querySelectorAll(".ff-render-controls select")[1].value==="name-desc"')
 b.key(ENTER);b.check('Native Enter reopens the focused task','!!document.querySelector("[role=dialog]")');b.key(ESC)
 button('Reset filters');b.check('Native populated reset restores defaults and stable focus','document.querySelectorAll(".ff-render-browser-list > li").length===3 && document.activeElement.textContent.trim()==="Reset filters" && document.querySelectorAll(".ff-render-controls select")[1].value==="name-asc"')
 input_text('render-queued');b.check('Native ID search works without supplied task name','document.querySelectorAll(".ff-render-browser-list > li").length===1 && '+body_has('render-queued'));button('Reset filters')
 inspect('Social 原文')
 b.check('Failed task and attempt status remain separate with safe supplied failure',dialog_has('TASK_FAILED')+' && '+dialog_has('ATTEMPT_FAILED')+' && '+dialog_has('Encoder rejected supplied media')+' && '+dialog_has('MEDIA_REJECTED'))
 b.check('Invalid progress never clamps or invents percentage',dialog_has('Invalid supplied progress')+' && !'+dialog_has('140%')+' && !'+dialog_has('100%'))
 b.check('Explicit empty Artifact collection is not missing metadata',dialog_has('Source supplied an empty Artifact collection.'));shot('04-desktop-failed-attempt-en')
 b.ev('document.querySelector(".ff-render-attempts").scrollIntoView({block:"center"})');time.sleep(.15)
 b.check('Safe attempt failure is visually reachable','(()=>{const r=document.querySelector(".ff-render-attempts").getBoundingClientRect();return r.top>=0 && r.bottom<=innerHeight})()');shot('04b-desktop-attempt-failure-en');b.key(ESC)
 inspect('render-queued');b.check('Missing progress attempts and Artifacts remain unprovided',dialog_has('Progress was not supplied.')+' && '+dialog_has('Attempt history was not supplied.')+' && '+dialog_has('Artifact information was not supplied.'));shot('05-desktop-missing-metadata-en');b.key(ESC)
 mode('unknown-progress');refresh();wait_button('Inspect render Courtyard <final>');inspect('Courtyard <final>')
 b.check('Partial progress displays supplied value and unit without a percent',dialog_has('3 shots · total not supplied')+' && !'+dialog_has('37.5%'));shot('06-desktop-unknown-progress-en');b.key(ESC)
 mode('normal');refresh();wait_button('Inspect render Courtyard <final>')
 input_text('no such render');b.check('No matches remains distinct from empty source',body_has('No matching renders'));top();shot('07-desktop-no-matches-en');button('Reset filters')
 mode('empty');refresh();b.wait(body_has('No Renders in this snapshot'));b.check('Source empty is explicitly scoped',body_has('No Renders in this snapshot')+' && !'+body_has('No matching renders'));top();shot('08-desktop-empty-en')
 mode('normal');refresh();wait_button('Inspect render Courtyard <final>')
 mode('error');refresh();b.wait(body_has('Render source error'));b.check('Error clears old data while preserving native query Retry focus','!document.querySelector(".ff-render-browser-list") && document.activeElement.textContent.trim()==="Retry loading"');top();shot('09-desktop-error-en')
 normal();b.check('Native query retry restores data without an execution action','document.querySelectorAll(".ff-render-browser-list > li").length===3 && document.activeElement.textContent.trim()==="Refresh renders"')
 mode('pending');refresh();b.wait(body_has('Loading Render observability'));b.check('Pending read hides old data and offers native loading cancellation','!document.querySelector(".ff-render-browser-list") && document.activeElement.textContent.trim()==="Cancel loading"');top();shot('10-desktop-loading-en')
 button('Cancel loading');b.ev('window.__V7Fixture.resolvePending()');time.sleep(.3)
 b.check('Native cancellation fences a deliberately late successful adapter reply',body_has('Render loading cancelled')+' && !document.querySelector(".ff-render-browser-list")');top();shot('11-desktop-cancelled-en');normal()
 for state,title in [('denied','Render observability denied'),('unknown','Render observability access unknown'),('unsupported','Render observability unsupported'),('unavailable','Render observability unavailable'),('stale','Render snapshot is stale'),('invalid','Invalid Render snapshot'),('invalid-relationship','Invalid Render relationships')]:
  mode(state);refresh();b.wait(body_has(title));b.check('Explicit '+state+' read outcome is non-disclosing and distinct',body_has(title)+' && !document.querySelector(".ff-render-browser-list") && !'+body_has('artifact-courtyard-preview'));top();shot('12-desktop-'+state+'-en');normal()
 mode('bounded');refresh();wait_button('Inspect render Courtyard <final>');b.check('Bounded result does not claim a global total or invent pagination',body_has('bounded snapshot; more may exist')+' && document.querySelectorAll(".ff-render-browser-list > li").length===2');top();shot('13-desktop-bounded-en')
 mode('artifact-denied');refresh();wait_button('Inspect render Courtyard <final>');inspect('Courtyard <final>');b.check('Artifact denied is distinct from empty or inspectable metadata',dialog_has('Artifact metadata denied')+' && !'+dialog_has('artifact-courtyard-preview'));shot('14-desktop-artifact-denied-en');b.key(ESC)
 mode('artifact-stale');refresh();wait_button('Inspect render Courtyard <final>');inspect('Courtyard <final>');b.check('Artifact stale remains explicitly unavailable for inspection actions',dialog_has('Artifact metadata stale')+' && !document.querySelector("[role=dialog] a[href]")');b.key(ESC)
 mode('normal');refresh();wait_button('Inspect render Courtyard <final>')
 b.viewport(390,844);b.locale('zh-CN');top();b.check('Narrow Chinese Render entry fits document width',body_has('渲染可观测性')+' && document.documentElement.scrollWidth<=innerWidth');shot('15-narrow-list-zh')
 button('检查渲染 Courtyard <final>');b.wait('!!document.querySelector("[role=dialog]")');b.check('Narrow Chinese task dialog preserves source values',body_has('渲染详情')+' && '+dialog_has('task-courtyard')+' && document.documentElement.scrollWidth<=innerWidth');shot('16-narrow-detail-zh')
 b.ev('document.querySelector(".ff-render-artifacts").scrollIntoView({block:"center"})');time.sleep(.15)
 b.check('Narrow Chinese Artifact section is reachable without horizontal overflow','(()=>{const r=document.querySelector(".ff-render-artifacts").getBoundingClientRect();return r.top>=0 && r.top<innerHeight && document.documentElement.scrollWidth<=innerWidth})()');shot('16b-narrow-artifact-metadata-zh')
 b.key(ESC);b.check('Narrow native close restores the localized launcher','!document.querySelector("[role=dialog]") && document.activeElement.getAttribute("aria-label")==="检查渲染 Courtyard <final>"')
 b.locale('en');top();shot('17-narrow-list-en');input_text('Courtyard')
 b.click(locate('.ff-render-controls select',index=0));b.key(DOWN);b.key(ENTER)
 b.click(locate('.ff-render-controls select',index=1));b.key(DOWN);b.key(ENTER)
 inspect('Courtyard <final>');b.key(ESC)
 b.check('Narrow filtered detail return retains native focus and browsing criteria','document.activeElement.getAttribute("aria-label")==="Inspect render Courtyard <final>" && document.querySelector(".ff-render-browser input[type=search]").value==="Courtyard" && document.querySelectorAll(".ff-render-controls select")[0].value==="VENDOR_WARMING"')
 button('Reset filters');b.check('Narrow reset restores a populated snapshot','document.querySelectorAll(".ff-render-browser-list > li").length===3 && document.activeElement.textContent.trim()==="Reset filters"')
 input_text('no such narrow render');b.check('Narrow no-match remains recoverable',body_has('No matching renders'));top();shot('18-narrow-no-matches-en');button('Reset filters')
 mode('empty');refresh();b.wait(body_has('No Renders in this snapshot'));b.check('Narrow source empty remains distinct',body_has('No Renders in this snapshot'));top();shot('19-narrow-empty-en')
 mode('normal');refresh();wait_button('Inspect render Courtyard <final>');mode('error');refresh();b.wait(body_has('Render source error'));b.check('Narrow error clears content and retains native Retry focus','!document.querySelector(".ff-render-browser-list") && document.activeElement.textContent.trim()==="Retry loading"');top();shot('20-narrow-error-en');normal()
 b.check('Narrow native retry recovers without document horizontal overflow','document.querySelectorAll(".ff-render-browser-list > li").length===3 && document.documentElement.scrollWidth<=innerWidth');top();shot('21-narrow-recovered-en')
 requests=[x for x in b.network if '/api/' in x['url']];allowed=all(x['method']=='GET' and '/api/v1/me/dashboard' in x['url'] for x in requests)
 (R/'APPLICATION_TRAFFIC.json').write_text(json.dumps({'requests':requests,'allowed_only_simulated_dashboard_reads':allowed,'feature_http_requests':0,'http_mutations':sum(x['method']!='GET' for x in requests)},indent=2));assert allowed,requests
 (R/'FIXTURE_READ_CALLS.json').write_text(json.dumps(b.ev('window.__V7Fixture.calls'),indent=2))
 (R/'ASSISTANCE.json').write_text(json.dumps({'tree':T,'native':'CDP pointer, Escape/Enter/ArrowDown/Control+A and Input.insertText; native select keyboard delivery','dom_assistance':['DOM text/rectangle/state queries','text locator annotations and scrollIntoView','locale DOM helper','inert auth marker in disposable loopback localStorage','explicit external adapter outcome/delay/late resolution control, not real server'],'fixture':'same final multi-entry build; ordinary application unavailable; external RenderBrowserProvider around exact registered route tree','focus_emulation':True,'viewports':[[1440,1000],[390,844]],'limits':['headless desktop viewport emulation only','document width is not mobile certification; internal scrolling visible','no physical device/touch/keyboard/OS IME/screenreader acceptance','no real backend/auth/permission integration','owner retirement, relationship breadth and detailed context races additionally exercised in component tests'],'checks':len(b.checks),'timestamp':now()},ensure_ascii=False,indent=2))
 print('RENDER_NATIVE_CHECKS',len(b.checks),flush=True)
except BaseException:
 (R/'FAILURE.txt').write_text(traceback.format_exc())
 try:shot('failure')
 except Exception:pass
 raise
finally:
 try:b.raw('Browser.close',{})
 except Exception:pass
 b.ws.close()
