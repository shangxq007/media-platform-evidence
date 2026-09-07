"""Focused Review flow only; existing Chromium helpers, deterministic mock HTTP."""
import json,time,traceback,sys
from pathlib import Path
from chromium_helpers import Browser
from control import T,now
R=Path(__file__).parent;b=Browser();rc=0
assistance='Chromium CDP trusted pointer/key events; DOM scroll/geometry/ARIA reads; focus emulation; synthetic locale change; deterministic mock HTTP through existing production gateway. No device/screen-reader/OS IME evidence.'
def q(s):return json.dumps(s)
def key(key,code,vk):
 for typ in ('keyDown','keyUp'):b.raw('Input.dispatchKeyEvent',{'type':typ,'key':key,'code':code,'windowsVirtualKeyCode':vk})
 time.sleep(.08)
def rec(name,expression):b.check(name,expression)
def view(selector):b.ev('document.querySelector('+q(selector)+').scrollIntoView({block:"center"})');time.sleep(.08)
def choose(index,offset):
 selector='.ff-review-compare-controls label:nth-of-type('+str(index)+') select'
 view(selector);b.click(selector);key('Home','Home',36)
 for _ in range(offset):b.key('\ue015')
 b.key('\ue007')
def compare():
 b.ev('(()=>{const e=document.querySelector(".ff-review-compare-controls button");if(!e)throw Error("missing compare");e.scrollIntoView({block:"center"});})()')
 b.click('.ff-review-compare-controls button')
def mode(value):(R/'fixture-mode.txt').write_text(value)
def geometry():
 return '(()=>{const root=document.querySelector(".ff-review-compare-controls");return !!root && root.getBoundingClientRect().right<=innerWidth+1 && [...root.querySelectorAll("select")].every(e=>e.getBoundingClientRect().width>40 && e.getBoundingClientRect().right<=innerWidth+1) && document.documentElement.scrollWidth<=innerWidth+1})()'
try:
 for lang,width,height in [('en',1440,1000),('en',390,844),('zh-CN',1440,1000),('zh-CN',390,844)]:
  tag=('desktop' if width>400 else 'narrow')+'-'+lang
  mode('ready');b.viewport(width,height);b.nav('/w/ux-workspace/projects/ux-project/review');b.locale(lang)
  b.wait('document.querySelectorAll(".ff-review-compare-controls select option").length===8')
  rec(tag+'-explicit-empty-start','[...document.querySelectorAll(".ff-review-compare-controls select")].every(e=>e.value==="") && document.querySelector(".ff-review-compare-controls button").disabled')
  choose(1,1);choose(2,2)
  rec(tag+'-native-ordered-selection','(()=>{const s=document.querySelectorAll(".ff-review-compare-controls select");return s[0].value.startsWith("review-1-") && s[1].value.startsWith("review-2-") && !document.querySelector(".ff-review-compare-controls button").disabled})()')
  b.key('\ue004');rec(tag+'-tab-to-compare-visible-focus','document.activeElement===document.querySelector(".ff-review-compare-controls button") && document.activeElement.matches(":focus-visible")')
  b.key('\ue007');b.wait('document.body.textContent.includes("fixture-modified-track")')
  rec(tag+'-result-and-focus-stable','document.body.textContent.includes("fixture-added-clip-") && document.activeElement===document.querySelector(".ff-review-compare-controls button")')
  rec(tag+'-long-label-layout',geometry());b.shot(tag+'-result')
  selector='.ff-semantic-diff select';view(selector);b.click(selector);key('End','End',35);b.key('\ue007')
  rec(tag+'-filter-local-result','document.querySelector(".ff-semantic-diff select").value==="MODIFIED" && document.body.textContent.includes("fixture-modified-track") && !document.querySelector(".ff-entity-change-list")?.textContent.includes("fixture-added-clip-")')
  b.shot(tag+'-filtered')
  rec(tag+'-labels-and-tab-links','(()=>{const c=document.querySelector(".ff-review-compare-controls");const tab=document.querySelector("[role=tab][aria-selected=true]");const panel=document.getElementById(tab.getAttribute("aria-controls"));return [...c.querySelectorAll("select")].every(s=>s.labels.length>0) && panel?.getAttribute("aria-labelledby")===tab.id})()')
  if lang=='zh-CN':rec(tag+'-localized-flow','!document.querySelector(".ff-review-compare-controls").textContent.includes("From revision") && !document.querySelector(".ff-semantic-diff").textContent.includes("Tracks added")')
 # Representative retryable unavailable -> explicit retry -> denied nonretryable.
 b.viewport(1440,1000);b.locale('en');mode('unavailable');compare()
 b.wait('document.body.textContent.includes("MOCK_SERVER_UNAVAILABLE")')
 rec('failed-refresh-clears-prior-success','!document.querySelector(".ff-entity-change-list") && !!document.querySelector("[role=alert]") && !document.querySelector(".ff-review-compare-controls button").disabled')
 b.shot('desktop-en-unavailable');mode('ready');compare();b.wait('document.body.textContent.includes("fixture-modified-track")');rec('retry-success','!!document.querySelector(".ff-entity-change-list")')
 mode('denied');compare();b.wait('document.body.textContent.includes("MOCK_SERVER_DENIED")')
 rec('denied-not-retryable','document.querySelector(".ff-review-compare-controls button").disabled && !document.querySelector(".ff-entity-change-list")');b.shot('desktop-en-denied')
 # New explicit pair permits a new read; unsupported response not a fake empty success.
 choose(1,3);mode('unsupported');compare();b.wait('!!document.querySelector(".ff-semantic-diff")')
 rec('unsupported-not-zero-success','!document.querySelector(".ff-entity-change-list") && document.querySelector(".ff-semantic-diff").textContent.toLowerCase().includes("summary")');b.shot('desktop-en-unsupported')
 mode('empty');compare();b.wait('document.querySelector(".ff-semantic-diff")?.textContent.toLowerCase().includes("no changes")');rec('supported-no-changes','!document.querySelector(".ff-entity-change-list")');b.shot('desktop-en-no-changes')
 requests=[json.loads(line) for line in (R/'HTTP_REQUESTS.jsonl').read_text().splitlines()]
 comparisons=[x for x in requests if x['path'].endswith('/revisions/compare')]
 assert comparisons and all(set(x['query'])=={'from','to'} for x in comparisons)
 assert not (R/'MUTATION_ATTEMPTS.jsonl').exists()
 (R/'HTTP_ASSERTIONS.json').write_text(json.dumps({'requests':len(requests),'comparisons':len(comparisons),'all_explicit_ordered_pairs':True,'mutation_attempts':0,'backend_endpoints_called':0},indent=2))
except BaseException:
 rc=1;(R/'FAILURE.txt').write_text(traceback.format_exc());traceback.print_exc()
finally:
 try:b.shot('final-state')
 except BaseException:pass
 result={'exit':rc,'tree':T,'checks':len(b.checks),'passed':sum(x['passed'] for x in b.checks),'assistance':assistance,'physical_device':False,'screen_reader':False,'OS_IME':False,'build_manifest_sha256':json.loads((R/'BUILD_ARTIFACT_BOUNDARY.json').read_text())['build_manifest_sha256']}
 (R/'SMOKE_EXIT.json').write_text(json.dumps(result,indent=2));b.ws.close()
sys.exit(rc)
