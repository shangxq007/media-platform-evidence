"""Focused V5 local-history browser checks; no product state injection."""
from pathlib import Path
import json,time,traceback
from chromium_helpers import Browser
from control import T,now
R=Path(__file__).parent;b=Browser();BASE='/w/workspace-1/projects/simulated-project/canvas'
ESC='\ue00c';TAB='\ue004';ENTER='\ue007';RIGHT='\ue014'
U='[data-canvas-history="undo"]';D='[data-canvas-history="redo"]';N='[data-canvas-node="project-node"]'
STATE='JSON.stringify([...document.querySelectorAll("[data-canvas-node]")].map(e=>({id:e.dataset.canvasNode,title:e.querySelector("strong").textContent,x:e.style.left,y:e.style.top})))'
def state():return b.ev(STATE)
def check_state(name,expected):b.check(name,STATE+'==='+json.dumps(expected))
def disabled(selector):return 'document.querySelector('+json.dumps(selector)+').getAttribute("aria-disabled")==="true"'
def btn(label):
 b.ev('(()=>{const es=[...document.querySelectorAll("button")].filter(e=>e.textContent.trim()==='+json.dumps(label)+'&&e.getClientRects().length);if(es.length!==1)throw Error("button count "+es.length);document.querySelectorAll("[data-native-target]").forEach(e=>e.removeAttribute("data-native-target"));es[0].dataset.nativeTarget="yes";es[0].scrollIntoView({block:"nearest"});})()');b.click('[data-native-target="yes"]')
def chord(key):
 for typ in ['keyDown','keyUp']:b.raw('Input.dispatchKeyEvent',{'type':typ,'key':key,'code':'Key'+key.upper(),'windowsVirtualKeyCode':ord(key.upper()),'modifiers':2})
 time.sleep(.15)
def rename(text):
 b.click('#selection-inspector input:not([type="number"])');chord('a');b.raw('Input.insertText',{'text':text});time.sleep(.15)
def pointer(typ,x,y):
 b.raw('Input.dispatchMouseEvent',{'type':typ,'x':x,'y':y,'button':'left','buttons':0 if typ=='mouseReleased' else 1,'clickCount':1,'modifiers':0})
def drag_start():
 q=b.ev('(()=>{const e=document.querySelector('+json.dumps(N)+'),r=e.getBoundingClientRect();return {x:r.left+35,y:r.top+35}})()')
 pointer('mousePressed',q['x'],q['y']);time.sleep(.1)
 pointer('mouseMoved',q['x']+40,q['y']+24);time.sleep(.1)
 return q
