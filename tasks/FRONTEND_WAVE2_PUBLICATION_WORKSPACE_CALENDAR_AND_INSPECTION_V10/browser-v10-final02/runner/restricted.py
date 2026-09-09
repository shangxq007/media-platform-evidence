import json,time,traceback,sys
from chromium_helpers import Browser,ROOT
b=Browser();results=[]
def ck(n,e):b.check(n,e)
def ev(e):return b.ev(e)
def snap(n):
 b.shot(n);(ROOT/(n+'-DOM.json')).write_text(json.dumps(ev('({html:document.documentElement.outerHTML,focus:document.activeElement.outerHTML,url:location.href})'),ensure_ascii=False,indent=2))
def click(s):
 ev('document.querySelector('+json.dumps(s)+').scrollIntoView({block:"center"})');b.click(s)
def button(t):
 ev('(()=>{const e=[...document.querySelectorAll(".ff-publication button")].find(e=>e.textContent==='+json.dumps(t)+');if(!e)throw Error("button missing: '+t+'");e.setAttribute("data-probe-target","yes")})()');click('[data-probe-target="yes"]');ev('document.querySelectorAll("[data-probe-target]").forEach(e=>e.removeAttribute("data-probe-target"))')
def sel(i,v):ev('(()=>{const e=document.querySelectorAll(".ff-publication select")['+str(i)+'];e.value='+json.dumps(v)+';e.dispatchEvent(new Event("change",{bubbles:true}))})()');time.sleep(.15)
def fresh():
 b.viewport(1440,1000);b.nav('/w/w/projects/p/publication?publicationFixture=1');b.wait('document.querySelectorAll(".ff-publication-row").length===12')
def text(v):
 click('.ff-publication input');b.key('\ue009') if False else None
 b.raw('Input.dispatchKeyEvent',{'type':'keyDown','key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2});b.raw('Input.dispatchKeyEvent',{'type':'keyUp','key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2});b.raw('Input.insertText',{'text':v});time.sleep(.2)
def run(id,fn):
 row={'id':id,'status':'RUNNING','start_assertion':len(b.checks)};results.append(row)
 try:fn();row['status']='PASS'
 except Exception as e:row.update(status='FAIL',error=str(e));snap(id+'-failure');raise
 finally:
  row['end_assertion']=len(b.checks);(ROOT/'SCENARIO_RESULTS.json').write_text(json.dumps(results,indent=2))
def ordinary():
 b.viewport(1440,1000);b.nav('/w/w/projects/p/publication',4201);b.wait('document.body.innerText.includes("Workspace context unavailable")');ck('ordinary no injected provider','!window.__V10 && !document.querySelector(".ff-publication-row")');snap('ordinary-desktop');b.viewport(390,844);snap('ordinary-narrow')
def native():
 fresh();ck('actual AppShell publication route','!!document.querySelector("[data-surface=publication]") && __V10.reads.length===1');ev('window.__submits=[];document.addEventListener("submit",e=>__submits.push({target:e.target.tagName,submitter:e.submitter?.textContent}),true)')
 ck('all publication actions explicit non-submit','[...document.querySelectorAll(".ff-publication button")].every(e=>e.getAttribute("type")==="button")');text('Opening');b.key('\ue007');ck('native Enter no spurious submission','__submits.length===0 && document.querySelectorAll(".ff-publication-row").length===1');click('.ff-publication-row button');b.wait('!!document.querySelector("[role=dialog]")');ck('native dialog initial focus','document.querySelector("[role=dialog]").contains(document.activeElement)');b.key('\ue004');ck('native Tab contained','document.querySelector("[role=dialog]").contains(document.activeElement)');snap('english-detail');b.key('\ue00c');ck('Escape restores launcher','!document.querySelector("[role=dialog]") && document.activeElement.matches(".ff-publication-row button")');snap('english-list')
def locales():
 fresh()
 for locale in ['en','zh-CN']:
  b.locale(locale)
  for width in [1440,390]:
   b.viewport(width,1000 if width==1440 else 844);ck(locale+str(width)+' viewport bounded','document.documentElement.scrollWidth<=innerWidth');snap(locale+'-'+str(width))
 b.locale('en')
