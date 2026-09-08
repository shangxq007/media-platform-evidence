from pathlib import Path
import json,time,traceback
from chromium_helpers import Browser
from control import T,now
R=Path(__file__).parent;b=Browser();BASE='/w/workspace-1/projects/simulated-project/canvas'
ESC='\ue00c';TAB='\ue004';ENTER='\ue007'
def btn(label):
 expr='(()=>{const es=[...document.querySelectorAll("button")].filter(e=>e.textContent.trim()==='+json.dumps(label)+' && e.getClientRects().length);if(es.length!==1)throw Error("button count '+label+' "+es.length);document.querySelectorAll("[data-native-target]").forEach(e=>e.removeAttribute("data-native-target"));es[0].dataset.nativeTarget="yes";es[0].scrollIntoView({block:"nearest"});})()'
 b.ev(expr);b.click('[data-native-target="yes"]')
def toolbar_commands():b.click('.ff-shell-toolbar button:has(kbd)')
def chord(key='k',alt=False,shift=False,meta=False):
 mods=0;held=[]
 for yes,name,code,vk,bit in [(not meta,'Control','ControlLeft',17,2),(meta,'Meta','MetaLeft',91,4),(alt,'Alt','AltLeft',18,1),(shift,'Shift','ShiftLeft',16,8)]:
  if yes:
   mods|=bit;held.append((name,code,vk,bit));b.raw('Input.dispatchKeyEvent',{'type':'keyDown','key':name,'code':code,'windowsVirtualKeyCode':vk,'modifiers':mods})
 for typ in ['keyDown','keyUp']:b.raw('Input.dispatchKeyEvent',{'type':typ,'key':key,'code':'Key'+key.upper(),'windowsVirtualKeyCode':ord(key.upper()),'modifiers':mods})
 for name,code,vk,bit in reversed(held):
  mods&=~bit;b.raw('Input.dispatchKeyEvent',{'type':'keyUp','key':name,'code':code,'windowsVirtualKeyCode':vk,'modifiers':mods})
 time.sleep(.15)
def choose(index):
 # Native select keyboard navigation; no JS value/onChange injection.
 b.click('.ff-shortcut-editor select');b.raw('Input.dispatchKeyEvent',{'type':'keyDown','key':'Home','code':'Home','windowsVirtualKeyCode':36});b.raw('Input.dispatchKeyEvent',{'type':'keyUp','key':'Home','code':'Home','windowsVirtualKeyCode':36})
 for _ in range(index):b.key('\ue015')
 b.key(ENTER)
