import json,time,base64,urllib.request
from websockets.sync.client import connect
from browser_helpers import Browser as Base
from control import T,now
from pathlib import Path
ROOT=Path(__file__).parent
class Browser(Base):
 def __init__(self):
  targets=json.loads(urllib.request.urlopen('http://127.0.0.1:9267/json/list').read())
  self.ws=connect(next(t['webSocketDebuggerUrl'] for t in targets if t['type']=='page'));self.seq=0;self.commands=[];self.checks=[];self.context='CDP-page';self.mods=0;self.x=0;self.y=0
  self.raw('Page.enable',{});self.raw('Emulation.setFocusEmulationEnabled',{'enabled':True})
 def raw(self,method,params):
  self.seq+=1;self.ws.send(json.dumps({'id':self.seq,'method':method,'params':params}))
  while True:
   r=json.loads(self.ws.recv(timeout=30))
   if r.get('id')==self.seq:break
  self.commands.append({'tree':T,'timestamp':now(),'method':method,'params':params,'result':r if method!='Page.captureScreenshot' else {'captured':'error' not in r}})
  (ROOT/'NATIVE_COMMANDS.json').write_text(json.dumps(self.commands,ensure_ascii=False,indent=2))
  if 'error' in r:raise RuntimeError(r)
  return r.get('result',{})
 def call(self,method,params):
  if method=='session.end':return {}
  if method=='input.releaseActions':
   for bit,key,code,vk in [(2,'Control','ControlLeft',17),(4,'Meta','MetaLeft',91),(8,'Shift','ShiftLeft',16),(1,'Alt','AltLeft',18)]:
    if self.mods & bit:self.mods &= ~bit;self.raw('Input.dispatchKeyEvent',{'type':'keyUp','key':key,'code':code,'windowsVirtualKeyCode':vk,'modifiers':self.mods})
   return {}
  assert method=='input.performActions',method
  keys={'\ue004':('Tab','Tab',9,0),'\ue007':('Enter','Enter',13,0),'\ue00c':('Escape','Escape',27,0),'\ue009':('Control','ControlLeft',17,2),'\ue03d':('Meta','MetaLeft',91,4),'\ue008':('Shift','ShiftLeft',16,8),'\ue012':('ArrowLeft','ArrowLeft',37,0),'\ue014':('ArrowRight','ArrowRight',39,0),'\ue013':('ArrowUp','ArrowUp',38,0),'\ue015':('ArrowDown','ArrowDown',40,0),' ':(' ','Space',32,0)}
  for source in params['actions']:
   for a in source['actions']:
    if a['type'] in ['keyDown','keyUp']:
     value=a['value'];key,code,vk,bit=keys.get(value,(value,'Key'+value.upper(),ord(value.upper()),0))
     down=a['type']=='keyDown'
     if bit:self.mods=(self.mods|bit) if down else (self.mods&~bit)
     p={'type':a['type'],'key':key,'code':code,'windowsVirtualKeyCode':vk,'modifiers':self.mods}
     if down and not bit and (key in ['Enter',' '] or (len(key)==1 and not self.mods)):p['text']='\r' if key=='Enter' else key;p['unmodifiedText']=p['text']
     self.raw('Input.dispatchKeyEvent',p)
    elif a['type']=='pointerMove':self.x=a['x'];self.y=a['y'];self.raw('Input.dispatchMouseEvent',{'type':'mouseMoved','x':self.x,'y':self.y,'modifiers':self.mods})
    elif a['type'] in ['pointerDown','pointerUp']:self.raw('Input.dispatchMouseEvent',{'type':'mousePressed' if a['type']=='pointerDown' else 'mouseReleased','x':self.x,'y':self.y,'button':'left','clickCount':1,'modifiers':self.mods})
    else:raise RuntimeError(a)
  return {}
 def ev(self,expression):
  r=self.raw('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True})
  if r.get('exceptionDetails'):raise RuntimeError(r)
  return r.get('result',{}).get('value')
 def nav(self,path,port=4196):
  self.raw('Page.navigate',{'url':f'http://127.0.0.1:{port}'+path});time.sleep(.3);self.wait('!!document.querySelector(".ff-app-shell")')
 def viewport(self,width,height):self.raw('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False})
 def shot(self,name):
  r=self.raw('Page.captureScreenshot',{'format':'png'});(ROOT/(name+'.png')).write_bytes(base64.b64decode(r['data']))
