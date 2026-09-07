import json,time
from chromium_helpers import Browser
from control import T,now
from pathlib import Path
R=Path(__file__).parent
class CanvasBrowser(Browser):
 def __init__(self):
  super().__init__();self.buttons=0;self.mark=0;self.browser_version=self.raw('Browser.getVersion',{})
 def mouse(self,kind,x,y,mods=0):
  if kind=='mousePressed':self.buttons=1
  if kind=='mouseReleased':self.buttons=0
  self.raw('Input.dispatchMouseEvent',{'type':kind,'x':float(x),'y':float(y),'button':'left' if kind!='mouseMoved' or self.buttons else 'none','buttons':self.buttons,'clickCount':1 if kind!='mouseMoved' else 0,'modifiers':mods,'pointerType':'mouse'})
  time.sleep(.08)
 def positions(self):return self.ev('Array.from(document.querySelectorAll("[data-canvas-node]"),e=>({id:e.dataset.canvasNode,x:parseFloat(e.style.left),y:parseFloat(e.style.top),selected:e.getAttribute("aria-pressed")==="true"}))')
 def rect(self,selector):return self.ev('(()=>{const r=document.querySelector('+json.dumps(selector)+').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()')
 def camera(self):return self.ev('(()=>{const m=new DOMMatrix(getComputedStyle(document.querySelector(".ff-canvas-viewport")).transform);return {zoom:m.a,x:m.e,y:m.f}})()')
 def point(self,selector):
  r=self.rect(selector);return (r['x']+r['w']/2,r['y']+r['h']/2)
 def down(self,selector):
  x,y=self.point(selector);self.mouse('mouseMoved',x,y);self.mouse('mousePressed',x,y);return x,y
 def up(self,x,y):self.mouse('mouseReleased',x,y);time.sleep(.25)
 def move(self,x,y,mods=0):self.mouse('mouseMoved',x,y,mods)
 def button(self,text):
  self.ev('(()=>{document.querySelectorAll("[data-native-target]").forEach(e=>e.removeAttribute("data-native-target"));const e=Array.from(document.querySelectorAll("button")).find(e=>e.innerText.trim()==='+json.dumps(text)+');if(!e)throw Error("missing button");e.setAttribute("data-native-target","");e.scrollIntoView({block:"nearest"});})()');self.click('[data-native-target]');time.sleep(.3)
 def record(self,name,expected,actual,passed,assistance='DOM geometry reads and focus emulation; CDP trusted mouse/key input',simulation=False):
  commands=self.commands[self.mark:];self.mark=len(self.commands)
  row={'test_identity':name,'source_tree':T,'production_build_sha256':json.loads((R/'BUILD_ARTIFACT_BOUNDARY.json').read_text())['build_manifest_sha256'],'browser':'Chromium CDP headless','browser_version':self.browser_version,'CDP_used':True,'held_button_encoding':'button=left and buttons=1 for held mouseMoved','input_method':sorted(set(c['method'] for c in commands)),'expected':expected,'actual':actual,'result':'PASS' if passed else 'FAIL','passed':bool(passed),'synthetic_assistance':assistance,'DOM_helper':True,'focus_emulation':True,'pointer_injection':any(c['method']=='Input.dispatchMouseEvent' for c in commands),'capture_simulation':simulation,'reason':'Synthetic API fixture; frontend presentation-only browser acceptance, no backend or physical-device evidence','timestamp':now()}
  self.checks.append(row);(R/'NATIVE_INTERACTION_RESULTS.json').write_text(json.dumps({'tree':T,'checks':self.checks,'passed':sum(c['passed'] for c in self.checks),'total':len(self.checks),'physical_touch_tested':False,'OS_IME_tested':False,'screen_reader_tested':False},ensure_ascii=False,indent=2))
  assert passed,(name,expected,actual)
 def reset(self):
  self.nav('/w/ux-workspace/projects/ux-project/canvas',4198);self.wait('document.querySelectorAll("[data-canvas-node]").length===2');self.locale('en');time.sleep(.5)
  self.ev('window.__captureEvents=[];document.querySelector(".ff-workspace-canvas").addEventListener("gotpointercapture",e=>window.__captureEvents.push({type:e.type,id:e.pointerId}));document.querySelector(".ff-workspace-canvas").addEventListener("lostpointercapture",e=>window.__captureEvents.push({type:e.type,id:e.pointerId}));')