def width_ok():return 'document.documentElement.scrollWidth <= innerWidth && [...document.querySelectorAll(".ff-shortcut-editor button,.ff-shortcut-editor select")].every(e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight})'
try:
 b.viewport(1440,1000);b.raw('Page.navigate',{'url':'http://127.0.0.1:4198/'});time.sleep(.3)
 b.ev('localStorage.setItem("dev_access_token","SIMULATED_LOCAL_ONLY_NOT_A_CREDENTIAL")')
 b.nav(BASE);b.locale('en');b.wait('document.querySelectorAll("[data-canvas-node]").length > 0')
 b.check('Default binding is discoverable with accessible direct Commands fallback','document.querySelector(".ff-shell-toolbar button:has(kbd)").textContent.includes("Mod+K")')
 b.click('[data-canvas-node]');b.wait('!!document.querySelector("[data-canvas-node][aria-pressed=true]")');selected=b.ev('document.querySelector("[data-canvas-node][aria-pressed=true]").dataset.canvasNode')
 btn('Keyboard shortcut');b.wait('!!document.querySelector(".ff-shortcut-editor")')
 b.check('Shared editor owns initial focus and discloses unsaved session','document.activeElement.matches(".ff-shortcut-editor select") && document.querySelector(".ff-shortcut-editor").textContent.includes("not saved") && document.querySelectorAll("[role=dialog]").length===1')
 b.shot('01-desktop-editor-en')
 choose(1);b.check('Native select chooses alternate draft without applying','document.querySelector(".ff-shortcut-editor select").value==="Mod+Alt+K" && document.querySelector(".ff-shell-toolbar kbd").textContent==="Mod+K"')
 btn('Cancel');b.check('Cancel preserves default and restores launcher focus','!document.querySelector("[role=dialog]") && document.activeElement.textContent==="Keyboard shortcut" && document.querySelector(".ff-shell-toolbar kbd").textContent==="Mod+K"')
 btn('Keyboard shortcut');choose(1);btn('Apply shortcut')
 b.check('Apply changes binding/help without clearing shared selection','document.querySelector(".ff-shell-toolbar kbd").textContent==="Mod+Alt+K" && !!document.querySelector("[data-canvas-node][aria-pressed=true]") && document.activeElement.textContent==="Keyboard shortcut"')
 chord();b.check('Old default chord no longer opens palette','!document.querySelector("[role=dialog]")')
 chord(alt=True);b.check('New native chord opens existing palette','!!document.querySelector("[role=dialog]") && !document.querySelector(".ff-shortcut-editor")')
 b.shot('02-desktop-palette-remapped')
 # Existing selection-command label from accepted catalog/source.
 btn(b.ev('[...document.querySelectorAll("[role=dialog] button")].find(e=>e.textContent.trim().startsWith("Inspect " )).textContent.trim()'));b.check('Remapped palette dispatches existing Inspect and preserves selected node','!!document.querySelector("#selection-inspector") && document.querySelector("[data-canvas-node][aria-pressed=true]").dataset.canvasNode==='+json.dumps(selected))
 btn('Keyboard shortcut');chord(alt=True)
 b.check('Editor select and modal retain precedence over active global chord','document.querySelectorAll("[role=dialog]").length===1 && !!document.querySelector(".ff-shortcut-editor")')
 b.key(ESC);b.check('Escape closes editor and restores initiating control','!document.querySelector("[role=dialog]") && document.activeElement.textContent==="Keyboard shortcut"')
 btn('Keyboard shortcut')
 # Backdrop native pointer, away from centered dialog.
 b.raw('Input.dispatchMouseEvent',{'type':'mousePressed','x':4,'y':4,'button':'left','clickCount':1});b.raw('Input.dispatchMouseEvent',{'type':'mouseReleased','x':4,'y':4,'button':'left','clickCount':1});time.sleep(.15)
 b.check('Backdrop cancels without losing launcher focus','!document.querySelector("[role=dialog]") && document.activeElement.textContent==="Keyboard shortcut"')
 chord(alt=True,shift=True);b.check('Extra Shift modifier is not intercepted','!document.querySelector("[role=dialog]")')
 toolbar_commands();b.check('Canonical commands remain truthfully unavailable','[...document.querySelectorAll("[role=dialog] button")].filter(e=>e.disabled).length>=3 && document.querySelector("[role=dialog]").textContent.includes("cannot be applied here yet")')
 b.key(ESC)
 btn('Keyboard shortcut');btn('Restore default');chord(alt=True);b.check('Reset retires alternate binding','document.querySelector(".ff-shell-toolbar kbd").textContent==="Mod+K" && !document.querySelector("[role=dialog]")')
 chord();b.check('Reset default is genuinely active','!!document.querySelector("[role=dialog]")');b.key(ESC)
 btn('Keyboard shortcut');choose(2);btn('Apply shortcut');b.nav(BASE);b.check('Reload/remount discards unsaved shortcut override','document.querySelector(".ff-shell-toolbar kbd").textContent==="Mod+K"')
 b.viewport(390,844);b.locale('zh-CN');btn('键盘快捷键');b.check('Narrow Chinese editor and controls fit viewport',width_ok());b.shot('03-narrow-editor-zh')
 # Entry select -> Shift+Tab wraps to close button; Tab returns to select.
 b.raw('Input.dispatchKeyEvent',{'type':'keyDown','key':'Tab','code':'Tab','windowsVirtualKeyCode':9,'modifiers':8});b.raw('Input.dispatchKeyEvent',{'type':'keyUp','key':'Tab','code':'Tab','windowsVirtualKeyCode':9,'modifiers':0})
 b.check('Native keyboard focus stays in shared modal','!!document.activeElement.closest(".ff-shortcut-editor")');b.key(TAB)
 choose(2);btn('应用快捷键');chord('p',alt=True);b.check('Narrow Chinese remap opens existing palette with native chord','!!document.querySelector("[role=dialog]") && document.querySelector(".ff-shell-toolbar kbd").textContent==="Mod+Alt+P"');b.shot('04-narrow-palette-zh');b.key(ESC)
 btn('键盘快捷键');btn('恢复默认');b.check('Chinese reset restores default without persistence','document.querySelector(".ff-shell-toolbar kbd").textContent==="Mod+K"');b.shot('05-narrow-reset-zh')
 b.locale('en');btn('Keyboard shortcut');b.check('Narrow English editor and controls fit viewport',width_ok());b.shot('06-narrow-editor-en');b.key(ESC)
 b.raw('Runtime.evaluate',{'expression':'document.title','returnByValue':True})
 application=[x for x in b.network if '/api/' in x['url']];allowed=all(x['method']=='GET' and '/api/v1/me/dashboard' in x['url'] for x in application)
 (R/'APPLICATION_TRAFFIC.json').write_text(json.dumps({'requests':application,'allowed_only_simulated_dashboard_reads':allowed,'feature_mutations':sum(x['method']!='GET' for x in application)},indent=2));assert allowed,application
 (R/'ASSISTANCE.json').write_text(json.dumps({'tree':T,'native':'CDP pointer clicks, modifier chords, Escape, Tab and native select keyboard navigation','dom_assistance':['query text/rect assertions','data-native-target annotation and scrollIntoView for native pointer locator','locale select change/input via established DOM helper','inert auth marker in disposable loopback localStorage only'],'fixture':'external static receiver with explicitly simulated dashboard workspace/project context; no product adapter/mock flag changes','source_injection':False,'shortcut_state_injection':False,'focus_emulation':True,'viewport':[[1440,1000],[390,844]],'limitations':['headless Chromium only','no physical mobile/touch keyboard','no OS IME or screen reader','no real backend/auth/access integration','unsupported/conflicting supplied override branches are component-tested, not injected into served build'],'checks':len(b.checks),'timestamp':now()},ensure_ascii=False,indent=2))
 print('SHORTCUT_NATIVE_CHECKS',len(b.checks),flush=True)
except BaseException:
 (R/'FAILURE.txt').write_text(traceback.format_exc())
 try:b.shot('failure')
 except Exception:pass
 raise
finally:
 try:b.raw('Browser.close',{})
 except Exception:pass
 b.ws.close()