try:
 b.viewport(1440,1000);b.raw('Page.navigate',{'url':'http://127.0.0.1:4198/'});time.sleep(.3)
 b.ev('localStorage.setItem("dev_access_token","SIMULATED_LOCAL_ONLY_NOT_A_CREDENTIAL")')
 b.nav(BASE);b.locale('en');b.wait('!!document.querySelector('+json.dumps(U)+')');initial=state()
 b.check('Empty local history has unavailable Undo and Redo',disabled(U)+'&&'+disabled(D));b.shot('01-desktop-empty-en')
 b.click(U);b.key(ENTER);check_state('Unavailable Undo is a no-op under pointer and Enter',initial)
 b.check('Unavailable control retains native focus','document.activeElement.matches('+json.dumps(U)+')')
 b.click(N);b.key(RIGHT);moved=state();b.check('Native arrow changes local placement',STATE+'!=='+json.dumps(initial))
 camera=b.ev('document.querySelector(".ff-canvas-viewport").style.transform')
 b.click(U);check_state('Pointer Undo restores keyboard movement',initial)
 b.check('Undo preserves current selection and camera','document.querySelector('+json.dumps(N)+').getAttribute("aria-pressed")==="true" && document.querySelector(".ff-canvas-viewport").style.transform==='+json.dumps(camera))
 b.check('Last Undo remains focused and communicates unavailability','document.activeElement.matches('+json.dumps(U)+') && '+disabled(U))
 b.key(TAB);b.check('Native Tab reaches Redo','document.activeElement.matches('+json.dumps(D)+')');b.key(ENTER);check_state('Native Enter redoes the exact local placement',moved)
 b.key(' ');check_state('Unavailable Redo Space does not replay twice',moved)
 rename('<b>Creator draft</b>');renamed=state();b.check('Native text input safely renders title, not HTML','document.querySelector('+json.dumps(N)+').getAttribute("aria-label")==="<b>Creator draft</b>" && !document.querySelector("[data-canvas-node] b")')
 b.click(U);check_state('Undo title leaves preceding position edit intact',moved)
 b.check('Shared Inspector refreshes after Undo','document.querySelector("#selection-inspector input:not([type=number])").value==="Project reference"')
 b.click(D);check_state('Redo restores exact safe title',renamed);b.shot('02-desktop-restored-en')
 # Palette uses the already-accepted Commands entry and contextual dispatcher.
 b.click('.ff-shell-toolbar button:has(kbd)');b.wait('!!document.querySelector("[role=dialog]")');btn('Undo local edit');check_state('Contextual palette Undo uses the same local history',moved)
 b.click('.ff-shell-toolbar button:has(kbd)');btn('Redo local edit');check_state('Contextual palette Redo uses the same local history',renamed)
 b.click(U);rename('New branch');branched=state();b.check('New title edit discards redo branch',disabled(D));b.click(D);check_state('Discarded future cannot be reapplied',branched)
 b.click('.ff-shell-toolbar button:has(kbd)');b.check('Canonical commands remain unavailable','[...document.querySelectorAll("[role=dialog] button")].filter(e=>e.disabled).length>=3');b.key(ESC)
 # Fresh session isolates one completed group drag and one canceled preview.
 b.nav(BASE);b.locale('en');b.click(N)
 b.call('input.performActions',{'context':b.context,'actions':[{'type':'key','id':'keyboard','actions':[{'type':'keyDown','value':'\ue009'}]}]})
 b.click('[data-canvas-node="note-node"]');b.call('input.releaseActions',{});b.wait('document.querySelectorAll("[data-canvas-node][aria-pressed=true]").length===2')
 before=state();q=drag_start();b.check('Group preview exists before completion',STATE+'!=='+json.dumps(before));pointer('mouseReleased',q['x']+40,q['y']+24);time.sleep(.2);group=state()
 b.check('Completed group drag changes both nodes','(()=>{const a='+before+',z='+group+';return a.every((e,i)=>e.x!==z[i].x&&e.y!==z[i].y)})()')
 b.click(U);check_state('One Undo restores entire group drag atomically',before);b.check('Group undo exhausts single edit and keeps both selected',disabled(U)+'&&document.querySelectorAll("[data-canvas-node][aria-pressed=true]").length===2')
 b.click(D);check_state('One Redo restores entire group placement',group)
 q=drag_start();b.check('Canceled gesture test has a real preview',STATE+'!=='+json.dumps(group));b.key(ESC);pointer('mouseReleased',q['x']+40,q['y']+24);time.sleep(.15);check_state('Escape discards preview without another edit',group)
 b.click(U);check_state('Undo after canceled preview reaches original group state',before);b.check('Canceled preview adds no history',disabled(U));b.shot('03-desktop-group-undone')
 b.nav(BASE);b.check('Reload clears local history',disabled(U)+'&&'+disabled(D));check_state('Reload restores initial local layout',initial)
 b.viewport(390,844);b.locale('zh-CN');b.ev('document.querySelector("[data-canvas-history]").scrollIntoView({block:"center"})')
 b.check('Narrow Chinese history controls fit without document overflow','document.documentElement.scrollWidth<=innerWidth && [...document.querySelectorAll("[data-canvas-history]")].every(e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth}) && document.querySelector('+json.dumps(U)+').textContent==="撤销本地编辑"');b.shot('04-narrow-empty-zh')
 b.click(N);b.key(RIGHT);narrowMoved=state();b.ev('document.querySelector("[data-canvas-history]").scrollIntoView({block:"center"})');b.click(U);b.key(TAB);b.key(ENTER);check_state('Narrow native Undo then keyboard Redo restores edit',narrowMoved);b.shot('05-narrow-restored-zh')
 b.locale('en');b.ev('document.querySelector("[data-canvas-history]").scrollIntoView({block:"center"})');b.shot('06-narrow-en')
 b.raw('Runtime.evaluate',{'expression':'document.title','returnByValue':True})
 requests=[x for x in b.network if '/api/' in x['url']];allowed=all(x['method']=='GET' and '/api/v1/me/dashboard' in x['url'] for x in requests)
 (R/'APPLICATION_TRAFFIC.json').write_text(json.dumps({'requests':requests,'allowed_only_simulated_dashboard_reads':allowed,'feature_mutations':sum(x['method']!='GET' for x in requests)},indent=2));assert allowed,requests
 (R/'ASSISTANCE.json').write_text(json.dumps({'tree':T,'native':'CDP pointer clicks, held-left group drag, Escape, Tab/Enter/Space, arrow, Control+A and Input.insertText','dom_assistance':['DOM state/rectangle queries','text-based locator annotations and scrollIntoView','locale DOM change/input helper','inert auth marker in disposable loopback localStorage'],'fixture':'external simulated dashboard host context only; no history/source/adapter injection','focus_emulation':True,'viewport':[[1440,1000],[390,844]],'limitations':['headless Chromium only','narrow desktop viewport emulation, not physical/touch/virtual keyboard','no OS IME or screen reader','no real backend/auth integration','owner retirement and 50-entry capacity are component/model tests, not repeated historical browser lifecycle qualification'],'checks':len(b.checks),'timestamp':now()},ensure_ascii=False,indent=2))
 print('HISTORY_NATIVE_CHECKS',len(b.checks),flush=True)
except BaseException:
 (R/'FAILURE.txt').write_text(traceback.format_exc())
 try:b.shot('failure')
 except Exception:pass
 raise
finally:
 try:b.raw('Browser.close',{})
 except Exception:pass
 b.ws.close()
