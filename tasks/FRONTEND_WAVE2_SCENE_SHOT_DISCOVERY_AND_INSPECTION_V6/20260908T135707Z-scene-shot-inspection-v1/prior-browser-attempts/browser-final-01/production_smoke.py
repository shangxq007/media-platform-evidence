"""Final-tree Scene/Shot browser evidence, explicit external fixture host."""
from pathlib import Path
import json,time,traceback
from chromium_helpers import Browser
from control import T,now
R=Path(__file__).parent;b=Browser();BASE='/w/workspace-1/projects/simulated-project/production';FIXTURE=BASE+'?v6Fixture=1'
ESC='\ue00c';TAB='\ue004';ENTER='\ue007';DOWN='\ue015'
def text(s):return json.dumps(s,ensure_ascii=False)
def body_has(s):return 'document.body.innerText.includes('+text(s)+')'
def locate(selector,label=None):
 expr='(()=>{const es=[...document.querySelectorAll('+text(selector)+')].filter(e=>e.getClientRects().length'+(' && (e.getAttribute("aria-label")=== '+text(label)+' || e.textContent.trim()=== '+text(label)+')' if label else '')+');if(es.length!==1)throw Error("target count "+es.length);document.querySelectorAll("[data-native-target]").forEach(e=>e.removeAttribute("data-native-target"));es[0].dataset.nativeTarget="yes";es[0].scrollIntoView({block:"center"});})()'
 b.ev(expr);return '[data-native-target="yes"]'
