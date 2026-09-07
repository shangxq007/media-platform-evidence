"""Same exact-product-bundle focus probes for baseline and correction.
Trusted CDP Tab/Enter/Escape/pointer; natural disabled blur only.
External test adapter wraps the explicitly simulated InboxSession source via
React fiber inspection. No bundle/source patch, DOM blur, or BODY focus injection.
Resolution is explicit; no sleep establishes pending/order boundaries.
"""
import json, traceback, sys, urllib.parse
from pathlib import Path
from chromium_helpers import Browser
from control import T
R=Path(__file__).parent
b=Browser(); observations=[]; failures=[]; harness_error=None
q=json.dumps
entry='.ff-notification-entry';dialog='.ff-notification-inbox'
read='.ff-notification-list [data-notification-id="simulated-1"] button:last-child'
allread='.ff-notification-controls > button:last-child'
activefilter='.ff-notification-controls [aria-pressed=true]'
refresh='.ff-notification-controls > button:first-of-type'
base='/w/simulated-workspace/projects/simulated-project/overview?notificationFixture=1'
inject=r'''(()=>{
 let node=document.querySelector('.ff-notification-entry');
 let fiber=node[Object.keys(node).find(k=>k.startsWith('__reactFiber$'))];
 while(fiber && !fiber.memoizedProps?.source?.adapter) fiber=fiber.return;
 if(!fiber) throw Error('Missing explicit InboxSession source');
 const source=fiber.memoizedProps.source,adapter=source.adapter;
 if(adapter.origin!=='simulated')throw Error('Refuse non-simulated adapter');
 const originals={list:adapter.list,markRead:adapter.markRead,markAllRead:adapter.markAllRead};
 const h=window.__focusHarness={source,adapter,originals,pending:[],calls:[],holdList:false};
 for(const method of ['markRead','markAllRead'])adapter[method]=function(request,signal){
  h.calls.push({method,request});
  return new Promise((resolve,reject)=>h.pending.push({method,request,signal,resolve,reject}));
 };
 adapter.list=function(request,signal){
  h.calls.push({method:'list',request});
  if(h.holdList)return new Promise((resolve,reject)=>h.pending.push({method:'list',request,signal,resolve,reject}));
  return originals.list.call(adapter,request,signal);
 };
 h.finish=async function(index,outcome){const p=h.pending[index];if(!p)throw Error('No pending operation');
  if(p.finished)throw Error('Already resolved');p.finished=true;
  if(outcome==='reject'){p.reject(Error('controlled rejection'));return;}
  if(outcome==='invalid'){p.resolve({error:'NOT_FOUND'});return;}
  if(outcome==='fail'){p.resolve({status:'error',context:p.request.context,requestId:p.request.requestId});return;}
  p.resolve(await originals[p.method].call(adapter,p.request,p.signal));
 };
 return {origin:adapter.origin,context:source.context};
})()'''
def save():
 (R/'FOCUS_OBSERVATIONS.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2))
def observe(name):
 state=b.ev('''(()=>{const e=document.activeElement;return {tag:e?.tagName,text:e?.textContent?.slice(0,120),className:e?.className,disabled:e?.disabled??false,inDialog:!!e?.closest('.ff-notification-inbox'),isLauncher:e===document.querySelector('.ff-notification-entry'),dialogOpen:!!document.querySelector('.ff-notification-inbox'),status:document.querySelector('.ff-notification-inbox [role=status]')?.textContent,rows:document.querySelectorAll('.ff-notification-list li').length}})()''')
 observations.append({'name':name,'tree':T,'state':state});save();return state

def check(name,expression):
 # Collect all explicitly authorized diagnostic scenarios despite expected RED.
 value=b.ev(expression);passed=value is True
 b.checks.append({'IMPLEMENTATION_TREE':T,'name':name,'expression':expression,'passed':passed,'value':value})
 (R/'NATIVE_CHECKS.json').write_text(json.dumps(b.checks,ensure_ascii=False,indent=2))
 if not passed:failures.append(name)

def click(selector):
 b.ev('document.querySelector('+q(selector)+').scrollIntoView({block:"nearest"})');b.click(selector)

def prepare(tag,locale='en',width=1440,unread=False,hold=True):
 b.viewport(width,844 if width<500 else 1000);b.nav(base);b.locale(locale)
 click(entry);b.wait('document.querySelectorAll(".ff-notification-list li").length===3')
 if unread:
  click('.ff-notification-controls [role=group] button:nth-child(2)');b.wait('document.querySelectorAll(".ff-notification-list li").length===2')
 if hold:
  binding=b.ev(inject);observations.append({'name':tag+'-adapter-injection','tree':T,'binding':binding});save()
 # Passive capture of actual delivered focus/keys; no preventDefault/mutations.
 b.ev("window.__focusEvents=[];for(const type of ['focusin','focusout','keydown'])document.addEventListener(type,e=>window.__focusEvents.push({type,key:e.key,trusted:e.isTrusted,tag:e.target.tagName,text:e.target.textContent?.slice(0,100),active:document.activeElement?.tagName}),true)")

def activate(tag,selector=read):
 # Native Tab traversal establishes focus without DOM focus().
 for _ in range(30):
  if b.ev('document.activeElement===document.querySelector('+q(selector)+')'):break
  b.key('\ue004')
 else:raise AssertionError('Cannot reach initiating read control with Tab')
 observe(tag+'-before-activation');b.key('\ue007');observe(tag+'-after-activation')

def escape(tag):
 observe(tag+'-before-escape');b.key('\ue00c');observe(tag+'-after-escape')
 check(tag+'-escape-closes','!document.querySelector(".ff-notification-inbox")')
 check(tag+'-launcher-restored','document.activeElement===document.querySelector(".ff-notification-entry")')
 events=b.ev('window.__focusEvents');(R/(tag+'-events.json')).write_text(json.dumps(events,ensure_ascii=False,indent=2))

def stable(tag):
 check(tag+'-stable-enabled-focus',"!!document.activeElement?.closest('.ff-notification-inbox') && document.activeElement?.tagName==='BUTTON' && !document.activeElement.disabled")

def finish(index=0,outcome='success'):b.ev('window.__focusHarness.finish('+str(index)+','+q(outcome)+')')
def loaded():b.wait('!!document.querySelector(".ff-notification-list") && !document.querySelector(".ff-notification-list").getAttribute("aria-busy").includes("true")')
try:
 # Existing immediate fixture, no injected adapter, naturally delivered activation.
 prepare('immediate-all',hold=False);activate('immediate-all')
 b.wait('document.querySelector('+q(read)+').disabled && document.querySelector(".ff-notification-count").textContent==="1"')
 stable('immediate-all');check('immediate-all-row-retained','document.querySelectorAll(".ff-notification-list li").length===3');b.shot('immediate-all');escape('immediate-all')
 # Explicitly held adapter resolves deterministic pending boundaries.
 prepare('pending');activate('pending');b.wait('window.__focusHarness.pending.length===1')
 check('pending-read-disabled','document.querySelector('+q(read)+').disabled');stable('pending')
 b.shot('pending');escape('pending');finish()
 check('pending-late-does-not-reopen','!document.querySelector(".ff-notification-inbox")')
 for outcome in ['success','fail','invalid','reject','reconcile-fail']:
  tag='all-'+outcome;locale='zh-CN' if outcome in ['fail','reconcile-fail'] else 'en';width=390 if locale=='zh-CN' else 1440
  prepare(tag,locale,width);activate(tag);stable(tag+'-pending')
  if outcome=='reconcile-fail':b.ev('window.__focusHarness.holdList=true')
  finish(outcome='success' if outcome=='reconcile-fail' else outcome)
  if outcome=='reconcile-fail':
   b.wait('window.__focusHarness.pending.length===2');observe(tag+'-reconciliation-loading');stable(tag+'-loading');finish(1,'fail');b.wait('!document.querySelector(".ff-notification-list")')
  elif outcome=='success':
   b.wait('document.querySelector(".ff-notification-count")?.textContent==="1"');check(tag+'-row-remains','document.querySelectorAll(".ff-notification-list li").length===3')
  else:
   b.wait('!document.querySelector('+q(read)+').disabled');check(tag+'-unread-retained','document.querySelector(".ff-notification-count")?.textContent==="2"')
  observe(tag+'-outcome');stable(tag+'-outcome');b.shot(tag);escape(tag)
 prepare('unread',locale='zh-CN',width=390,unread=True);activate('unread');stable('unread-pending');finish()
 b.wait('!document.querySelector('+q(read)+')');stable('unread-complete');escape('unread')
 prepare('read-all',locale='zh-CN',width=390);activate('read-all',allread);stable('read-all-pending');finish()
 b.wait('document.querySelector(".ff-notification-count")?.textContent==="0"');stable('read-all-complete');escape('read-all')
 prepare('no-theft');activate('no-theft');click(refresh);b.wait('document.activeElement===document.querySelector('+q(refresh)+')');finish();loaded()
 check('user-moved-no-focus-theft','document.activeElement===document.querySelector('+q(refresh)+')');escape('no-theft')
 prepare('programmatic');click(refresh);loaded();b.ev('document.querySelector('+q(read)+').click()')
 check('programmatic-no-focus-theft-pending','document.activeElement===document.querySelector('+q(refresh)+')');finish();loaded()
 check('programmatic-no-focus-theft-complete','document.activeElement===document.querySelector('+q(refresh)+')');escape('programmatic')
 prepare('reopen');activate('reopen');escape('reopen')
 # On baseline Escape can fail; close via its native close control only to set
 # the close/reopen regression precondition, never relabel the Escape failure.
 if b.ev('!!document.querySelector(".ff-notification-inbox")'):click('.ff-notification-inbox header button')
 click(entry);loaded();activate('reopen-new');b.wait('window.__focusHarness.pending.length===2');finish(0)
 check('old-finally-keeps-new-lock','document.querySelector('+q(read)+').disabled && window.__focusHarness.pending.length===2')
 stable('old-completion-no-theft');finish(1);loaded();escape('reopen-new')
 # A native Tab from stable pending focus must remain inside the dialog.
 prepare('pending-tab');activate('pending-tab');b.key('\ue004');observe('pending-tab-after-tab')
 check('pending-tab-contained',"!!document.activeElement?.closest('.ff-notification-inbox') && !document.activeElement.disabled")
 escape('pending-tab')
except BaseException:
 harness_error=traceback.format_exc();(R/'HARNESS_FAILURE.txt').write_text(harness_error);traceback.print_exc()
finally:
 try:
  b.shot('final-state')
  network=[x for x in b.network if x['url'].startswith(('http:','https:'))]
  external=[x for x in network if urllib.parse.urlsplit(x['url']).hostname!='127.0.0.1']
  requests=[json.loads(l) for l in (R/'HTTP_REQUESTS.jsonl').read_text().splitlines()]
  mutations=[json.loads(l) for l in (R/'MUTATION_ATTEMPTS.jsonl').read_text().splitlines()] if (R/'MUTATION_ATTEMPTS.jsonl').exists() else []
  (R/'HTTP_ASSERTIONS.json').write_text(json.dumps({'browser_http_requests':len(network),'local_receiver_requests':len(requests),'external_attempts':external,'notification_http_requests':len([x for x in network if '/notifications' in x['url']]),'real_backend_requests':len(external),'local_auth_posts':len(mutations),'mutations':mutations},indent=2))
 except BaseException:
  harness_error=(harness_error or '')+traceback.format_exc()
 rc=2 if harness_error else (1 if failures else 0)
 (R/'SMOKE_EXIT.json').write_text(json.dumps({'native_exit':rc,'harness_error':harness_error,'tree':T,'checks':len(b.checks),'passed':sum(x['passed'] for x in b.checks),'failed':failures,'natural_focus':True,'forced_body_focus':False,'assistance':['CDP focus emulation','DOM locale and scrollIntoView','explicit simulated adapter closure wrapper via React fiber; no product byte changes','programmatic activation scenario explicitly DOM click'],'physical_device':False,'screen_reader_speech':False,'OS_push':False},indent=2))
 b.ws.close()
sys.exit(rc)