def calendar():
 fresh();button('Calendar')
 # Native month stepping from actual clock to fixture month; not a frozen product Date.
 ev('window.__monthBefore=document.querySelector(".ff-publication-results h2").textContent')
 while ev('document.querySelector(".ff-publication-results h2").textContent')!='2024-03':button('Previous month')
 click('[aria-label="2024-03-10"]');ck('DST day seven supplied rows','document.querySelectorAll(".ff-publication-agenda .ff-publication-row").length===7')
 sel(3,'America/New_York');ck('NY cross-midnight excludes midnight from March10','document.querySelectorAll(".ff-publication-agenda .ff-publication-row").length===6');click('[aria-label="2024-03-09"]');ck('cross midnight assigned prior civil day','document.querySelector(".ff-publication-agenda").innerText.includes("midnight")');ck('unscheduled and invalid separate','document.querySelector("[aria-label=Unscheduled]").innerText.includes("unscheduled") && document.querySelector("[aria-label=\\"Indeterminate date\\"]").innerText.includes("invalid")');button('Previous month');ck('leap29 exists no30','!!document.querySelector("[aria-label=\\"2024-02-29\\"]") && !document.querySelector("[aria-label=\\"2024-02-30\\"]")');button('Previous month');button('Previous month');ck('year boundary December2023','document.querySelector(".ff-publication-results h2").textContent==="2023-12"');button('Next month');ck('year rollover January2024','document.querySelector(".ff-publication-results h2").textContent==="2024-01"');snap('calendar-year');button('Today');ck('today explicitly current','!!document.querySelector("[aria-current=date][aria-pressed=true]")');snap('calendar-today')
def filters():
 fresh();sel(0,'b');ck('stable second account only','document.querySelectorAll(".ff-publication-row").length===1 && document.querySelector(".ff-publication-row").innerText.includes("Second story")');button('Calendar');ck('account retained calendar','document.querySelectorAll(".ff-publication select")[0].value==="b"');button('List');sel(0,'');sel(1,'alien-state');ck('unknown raw filter','document.querySelectorAll(".ff-publication-row").length===1');button('Reset filters');text('tie-');ck('tie asc stable','[...document.querySelectorAll(".ff-publication-row button")].map(e=>e.textContent).join(",")==="tie-a,tie-z"');sel(2,'desc');ck('tie desc stable','[...document.querySelectorAll(".ff-publication-row button")].map(e=>e.textContent).join(",")==="tie-a,tie-z"');snap('filters')
def privacy():
 fresh();ck('restricted full DOM omission','!document.documentElement.outerHTML.includes("RESTRICTED_COPY_SENTINEL") && !document.documentElement.outerHTML.includes("RESTRICTED_SUMMARY_SENTINEL") && !document.documentElement.outerHTML.includes("SECRET_URL")');button('Opening story');ck('independent attempt/external identities','["try1","try2","external1","unknown","Delivery rejected"].every(t=>document.querySelector("[role=dialog]").innerText.includes(t))');ck('no URL in detail attributes','!document.querySelector("[role=dialog]").outerHTML.includes("SECRET_URL") && !document.querySelector("[role=dialog] a")');snap('attempt-details');b.key('\ue00c')
def refresh():
 fresh();ev('document.querySelector(".ff-publication-results").scrollTop=100');button('Second story');ev('window.__returnScroll=document.querySelector(".ff-publication-results").scrollTop');b.key('\ue00c');ck('close preserves result scroll','document.querySelector(".ff-publication-results").scrollTop===__returnScroll');ev('__V10.mode("remove")');button('Refresh publications');b.wait('document.querySelectorAll(".ff-publication-row").length===11');ck('removed selection no dialog','!document.querySelector("[role=dialog]") && !document.querySelector(".ff-publication-row button[aria-pressed=true]")');ev('__V10.mode("error")');button('Refresh publications');b.wait('document.body.innerText.includes("Retry publications")');snap('error');ev('__V10.mode("partial")');button('Retry publications');b.wait('document.querySelectorAll(".ff-publication-row").length===0');snap('partial-empty');ck('partial not complete claim','document.querySelector(".ff-publication").innerText.includes("partial") || document.querySelector(".ff-publication").innerText.includes("Partial")');ev('__V10.mode("ready")');button('Refresh publications');b.wait('document.querySelectorAll(".ff-publication-row").length===12');ck('same ID does not reopen','!document.querySelector("[role=dialog]")')