def button(label):b.click(locate('.ff-production-browser button,[role=dialog] button',label))
def input_text(value):
 b.click(locate('.ff-production-browser input[type=search]'))
 for typ in ['keyDown','keyUp']:b.raw('Input.dispatchKeyEvent',{'type':typ,'key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2})
 b.raw('Input.insertText',{'text':value});time.sleep(.2)
def mode(value):b.ev('window.__V6Fixture.setOutcome('+text(value)+')')
def wait_button(label):b.wait('[...document.querySelectorAll(".ff-production-browser button")].some(e=>e.getAttribute("aria-label")==='+text(label)+'||e.textContent.trim()==='+text(label)+')')
def shot(name):b.shot(name)
def top():b.ev('document.querySelector(".ff-production-browser").scrollIntoView({block:"start"})')
def refresh():button('Refresh production snapshot')
try:
 b.viewport(1440,1000);b.raw('Page.navigate',{'url':'http://127.0.0.1:4198/'});time.sleep(.4)
 b.ev('localStorage.setItem("dev_access_token","SIMULATED_LOCAL_ONLY_NOT_A_CREDENTIAL")')
 b.nav(BASE);b.locale('en');b.wait(body_has('Production snapshot unavailable'))
 b.check('Ordinary final application is unavailable without any fixture source',body_has('Production snapshot unavailable')+' && !window.__V6Fixture && !document.querySelector("[data-v6-host]")');top();shot('01-ordinary-unavailable-en')
 b.nav(FIXTURE);b.locale('en');wait_button('Browse scene Courtyard <scene>')
 b.check('Explicit fixture host and simulated disclosure are visible',body_has('SIMULATED PRODUCTION DATA')+' && !!document.querySelector("[data-v6-host]")')
 b.check('Approved literal Scene labels render safely, not as HTML','document.querySelectorAll(".ff-production-scene-list > li").length===3 && !document.querySelector(".ff-production-scene-list scene")');top();shot('02-desktop-scenes-en')
 input_text('Courtyard');b.check('Native search filters only the supplied Scene snapshot','document.querySelectorAll(".ff-production-scene-list > li").length===1 && '+body_has('Courtyard <scene>'))
 b.click(locate('.ff-production-controls label:first-of-type select'));b.key(DOWN);b.key(ENTER)
 b.check('Native status selection uses supplied status','document.querySelector(".ff-production-controls label:first-of-type select").value==="APPROVED"')
 b.click(locate('.ff-production-controls label:last-of-type select'));b.key(DOWN);b.key(ENTER)
 b.check('Native sort selection remains local','document.querySelector(".ff-production-controls label:last-of-type select").value==="name-desc"')
 button('Browse scene Courtyard <scene>')
 b.check('Native Scene selection exposes only explicitly related Shots',body_has('Arrival shot')+' && !'+body_has('Studio insert')+' && document.querySelector("button[aria-pressed=true]").getAttribute("aria-label")==="Browse scene Courtyard <scene>"')
 button('Inspect shot Arrival shot');b.wait('!!document.querySelector("[role=dialog]")')
 b.check('Shot dialog shows supplied identity version and safe reference, no arbitrary URL',body_has('arrival-v2')+' && '+body_has('render-arrival')+' && !document.querySelector("[role=dialog] a[href]")');shot('03-desktop-shot-detail-en')
 b.key(ESC)
 b.check('Native Escape closes dialog and restores Shot launcher focus','!document.querySelector("[role=dialog]") && document.activeElement.getAttribute("aria-label")==="Inspect shot Arrival shot"')
 b.check('Return retains query status sort and Scene selection','document.querySelector(".ff-production-browser input[type=search]").value==="Courtyard" && document.querySelector(".ff-production-controls label:first-of-type select").value==="APPROVED" && document.querySelector(".ff-production-controls label:last-of-type select").value==="name-desc" && !!document.querySelector("button[aria-pressed=true]")')
 button('Inspect scene Courtyard <scene>');b.key(ESC);b.key(TAB)
 b.check('Native Tab distinguishes focus from Scene selection','document.activeElement.getAttribute("aria-label")==="Inspect shot Arrival shot" && !!document.querySelector("button[aria-pressed=true]")')
 b.key(ENTER);b.check('Native Enter activates focused Shot inspection','!!document.querySelector("[role=dialog]") && '+body_has('arrival-v2'));b.key(ESC)
 input_text('no such scene');b.check('No matches is distinct from an empty inventory',body_has('No matching scenes'));top();shot('04-desktop-no-matches-en')
 button('Reset filters');b.check('Native reset restores populated Scene browse defaults','document.querySelectorAll(".ff-production-scene-list > li").length===3 && document.querySelector(".ff-production-browser input[type=search]").value==="" && document.querySelector(".ff-production-controls label:first-of-type select").value===""')
 button('Browse scene Silent scene');b.check('Scene without explicit related Shots is an honest empty relation state',body_has('No related shots in this snapshot'));button('Inspect scene Silent scene');b.check('Missing projected metadata remains not supplied',body_has('Not supplied'));b.key(ESC)
 mode('empty');refresh();b.wait(body_has('No scenes in this snapshot'));b.check('Source empty result differs from no search matches',body_has('No scenes in this snapshot')+' && !'+body_has('No matching scenes'));top();shot('05-desktop-empty-en')
 mode('normal');refresh();wait_button('Browse scene Courtyard <scene>')
 mode('error');refresh();b.wait(body_has('Production snapshot error'));b.check('Source error removes old Scene content and keeps retry focus',body_has('Production snapshot error')+' && !document.querySelector(".ff-production-scene-list") && document.activeElement.textContent.trim()==="Retry loading"');top();shot('06-desktop-error-en')
 mode('normal');button('Retry loading');wait_button('Browse scene Courtyard <scene>');b.check('Native retry recovers with stable workflow control focus','document.activeElement.textContent.trim()==="Refresh production snapshot" && document.querySelectorAll(".ff-production-scene-list > li").length===3')
 mode('pending');refresh();b.wait(body_has('Loading production snapshot'));b.check('Loading hides old data and offers native cancellation','!document.querySelector(".ff-production-scene-list") && document.activeElement.textContent.trim()==="Cancel loading"');top();shot('07-desktop-loading-en')
 button('Cancel loading');b.ev('window.__V6Fixture.resolvePending()');time.sleep(.3)
 b.check('Native cancellation fences a deliberately late successful adapter reply','!document.querySelector(".ff-production-scene-list") && document.activeElement.textContent.trim()==="Retry loading"');top();shot('08-desktop-cancelled-en')
 mode('normal');button('Retry loading');wait_button('Browse scene Courtyard <scene>')
 mode('bounded');refresh();b.wait(body_has('bounded snapshot; more may exist'));b.check('Bounded inventory never claims global completeness',body_has('bounded snapshot; more may exist'));top();shot('09-desktop-bounded-en')
 mode('denied');refresh();b.wait('!document.querySelector(".ff-production-scene-list") && '+body_has('SIMULATED controlled source result'));b.check('Denied source result is non-disclosing','!document.querySelector(".ff-production-scene-list") && !'+body_has('Arrival shot'))
 mode('normal');button('Retry loading');wait_button('Browse scene Courtyard <scene>')
 mode('invalid');refresh();b.wait(body_has('Invalid production snapshot'));b.check('Invalid receipt is distinct from a retryable source error',body_has('Invalid production snapshot')+' && !'+body_has('Production snapshot error')+' && !document.querySelector(".ff-production-scene-list")');top();shot('14-desktop-invalid-en')
 mode('normal');button('Retry loading');wait_button('Browse scene Courtyard <scene>')
 mode('stale');refresh();b.wait(body_has('Production snapshot is stale'));b.check('Explicit stale snapshot clears previous content',body_has('Production snapshot is stale')+' && !document.querySelector(".ff-production-scene-list")');top();shot('15-desktop-stale-en')
 mode('normal');button('Retry loading');wait_button('Browse scene Courtyard <scene>')
 b.viewport(768,1024);top();b.check('Tablet viewport has no document horizontal overflow','document.documentElement.scrollWidth<=innerWidth');shot('10-tablet-scenes-en')
 b.viewport(390,844);b.locale('zh-CN');top();b.check('Narrow Chinese Scene discovery fits document width',body_has('场景与镜头')+' && document.documentElement.scrollWidth<=innerWidth');shot('11-narrow-scenes-zh')
 button('浏览场景 Courtyard <scene>');button('检查镜头 Arrival shot');b.wait('!!document.querySelector("[role=dialog]")')
 b.check('Narrow Chinese Shot dialog shows supplied values without horizontal overflow',body_has('镜头详情')+' && '+body_has('arrival-v2')+' && document.documentElement.scrollWidth<=innerWidth');shot('12-narrow-shot-zh')
 b.key(ESC);b.check('Narrow native close returns to the Shot launcher','!document.querySelector("[role=dialog]") && document.activeElement.getAttribute("aria-label")==="检查镜头 Arrival shot"')
 b.locale('en');top();shot('13-narrow-scenes-en')
 b.raw('Runtime.evaluate',{'expression':'document.title','returnByValue':True})
 requests=[x for x in b.network if '/api/' in x['url']]
 allowed=all(x['method']=='GET' and '/api/v1/me/dashboard' in x['url'] for x in requests)
 (R/'APPLICATION_TRAFFIC.json').write_text(json.dumps({'requests':requests,'allowed_only_simulated_dashboard_reads':allowed,'feature_http_requests':0,'http_mutations':sum(x['method']!='GET' for x in requests)},indent=2));assert allowed,requests
 (R/'FIXTURE_READ_CALLS.json').write_text(json.dumps(b.ev('window.__V6Fixture.calls'),indent=2))
 (R/'ASSISTANCE.json').write_text(json.dumps({'tree':T,'native':'CDP pointer clicks, Escape/Tab/Enter/ArrowDown and Control+A/Input.insertText; select option keyboard delivery','dom_assistance':['DOM state/rectangle queries','text-based locator annotations and scrollIntoView','locale DOM change/input helper','inert auth marker in disposable localStorage','explicit external fixture adapter outcome/delay/resolution control; not product state injection'],'fixture':'same final multi-entry build: ordinary app remains unavailable; external host wraps exact registered route tree with ProductionSourceProvider and explicitly supplied simulation identity/data','focus_emulation':True,'viewports':[[1440,1000],[768,1024],[390,844]],'limits':['headless Chromium desktop viewport emulation','no physical device/touch/virtual keyboard','no OS IME/screenreader acceptance','no real backend/auth integration','retirement/race breadth is unit/component evidence, not physical bfcache qualification'],'checks':len(b.checks),'timestamp':now()},ensure_ascii=False,indent=2))
 print('PRODUCTION_NATIVE_CHECKS',len(b.checks),flush=True)
except BaseException:
 (R/'FAILURE.txt').write_text(traceback.format_exc())
 try:shot('failure')
 except Exception:pass
 raise
finally:
 try:b.raw('Browser.close',{})
 except Exception:pass
 b.ws.close()
