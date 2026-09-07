"""Focused inbox smoke; trusted Chromium CDP inputs plus disclosed DOM locale/scroll helpers."""
import json,time,traceback,sys,urllib.parse
from pathlib import Path
from chromium_helpers import Browser
from control import T
R=Path(__file__).parent;b=Browser();rc=0
q=json.dumps
entry='.ff-notification-entry';dialog='.ff-notification-inbox';row='[data-notification-id="simulated-1"]';row2='[data-notification-id="simulated-2"]'
base='/w/simulated-workspace/projects/simulated-project/overview'
def click(s):
 b.ev('document.querySelector('+q(s)+').scrollIntoView({block:"nearest"})');b.click(s)
def check(n,e):b.check(n,e)
def open_inbox():
 click(entry);b.wait('!!document.querySelector(".ff-notification-inbox")')
def loaded():b.wait('!!document.querySelector(".ff-notification-list li")')
def read_detail():click('.ff-notification-list '+row+' .ff-notification-title')
def filter_unread():click('.ff-notification-controls [role=group] button:nth-child(2)')
def mark():click('.ff-notification-list '+row+' button:last-child')
def readall():click('.ff-notification-controls > button:last-child')
def count(n):return 'document.querySelector(".ff-notification-count")?.textContent==='+q(str(n))
try:
 for locale,width,height in [('en',1440,1000),('en',390,844),('zh-CN',1440,1000),('zh-CN',390,844)]:
  tag=('desktop' if width>400 else 'narrow')+'-'+locale
  b.viewport(width,height);b.nav(base+'?notificationFixture=1');b.locale(locale)
  check(tag+'-single-entry-unknown-before-query','document.querySelectorAll(".ff-notification-entry").length===1 && !document.querySelector(".ff-notification-count")')
  click(entry);b.wait('!!document.querySelector(".ff-notification-inbox")');loaded()
  check(tag+'-known-global-count',count(2))
  check(tag+'-simulation-visible','document.querySelector(".ff-notification-origin").textContent.includes('+q('SIMULATED' if locale=='en' else '模拟')+')')
  check(tag+'-focus-contained','document.querySelector(".ff-notification-inbox").contains(document.activeElement)')
  read_detail();check(tag+'-opaque-full-detail','document.querySelector(".ff-notification-body").textContent.includes("No media was rendered.") && !document.querySelector(".ff-notification-inbox img")')
  check(tag+'-detail-does-not-mark',count(2))
  check(tag+'-layout','(()=>{const d=document.querySelector(".ff-notification-inbox"),r=d.getBoundingClientRect();return r.left>=-1 && r.right<=innerWidth+1 && r.top>=-1 && r.bottom<=innerHeight+1 && d.scrollWidth<=d.clientWidth+1 && document.documentElement.scrollWidth<=innerWidth+1})()')
  b.shot(tag+'-detail')
  if width < 400:
   b.raw('Input.dispatchMouseEvent',{'type':'mouseWheel','x':width//2,'y':height//2,'deltaX':0,'deltaY':1800});time.sleep(.3)
   check(tag+'-full-detail-native-scroll','(()=>{const r=document.querySelector(".ff-notification-detail").getBoundingClientRect();return r.top>=0 && r.bottom<=innerHeight+1})()');b.shot(tag+'-detail-scrolled')
  filter_unread();b.wait('document.querySelectorAll(".ff-notification-list li").length===2')
  check(tag+'-unread-filter','document.querySelectorAll(".ff-notification-controls [aria-pressed=true]")[0].textContent==='+q('Unread' if locale=='en' else '未读'))
  mark();b.wait('!document.querySelector(".ff-notification-list [data-notification-id=simulated-1]")')
  check(tag+'-confirmed-single-count',count(1))
  check(tag+'-disappearing-row-focus','document.activeElement===document.querySelector(".ff-notification-controls [aria-pressed=true]")')
  readall();b.wait(count(0));check(tag+'-inbox-wide-read-all','document.querySelectorAll(".ff-notification-list li").length===0')
  b.shot(tag+'-read-all');(R/(tag+'-pre-escape-focus.json')).write_text(json.dumps(b.ev('({activeTag:document.activeElement?.tagName,activeText:document.activeElement?.textContent.slice(0,200),activeClass:document.activeElement?.className,inDialog:!!document.activeElement?.closest(".ff-notification-inbox")})'),indent=2))
  b.key('\ue00c');check(tag+'-escape-restore','!document.querySelector(".ff-notification-inbox") && document.activeElement===document.querySelector(".ff-notification-entry")')
  b.key('\ue007');b.wait('!!document.querySelector(".ff-notification-inbox")');check(tag+'-native-keyboard-reopen','document.querySelector(".ff-notification-inbox").contains(document.activeElement)')
  b.key('\ue008');b.key('\ue004');b.call('input.releaseActions',{})
  check(tag+'-native-tab-contained','document.querySelector(".ff-notification-inbox").contains(document.activeElement)');b.key('\ue00c')
 # Explicit failures and ordinary unavailable path, no silent mock fallback.
 b.viewport(1440,1000);b.nav(base+'?notificationFixture=1&notificationFixtureFailure=read');b.locale('en');open_inbox();loaded();mark()
 b.wait('document.querySelector(".ff-notification-inbox [role=status]").textContent.toLowerCase().includes("denied")')
 check('read-failure-retains-unread',count(2));b.shot('desktop-en-read-failure');readall()
 b.wait('document.querySelector(".ff-notification-inbox [role=status]").textContent.toLowerCase().includes("could not")')
 check('read-all-failure-no-false-zero',count(2));b.shot('desktop-en-read-all-failure')
 b.nav(base);open_inbox();check('ordinary-path-unavailable','!document.querySelector(".ff-notification-list") && !document.querySelector(".ff-notification-count") && document.querySelector(".ff-notification-origin").textContent.toLowerCase().includes("connection unavailable")');b.shot('desktop-en-unavailable')
 for access in ['denied','unknown']:
  b.nav(base+'?notificationFixture=1&notificationFixtureAccess='+access);open_inbox()
  check(access+'-no-messages','!document.querySelector(".ff-notification-list") && !document.querySelector(".ff-notification-count")');b.shot('desktop-en-'+access)
 b.nav(base+'?notificationFixture=1');open_inbox();loaded();read_detail()
 link='.ff-notification-detail a[href]';b.wait('!!document.querySelector('+q(link)+')')
 href=b.ev('document.querySelector('+q(link)+').getAttribute("href")')
 check('safe-fixture-target','(()=>{const u=new URL(document.querySelector('+q(link)+').href);return u.origin===location.origin && /^\/w\/[^/]+\/projects\/[^/]+\/(overview|review)$/.test(u.pathname)})()')
 click(link);b.wait('location.pathname==='+q(urllib.parse.urlsplit(href).path));b.wait('!!document.querySelector(".ff-app-shell")');b.wait('document.body.textContent.includes("SIMULATED project")');check('target-existing-provisional-boundary','document.body.textContent.includes("Provisional presentation") && document.body.textContent.includes("simulated-project")');b.shot('supported-local-fixture-target')
 check('target-navigation-executed','location.pathname==='+q(urllib.parse.urlsplit(href).path))
 b.ev('document.readyState')
 network=[x for x in b.network if x['url'].startswith(('http:','https:'))]
 unexpected=[x for x in network if urllib.parse.urlsplit(x['url']).hostname!='127.0.0.1']
 assert not unexpected,unexpected
 requests=[json.loads(l) for l in (R/'HTTP_REQUESTS.jsonl').read_text().splitlines()]
 mutations=[json.loads(l) for l in (R/'MUTATION_ATTEMPTS.jsonl').read_text().splitlines()] if (R/'MUTATION_ATTEMPTS.jsonl').exists() else []
 assert all(x['method']=='POST' and x['path']=='/api/v1/dev/auth/token' and x['response_status']==403 and not x['forwarded'] for x in mutations),mutations
 assert not [x for x in requests if '/notifications' in x['path']]
 (R/'HTTP_ASSERTIONS.json').write_text(json.dumps({'all_local_receiver_requests':len(requests),'browser_http_requests':len(network),'all_post_attempts':len(mutations),'denied_mock_auth_bootstrap_attempts':len(mutations),'real_backend_requests':0,'notification_http_requests':0,'external_http_requests':len(unexpected),'simulated_reads':'in-memory adapter calls, not HTTP or persistence'},indent=2))
except BaseException:
 rc=1;(R/'FAILURE.txt').write_text(traceback.format_exc());traceback.print_exc()
finally:
 try:b.shot('final-state')
 except BaseException:pass
 (R/'SMOKE_EXIT.json').write_text(json.dumps({'exit':rc,'tree':T,'checks':len(b.checks),'passed':sum(x['passed'] for x in b.checks),'assistance':'trusted CDP pointer/key; focus emulation; DOM locale switching and scrollIntoView; deterministic localhost receiver and explicitly simulated in-memory inbox','physical_device':False,'screen_reader_speech':False,'OS_push':False},indent=2));b.ws.close()
sys.exit(rc)