def session():
 fresh();button('Opening story');ev('__V10.renew()');ck('same SDK renewal preserves dialog','!!document.querySelector("[role=dialog]")');ev('__V10.event("UserUnloaded")');b.wait('!document.querySelector("[role=dialog]")');ck('retired old binding cannot reread','!document.querySelector(".ff-publication-row") && __V10.reads.length===1');snap('session-retired');ev('__V10.replace()');b.wait('document.querySelectorAll(".ff-publication-row").length===12');ck('new binding no detail revival','!document.querySelector("[role=dialog]")')
def callbacks():
 fresh();ev('window.__old=[...document.querySelectorAll(".ff-publication button")].map(e=>({e,p:e[Object.keys(e).find(k=>k.startsWith("__reactProps$"))]})).filter(x=>x.p.onClick);true');ev('__V10.mode("loading")');button('Refresh publications');b.wait('__V10.pending.length===1');ev('__V10.scope()');ev('__V10.mode("ready");__V10.replace()');b.wait('document.querySelectorAll(".ff-publication-row").length===12');ev('__old.forEach(x=>x.p.onClick({currentTarget:x.e}));__V10.settle()');ck('retained old callbacks and late read inert','!document.querySelector("[role=dialog]") && document.querySelectorAll(".ff-publication-row").length===12 && document.querySelector(".ff-publication input").value===""');snap('late-nonrevival')
def network():
 ck('no browser mutation attempt',json.dumps(all(x['method']=='GET' for x in b.network)));ck('no intercepted mutation or remote permitted',json.dumps(all(x['method']=='GET' and x['allowed_to_local_receiver'] for x in b.blocked)))
def restrictedMetadata():
 fresh();ev('(()=>{let e=document.querySelector(".ff-publication");let f=e[Object.keys(e).find(k=>k.startsWith("__reactFiber$"))];while(f){if(f.memoizedProps?.source?.adapter){window.__source=f.memoizedProps.source;break}f=f.return}if(!window.__source)throw Error("source fixture not found");window.__read=__source.adapter.read;__source.adapter={origin:"isolated-verification",read:async(r,s)=>{const d=await __read(r,s);d.plans[0].title="PRIVATE_TITLE_SENTINEL";d.plans[0].summary="PRIVATE_SUMMARY_SENTINEL";d.plans[0].copyVersion="PRIVATE_COPY_SENTINEL";d.artifacts[0].name="PRIVATE_ARTIFACT_SENTINEL";d.artifacts[0].mediaType="PRIVATE_MEDIA_SENTINEL";d.attempts[0].failureSummary="PRIVATE_FAILURE_SENTINEL";d.externalPublications[0].url="https://invalid.invalid/PRIVATE_URL_SENTINEL";return d}};delete __source.access["test-only.publication.content:one"];delete __source.access["test-only.publication.artifact:output"];__V10.replace();return true})()');b.wait('document.querySelectorAll(".ff-publication-row").length===12');button('one');ck('restricted title copy artifact failure URL absent full DOM attributes','!["PRIVATE_TITLE_SENTINEL","PRIVATE_SUMMARY_SENTINEL","PRIVATE_COPY_SENTINEL","PRIVATE_ARTIFACT_SENTINEL","PRIVATE_MEDIA_SENTINEL","PRIVATE_FAILURE_SENTINEL","PRIVATE_URL_SENTINEL"].some(s=>document.documentElement.outerHTML.includes(s))');ck('restricted retains independent logical IDs','["one","output","try1","try2","external1"].every(s=>document.querySelector("[role=dialog]").innerText.includes(s))');snap('restricted-metadata-details');b.key('\ue00c');ev('delete __source.access["test-only.publication.list"];__V10.replace()');b.wait('!document.querySelector(".ff-publication-row")');ck('list denied withdraws all details','!document.querySelector("[role=dialog]")');snap('list-denied')
try:
 run('V10-S05',restrictedMetadata);run('V10-S06',network)
except Exception:traceback.print_exc();sys.exit(1)
finally:
 (ROOT/'BOUNDARY_LOGS.json').write_text(json.dumps(ev('window.__V10 ? ({reads:__V10.reads,sdkLog:__V10.sdkLog,boundaryLog:__V10.boundaryLog}):null'),indent=2))
