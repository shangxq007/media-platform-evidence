"""Focused Chromium check of fixture-free local Workflow sketch.
CDP trusted pointer/key delivery; DOM reads/scroll/focus targeting and locale helper disclosed.
"""
from chromium_helpers import Browser
from pathlib import Path
import json,time,traceback
R=Path(__file__).parent
b=Browser()
b.raw('Page.addScriptToEvaluateOnNewDocument',{'source':"localStorage.setItem('dev_access_token','SIMULATED_LOCAL_ONLY_NOT_A_CREDENTIAL')"})
NODE='[data-testid="workflow-sketch-node"]'
COUNT='document.querySelectorAll('+json.dumps(NODE)+').length'
def target(expr):
 b.ev("document.querySelectorAll('[data-native-target]').forEach(e=>e.removeAttribute('data-native-target'))")
 b.ev('(()=>{const e=('+expr+');if(!e)throw Error("target missing");e.setAttribute("data-native-target","");e.scrollIntoView({block:"nearest",inline:"nearest"});})()')
 b.click('[data-native-target]')
def button(text):
 target('Array.from(document.querySelectorAll("button")).find(e=>e.textContent.trim()==='+json.dumps(text)+' || e.getAttribute("aria-label")==='+json.dumps(text)+')')
def field(label):return 'Array.from(document.querySelectorAll("label")).find(e=>e.textContent.trim()==='+json.dumps(label)+')?.querySelector("input")'
def typefield(label,text):
 target(field(label));b.raw('Input.dispatchKeyEvent',{'type':'keyDown','key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2});b.raw('Input.dispatchKeyEvent',{'type':'keyUp','key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2});b.raw('Input.insertText',{'text':text});time.sleep(.15)
def check(name,expr):b.check(name,expr)
try:
 b.viewport(1440,1000);b.nav('/w/workspace-1/projects/project-1/workflow');b.locale('en')
 b.wait('!!document.querySelector(".ff-workflow-sketch")')
 check('ordinary unconfigured route starts empty',COUNT+'===0')
 check('local unsaved nonexecuting notice', 'document.body.innerText.includes("This sketch is local, unsaved, and cannot run.")')
 for category in ['OPERATION','RENDER','REVIEW','WAIT','CONDITION','AGENT','INTEGRATION']:button('Add '+category+' card')
 check('seven category cards authored by native add clicks',COUNT+'===7')
 b.ev('document.querySelector('+json.dumps(NODE)+').focus()')
 check('DOM-targeted card focus does not select','document.querySelector('+json.dumps(NODE)+').getAttribute("aria-pressed")==="false"')
 b.key('\ue007')
 check('native Enter selects card', 'document.querySelector('+json.dumps(NODE)+').getAttribute("aria-pressed")==="true"')
 check('user-authored card is not mislabeled a clip fixture','!document.body.innerText.includes("Synthetic fixture")')
 x=b.ev(field('Local X')+'.value');b.key('\ue014')
 check('native ArrowRight moves exactly one step through shared Inspector','Number('+field('Local X')+'.value)===Number('+json.dumps(x)+')+24')
 typefield('Local title','<img src=x onerror=alert(1)> local plan')
 check('hostile title rendered literally, no injected element','document.querySelector('+json.dumps(NODE)+').getAttribute("aria-label")==="<img src=x onerror=alert(1)> local plan" && !document.querySelector('+json.dumps(NODE+' img')+')')
 button('Show primary node');b.shot('desktop-selected-en')
 button('Remove selected card')
 check('native removal removes one card',COUNT+'===6')
 check('removal retains stable focus','document.activeElement!==document.body && document.activeElement?.isConnected && !document.activeElement.disabled')
 button('Reset sketch');b.wait('!!document.querySelector("[role=dialog]")')
 check('shared discard dialog opened','document.querySelector("[role=dialog]").textContent.includes("Discard local sketch?")')
 b.key('\ue00c');check('native Escape preserves sketch',COUNT+'===6 && !document.querySelector("[role=dialog]")')
 button('Reset sketch');b.wait('!!document.querySelector("[role=dialog]")');button('Keep sketch')
 check('native cancel preserves sketch',COUNT+'===6 && !document.querySelector("[role=dialog]")')
 button('Reset sketch');b.wait('!!document.querySelector("[role=dialog]")');button('Discard sketch')
 check('native confirmed discard clears local cards',COUNT+'===0 && !document.querySelector("[role=dialog]")')
 check('discard focus is connected and enabled','document.activeElement!==document.body && document.activeElement?.isConnected && !document.activeElement.disabled')
 for i in range(12):button('Add WAIT card')
 check('capacity is explicit and enforced',COUNT+'===12 && document.body.innerText.includes("12-card limit reached")')
 check('capacity transition does not leave disabled focus','document.activeElement!==document.body && !document.activeElement.disabled')
 # Real document navigation retires the local sketch, without pretending to be same-document scope testing.
 b.nav('/w/workspace-1/projects/project-2/workflow');b.locale('en');b.wait('!!document.querySelector(".ff-workflow-sketch")')
 check('fresh project document has no retained cards',COUNT+'===0')
 b.viewport(390,844);b.locale('zh-CN');button('添加 OPERATION 卡片');button('添加 REVIEW 卡片')
 check('Chinese creator controls and cards',COUNT+'===2 && document.body.innerText.includes("本地排列草图")')
 check('narrow document has no horizontal overflow','document.documentElement.scrollWidth<=window.innerWidth')
 b.shot('narrow-zh-local-sketch')
 check('only simulated dashboard reads; no Workflow requests or mutations',json.dumps(not any(('/api/' in x['url'] and not x['url'].endswith('/api/v1/me/dashboard')) or x['method'] not in ['GET','HEAD'] for x in b.network)))
 b.ev('true')
 check('no uncaught runtime exceptions',json.dumps(not any(x.get('method')=='Runtime.exceptionThrown' for x in b.diagnostics)))
 (R/'BROWSER_DIAGNOSTICS.json').write_text(json.dumps(b.diagnostics,indent=2))
 (R/'ASSISTANCE.json').write_text(json.dumps({'browser':'headless Chromium','viewport_emulation':[[1440,1000],[390,844]],'CDP_focus_emulation':True,'DOM_assistance':['target identification/temporary attribute','scrollIntoView','one focus-only precondition','locale input/change helper'],'text_input':'CDP Input.insertText after native pointer/control-A','fixtures_injected':'simulated dashboard workspace and inert local auth marker; no Workflow nodes injected','real_backend':False,'scope_check':'real document navigation only; same-document store/lifetime retirement is unit/component coverage','untested':['physical device/touch/virtual keyboard','screen reader speech','OS IME','Firefox/Safari']},indent=2))
except Exception:
 (R/'FAILURE.txt').write_text(traceback.format_exc())
 try:b.shot('failed-state')
 except Exception:pass
 raise
finally:
 try:b.raw('Browser.close',{})
 except Exception:pass
