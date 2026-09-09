from chromium_helpers import Browser,ROOT
import json,time,traceback
b=Browser(); results=[]; current=''; path='/w/workspace-1/projects/project-1/edit?nleFixture=1'
q=json.dumps
nav='.ff-timeline-navigation'
clip='[data-navigation-object="clip:clip-1"]'; clip2='[data-navigation-object="clip:clip-2"]'; track='[data-navigation-object="track:video-1"]'
def save():
 (ROOT/'SCENARIO_RESULTS.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
def check(name,expr):b.check(current+' / '+name,expr)
def snap(name):
 b.shot(name);(ROOT/(name+'-DOM.json')).write_text(json.dumps(b.ev('({text:document.body.innerText,focus:document.activeElement.outerHTML,dialogs:[...document.querySelectorAll("[role=dialog]")].map(e=>e.outerHTML)})'),ensure_ascii=False,indent=2))
def click(sel):
 b.ev('document.querySelector('+q(sel)+').scrollIntoView({block:"center"})');b.click(sel)
def btn(text,root=''):
 sel=b.ev('(()=>{let es=[...document.querySelectorAll('+q((root+' button').strip())+')];let e=es.find(e=>e.innerText.trim()==='+q(text)+');if(!e)throw Error("button missing: '+text+'");e.setAttribute("data-native-target","yes");return "[data-native-target=yes]"})()')
 click(sel);b.ev('document.querySelector("[data-native-target=yes]")?.removeAttribute("data-native-target")')
def typein(sel,text):
 click(sel);b.call('input.performActions',{'actions':[{'type':'key','actions':[{'type':'keyDown','value':'\ue009'}]}]});b.key('a');b.call('input.releaseActions',{});b.raw('Input.insertText',{'text':text});time.sleep(.1)
def ready():
 b.viewport(1440,1000);b.nav(path);b.wait('document.querySelectorAll("[data-navigation-object]").length===4');b.locale('en');install()
def install():
 b.ev('''(()=>{const e=document.querySelector('.ff-timeline-navigation');let f=e[Object.keys(e).find(k=>k.startsWith('__reactFiber'))];while(f){let d=f.dependencies?.firstContext;while(d){const v=d.memoizedValue;if(v?.getSnapshot&&v?.dispatch){window.__store=v;return true}d=d.next}f=f.return}throw Error('actual Selection store missing')})()''')
def selected(id):return 'document.querySelector('+q('[data-navigation-object="'+id+'"]')+')?.getAttribute("aria-pressed")==="true"'
def no_dialog():return '!document.querySelector("[role=dialog]")'
def retain():
 b.ev('''window.__retained=[...document.querySelectorAll('.ff-selection-bar button:not(:disabled)')].map(e=>({label:e.innerText,fn:e[Object.keys(e).find(k=>k.startsWith('__reactProps'))].onClick})); window.__retainedNames=__retained.map(x=>x.label)''')
def replay():b.ev('__retained.forEach(x=>x.fn())');time.sleep(.2)
def clear():b.ev('__store.dispatch({category:"LOCAL_EPHEMERAL",type:"select",ids:[]})');time.sleep(.2)
def metadata():click(clip);btn('Inspect selected metadata');b.wait('!!document.querySelector(".ff-navigation-detail")')
def mobile():
 b.viewport(390,844);click(track);click('.ff-mobile-inspector-launcher');b.wait('!!document.querySelector("[role=dialog]")')
def revision():
 click('.ff-nle-history summary');click('.ff-revision-list li:nth-child(2) button');b.wait('document.querySelector(".ff-navigation-identity").innerText.includes("revision-1")');b.wait('document.querySelectorAll("[data-navigation-object]").length===4')
def retire(kind):
 if kind=='revision':revision()
 else:b.ev('__V9.replace()');b.wait('document.querySelectorAll("[data-navigation-object]").length===4')
def run(id,fn):
 global current
 current=id;start=len(b.checks);net=len(b.network);attempt=len(b.blocked);row={'id':id,'status':'RUNNING','start_assertion':start,'network_start':net,'interception_start':attempt};results.append(row);save()
 try:fn();row['status']='PASS'
 except Exception as e:row['status']='FAIL';row['error']=repr(e);row['traceback']=traceback.format_exc();snap(id+'-failure')
 row.update(end_assertion=len(b.checks),network_end=len(b.network),interception_end=len(b.blocked));save()
def ordinary():
 b.viewport(1440,1000);b.raw('Page.navigate',{'url':'http://127.0.0.1:4201/w/workspace-1/projects/project-1/edit'});b.wait('document.body.innerText.includes("Workspace context unavailable")',45);snap('ordinary-final-desktop')
 check('ordinary final actual project boundary unavailable', 'document.body.innerText.includes("Workspace context unavailable") && !document.body.innerText.includes("Loading workspace context")')
 check('ordinary never injects projection','!window.__V9 && !document.querySelector("[data-navigation-object]")')
 check('unknown source not loaded','!document.body.innerText.includes("Loaded timeline projection")')
 b.viewport(390,844);snap('ordinary-final-narrow')
def discovery():
 ready();check('bounded four actual source objects','document.querySelectorAll("[data-navigation-object]").length===4 && document.body.innerText.includes("Partial loaded scope")')
 typein(nav+' > label input','Continuation');check('filter within loaded clips','document.querySelectorAll("[data-navigation-object]").length===2 && !document.querySelector('+q(clip)+')')
 typein('.ff-navigation-locate input','1001/30000');btn('Locate time');check('exact rational position','document.querySelector("output").textContent==="1001/30000"');check('inclusive shared boundary first clip selected',selected('clip:clip-1')+' && document.body.innerText.includes("Loaded clips at this position: 2")')
 click(clip2);check('native click selects second clip before locate',selected('clip:clip-2'));b.ev('window.__submitLog=[];document.querySelector(".ff-navigation-locate").addEventListener("submit",e=>__submitLog.push({submitter:e.submitter?.innerText,type:e.submitter?.type}));true');btn('Locate selected clip');(ROOT/'LOCATE_SELECTED_DIAGNOSTIC.json').write_text(json.dumps(b.ev('({selected:__store.getSnapshot().primarySelectedObject?.id,position:document.querySelector("output").textContent,submits:__submitLog,buttons:[...document.querySelectorAll(".ff-navigation-locate button")].map(e=>({text:e.innerText,type:e.type,attribute:e.getAttribute("type")}))})'),indent=2));check('locate explicitly selected clip retained',selected('clip:clip-2'));snap('english-exact-locate')
def keyboard():
 ready();click(track);b.key('\ue015');check('native down selects and focuses clip',selected('clip:clip-1')+' && document.activeElement.dataset.navigationObject==="clip:clip-1"')
 b.key('i');check('metadata exact supplied range and duration','document.querySelector(".ff-navigation-detail").innerText.includes("1001/30000") && document.querySelector(".ff-navigation-detail").innerText.includes("asset-1")');check('native I metadata focus','!!document.querySelector(".ff-navigation-detail") && !!document.activeElement.closest("[role=dialog]")')
 b.key('\ue004');check('native Tab trapped','!!document.activeElement.closest("[role=dialog]")');b.call('input.performActions',{'actions':[{'type':'key','actions':[{'type':'keyDown','value':'\ue008'}]}]});b.key('\ue004');b.call('input.releaseActions',{});check('native Shift Tab trapped','!!document.activeElement.closest("[role=dialog]")');snap('english-metadata-keyboard')
 b.key('\ue00c');check('Escape returns object focus',no_dialog()+' && document.activeElement.dataset.navigationObject==="clip:clip-1"');b.key('\ue015');check('continue next clip',selected('clip:clip-2'));b.key('\ue00c');check('Escape clears local selection','!document.querySelector("[data-navigation-object][aria-pressed=true]")')
def chinese():
 ready();b.locale('zh-CN');check('Chinese exact discovery locate inspect labels','["筛选已加载轨道和片段","精确时间（整数或分数）","定位时间","定位选中片段","检查选中对象元数据"].every(x=>document.querySelector(".ff-timeline-navigation").innerText.includes(x))');check('Chinese labels actual locale','document.documentElement.lang==="zh-CN" && !document.querySelector(".ff-navigation-locate").innerText.includes("Locate time")');click(clip);b.key('i');check('Chinese dialog','!!document.querySelector("[role=dialog]") && !document.querySelector("[role=dialog]").innerText.includes("Close details")');snap('chinese-desktop-metadata');b.key('\ue00c');b.viewport(390,844);snap('chinese-narrow');check('Chinese narrow no document overflow','document.documentElement.scrollWidth<=innerWidth+1')
def geometry():
 ready()
 for width in [1440,390]:
  b.viewport(width,1000 if width==1440 else 844);click(clip);check(str(width)+' full long name accessible title','document.querySelector('+q(clip)+').title===__V9.longName');check(str(width)+' no horizontal document overflow','document.documentElement.scrollWidth<=innerWidth+1');check(str(width)+' bounded list geometry','(()=>{let r=document.querySelector(".ff-navigation-list").getBoundingClientRect();return r.width>0&&r.left>=0&&r.right<=innerWidth+1})()');snap('english-longnames-'+str(width))
def states():
 ready();b.ev('__V9.mode("loading")');btn('Refresh loaded projection');check('loading no previous data','!document.querySelector("[data-navigation-object]") && document.querySelector(".ff-timeline-navigation [role=status]").innerText.includes("Loading")');snap('loading');b.ev('__V9.settle()');b.wait('!!document.querySelector("[data-navigation-object]")')
 b.ev('__V9.mode("empty")');btn('Refresh loaded projection');check('bounded empty not full empty','!document.querySelector("[data-navigation-object]") && document.querySelector(".ff-navigation-list").innerText.includes("loaded")');snap('empty')
 b.ev('__V9.mode("error")');btn('Refresh loaded projection');check('error and retry','!document.querySelector("[data-navigation-object]") && document.querySelector(".ff-timeline-navigation").innerText.includes("Retry")');snap('error');b.ev('__V9.mode("ready")');btn('Retry timeline projection');b.wait('document.querySelectorAll("[data-navigation-object]").length===4');check('retry real adapter ready','__V9.reads.some(x=>x.mode==="error") && __V9.reads.at(-1).mode==="ready"')
 b.ev('__V9.mode("unknown")');btn('Refresh loaded projection');check('unknown timing never guessed','document.querySelector(".ff-navigation-locate input").disabled && document.querySelector("output").textContent==="Not located"')
def revisions():
 ready();metadata();b.ev('window.__oldClip=document.querySelector('+q(clip)+');true');b.key('\ue00c');revision();check('real history gateway retires details',no_dialog()+' && !__oldClip.isConnected && !document.querySelector("[aria-pressed=true][data-navigation-object]")');check('new receipt targets explicit revision','__V9.reads.at(-1).request.target.revisionId==="revision-1"');snap('revision-retirement');ready();b.ev('__V9.mode("loading")');btn('Refresh loaded projection');b.ev('__V9.mode("empty")');revision_empty();b.ev('__V9.settle()');check('late prior revision response rejected','__V9.reads.some(x=>x.aborted&&x.settledLate)&&!document.querySelector("[data-navigation-object]")&&__V9.reads.at(-1).request.target.revisionId==="revision-1"')
def revision_empty():
 click('.ff-nle-history summary');click('.ff-revision-list li:nth-child(2) button');b.wait('document.querySelector(".ff-navigation-identity").innerText.includes("revision-1")');b.wait('!!document.querySelector(".ff-navigation-list")')
def late_source():
 ready();b.ev('__V9.mode("loading")');btn('Refresh loaded projection');b.ev('__V9.mode("empty");__V9.replace()');b.wait('!!document.querySelector(".ff-navigation-list")');b.ev('__V9.settle()');check('aborted source late completion not revived','__V9.reads.some(x=>x.aborted&&x.settledLate) && !document.querySelector("[data-navigation-object]")');snap('late-source')
def access():
 ready();metadata();b.ev('__V9.access("POLICY_DENIED")');check('denied retires data and modal',no_dialog()+' && !document.querySelector("[data-navigation-object]")');b.ev('__V9.access("AVAILABLE")');b.wait('!!document.querySelector("[data-navigation-object]")');check('access regain no selection or modal',no_dialog()+' && !document.querySelector("[data-navigation-object][aria-pressed=true]")')
 ready();b.ev('__V9.mode("loading")');btn('Refresh loaded projection');b.ev('__V9.access("POLICY_DENIED");__V9.settle()');check('late response after denied access rejected','__V9.reads.some(x=>x.aborted&&x.settledLate)&&!document.querySelector("[data-navigation-object]")')
def identity():
 ready();metadata();b.ev('__V9.mode("loading")');b.key('\ue00c');btn('Refresh loaded projection');b.ev('__V9.mode("empty");__V9.identity()');time.sleep(.5);b.ev('__V9.settle()');check('SDK true identity retires pending receipt','__V9.sdkLog.some(x=>x.event==="UserLoaded"&&x.callbacks>0) && __V9.reads.some(x=>x.aborted&&x.settledLate) && !document.querySelector("[data-navigation-object]") && !document.querySelector("[role=dialog]")')
def toolbar():
 for boundary in ['selection','revision','source']:
  ready();click(clip);retain();btn('Hide inspector','.ff-selection-bar')
  b.ev("(()=>{const e=[...document.querySelectorAll('.ff-selection-bar button')].find(e=>e.innerText==='Show inspector');__retained.push({label:e.innerText,fn:e[Object.keys(e).find(k=>k.startsWith('__reactProps'))].onClick});window.__originalStore=__store;window.__originalLifetime=__store.getSnapshot().lifetime;return true})()")
  check(boundary+' all six real toolbar callbacks captured','__retained.length===6 && new Set(__retained.map(x=>x.label)).size===6 && __retained.every(x=>typeof x.fn==="function")')
  if boundary=='selection':click(clip2)
  elif boundary=='revision':revision();click(clip)
  else:b.ev('__V9.replace()');b.wait('!!document.querySelector("[data-navigation-object]")');click(clip)
  install();check(boundary+' same actual Selection store','__store===__originalStore')
  if boundary!='selection':check(boundary+' retired actual Selection lifetime','__store.getSnapshot().lifetime!==__originalLifetime')
  names=b.ev('__retained.map(x=>x.label)')
  for i,name in enumerate(names):
   b.ev('__store.dispatch({category:"LOCAL_EPHEMERAL",type:"agent",open:false});__store.dispatch({category:"LOCAL_EPHEMERAL",type:"inspect",open:'+('false' if name in ['Show inspector','Edit local properties'] else 'true')+'});true')
   b.ev('window.__before=__store.getSnapshot();window.__focus=document.activeElement;window.__dispatchOriginal=__store.dispatch;window.__dispatchCalls=[];__store.dispatch=(...a)=>{__dispatchCalls.push(a);return __dispatchOriginal(...a)};true')
   b.ev('__retained['+str(i)+'].fn();true');time.sleep(.1)
   check(boundary+' retained '+name+' no dispatch/state/focus effect','__dispatchCalls.length===0 && __store.getSnapshot()===__before && document.activeElement===__focus && !document.querySelector("[role=dialog]")')
   b.ev('__store.dispatch=__dispatchOriginal;true')
def metadata_clear():
 ready();metadata();clear();check('clear closes metadata fallback',no_dialog()+' && document.activeElement.matches(".ff-timeline-navigation")');click(clip2);check('new clip no metadata revival',no_dialog());metadata();b.ev('__store.dispatch({category:"LOCAL_EPHEMERAL",type:"select",ids:[]});__store.dispatch({category:"LOCAL_EPHEMERAL",type:"select",ids:["clip:clip-1"]})');check('batched same clip no revival',no_dialog());snap('metadata-nonrevival');metadata();b.ev('__store.dispatch({category:"LOCAL_EPHEMERAL",type:"inspect",open:false});__store.dispatch({category:"LOCAL_EPHEMERAL",type:"inspect",open:true})');check('batched hide show metadata no revival',no_dialog());metadata();b.ev('__store.dispatch({category:"LOCAL_EPHEMERAL",type:"select",ids:["clip:clip-2"]})');check('primary change closes metadata',no_dialog());click(clip);check('original selection cannot revive metadata',no_dialog())
def mobile_clear():
 ready();mobile();snap('mobile-track-dialog');btn('Clear track selection','[role=dialog]');check('clear track closes mobile fallback',no_dialog()+' && document.activeElement.id==="main-content"');click(clip);check('new clip no mobile revival',no_dialog());click('.ff-mobile-inspector-launcher');check('explicit new mobile launch','!!document.querySelector("[role=dialog]")');b.key('\ue00c');check('mobile Escape returns launcher',no_dialog()+' && document.activeElement.matches(".ff-mobile-inspector-launcher")')
def both_retire():
 for modal in ['metadata','mobile']:
  for kind in ['revision','source']:
   ready();metadata() if modal=='metadata' else mobile();b.ev('window.__oldDialog=document.querySelector("[role=dialog]");true')
   # Explicit background boundary event: a native history click cannot target a modal-covered control.
   if kind=='revision':
    b.ev('(()=>{const e=document.querySelector(".ff-revision-list li:nth-child(2) button");e[Object.keys(e).find(k=>k.startsWith("__reactProps"))].onClick()})()');b.wait('document.querySelector(".ff-navigation-identity").innerText.includes("revision-1")')
   else:b.ev('__V9.replace()')
   b.wait('document.querySelectorAll("[data-navigation-object]").length===4');check(modal+' '+kind+' retires dialog',no_dialog()+' && !__oldDialog.isConnected');click(clip);check(modal+' '+kind+' no revival',no_dialog())
def network():
 # Ordinary bootstrap attempts remain in their own ledger and are not silently subtracted from global totals.
 rows=[r for r in results if r['id'] not in ['V9-01','V9-11']];observed=[];intercepted=[]
 for r in rows:observed+=b.network[r['network_start']:r['network_end']];intercepted+=b.blocked[r['interception_start']:r['interception_end']]
 bad=lambda r:r['method'] not in ['GET','HEAD'] or r.get('type') in ['Media','WebSocket'] or any(x in r['url'].lower() for x in ['operation','playback','streaming','download'])
 data={'navigation_network':observed,'navigation_interceptions':intercepted,'forbidden_navigation_network':[r for r in observed if bad(r)],'forbidden_navigation_interceptions':[r for r in intercepted if bad(r)]};(ROOT/'NAVIGATION_NETWORK_ASSERTION.json').write_text(json.dumps(data,indent=2));b.ev('window.__networkPass='+json.dumps(not data['forbidden_navigation_network'] and not data['forbidden_navigation_interceptions']));check('no new canonical operation or media attempts including blocked','__networkPass===true')
for id,fn in [('V9-01',ordinary),('V9-02',discovery),('V9-03',keyboard),('V9-04',chinese),('V9-05',geometry),('V9-06',states),('V9-07',revisions),('V9-08',late_source),('V9-09',access),('V9-10',identity),('IR01-1',toolbar),('IR01-2A',metadata_clear),('IR01-2B',mobile_clear),('IR01-2C',both_retire),('V9-11',network)]:run(id,fn)
b.raw('Browser.close',{})
print(json.dumps(results,indent=2));raise SystemExit(0 if all(r['status']=='PASS' for r in results) else 1)
