"""Native Firefox WebDriver BiDi evidence helpers; synthetic UI fixtures only."""
import json,time,base64
from control import T,now
from pathlib import Path
from websockets.sync.client import connect
ROOT=Path(__file__).parent
class Browser:
 def __init__(self,port=9255):
  self.ws=connect(f'ws://127.0.0.1:{port}/session');self.seq=0;self.commands=[];self.checks=[]
  self.call('session.new',{'capabilities':{'alwaysMatch':{}}})
  self.context=self.call('browsingContext.getTree',{})['contexts'][0]['context']
 def call(self,method,params):
  self.seq+=1;self.ws.send(json.dumps({'id':self.seq,'method':method,'params':params}))
  while True:
   r=json.loads(self.ws.recv(timeout=30))
   if r.get('id')==self.seq:break
  self.commands.append({'IMPLEMENTATION_TREE':T,'VALIDATION_TIMESTAMP':now(),'method':method,'params':params,'result':{k:v for k,v in r.items() if k!='id'} if method!='browsingContext.captureScreenshot' else {'captured':'error' not in r}})
  (ROOT/'NATIVE_COMMANDS.json').write_text(json.dumps(self.commands,ensure_ascii=False,indent=2))
  if 'error' in r:raise RuntimeError(r)
  return r['result']
 def ev(self,expression):
  r=self.call('script.evaluate',{'expression':expression,'target':{'context':self.context},'awaitPromise':True})
  if r.get('type')=='exception':raise RuntimeError(r)
  return r.get('result',{}).get('value')
 def check(self,name,expression):
  v=self.ev(expression);p=v is True
  # Parent task's global preservation census is outside this bounded smoke.
  self.checks.append({'IMPLEMENTATION_TREE':T,'VALIDATION_TIMESTAMP':now(),'name':name,'expression':expression,'passed':p,'value':v})
  (ROOT/'NATIVE_CHECKS.json').write_text(json.dumps(self.checks,ensure_ascii=False,indent=2))
  assert p,(name,v)
 def wait(self,expression,seconds=12):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if self.ev(expression):return
   time.sleep(.15)
  raise AssertionError('precondition timeout: '+expression)
 def viewport(self,width,height):
  self.call('browsingContext.setViewport',{'context':self.context,'viewport':{'width':width,'height':height},'devicePixelRatio':1})
 def nav(self,path,port=4198):
  self.call('browsingContext.navigate',{'context':self.context,'url':f'http://127.0.0.1:{port}'+path,'wait':'complete'})
  self.wait('!!document.querySelector(".ff-app-shell")')
 def click(self,selector):
  coords=json.loads(self.ev('JSON.stringify((()=>{const e=document.querySelector('+json.dumps(selector)+');if(!e)throw Error("missing element");const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})())'))
  self.call('input.performActions',{'context':self.context,'actions':[{'type':'pointer','id':'mouse','parameters':{'pointerType':'mouse'},'actions':[{'type':'pointerMove','x':round(coords['x']),'y':round(coords['y'])},{'type':'pointerDown','button':0},{'type':'pointerUp','button':0}]}]})
  time.sleep(.15)
 def key(self,value):
  self.call('input.performActions',{'context':self.context,'actions':[{'type':'key','id':'keyboard','actions':[{'type':'keyDown','value':value},{'type':'keyUp','value':value}]}]})
  time.sleep(.15)
 def locale(self,locale):
  self.ev('(()=>{const e=document.querySelector(".ff-locale-selector select");e.value='+json.dumps(locale)+';e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));})()')
  self.wait('document.documentElement.lang === '+json.dumps(locale))
 def shot(self,name):
  r=self.call('browsingContext.captureScreenshot',{'context':self.context})
  (ROOT/(name+'.png')).write_bytes(base64.b64decode(r['data']))
