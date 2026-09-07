import json,time,traceback,sys
from native_common import CanvasBrowser,R,T
b=CanvasBrowser();b.viewport(1440,1000)
P='.ff-command-palette';S=P+' input[type=search]';L=P+' ul button'
def q(s):return json.dumps(s)
def focused():return b.ev('({tag:document.activeElement.tagName,text:document.activeElement.textContent,search:document.activeElement.matches('+q(S)+')})')
def rec(name,ok,actual=None):b.record(name,'Current bounded palette contract',actual,ok,assistance='Reused Chromium CDP trusted keys/pointer; Input.insertText for search text; synthetic read-only HTTP fixtures; DOM geometry/ARIA reads; focus emulation; DOM locale change helper')
def special(key,code,vk):
 for typ in ['keyDown','keyUp']:b.raw('Input.dispatchKeyEvent',{'type':typ,'key':key,'code':code,'windowsVirtualKeyCode':vk})
 time.sleep(.08)
def search(text):
 b.click(S)
 for typ,key,code,vk,mods in [('keyDown','Control','ControlLeft',17,2),('keyDown','a','KeyA',65,2),('keyUp','a','KeyA',65,2),('keyUp','Control','ControlLeft',17,0)]:b.raw('Input.dispatchKeyEvent',{'type':typ,'key':key,'code':code,'windowsVirtualKeyCode':vk,'modifiers':mods})
 b.raw('Input.insertText',{'text':text});time.sleep(.15)
def palette():
 assert b.ev('document.querySelectorAll("button:has(kbd)").length')==1
 b.click('button:has(kbd)')
 b.wait('!!document.querySelector('+q(S)+')')
def names():return b.ev('Array.from(document.querySelectorAll('+q(L+':not(:disabled)')+'),e=>e.textContent)')
def layout():return b.ev('(()=>{const d=document.querySelector('+q(P)+'),i=d.querySelector("input"),h=d.querySelector("header"),r=d.getBoundingClientRect();return {dialog:{x:r.x,y:r.y,right:r.right,bottom:r.bottom},heading:h.getBoundingClientRect().bottom,search:i.getBoundingClientRect().bottom,width:innerWidth,height:innerHeight,overflow:document.documentElement.scrollWidth>innerWidth}})()')
rc=0
try:
 b.nav('/w/ux-workspace/projects/ux-project/canvas');b.wait('document.querySelectorAll("[data-canvas-node]").length===2');b.locale('en');b.click('[data-canvas-node="note-node"]')
 selected=b.ev('Array.from(document.querySelectorAll("[data-canvas-node][aria-pressed=true]"),e=>e.dataset.canvasNode)')
 palette();rec('open-search-focus',focused()['search'],focused())
 enabled=names();assert enabled
 b.key('\ue015');rec('arrow-down-first',focused()['text']==enabled[0],focused())
 b.key('\ue013');rec('first-boundary-clamped',focused()['text']==enabled[0],focused())
 special('End','End',35);rec('end-last',focused()['text']==enabled[-1],focused())
 b.key('\ue015');rec('last-boundary-clamped',focused()['text']==enabled[-1],focused())
 special('Home','Home',36);rec('home-first',focused()['text']==enabled[0],focused())
 rec('focus-not-selection',b.ev('Array.from(document.querySelectorAll("[data-canvas-node][aria-pressed=true]"),e=>e.dataset.canvasNode)')==selected)
 b.shot('desktop-en-focus')
 search('no-such-command-xyz');b.key('\ue007');rec('no-match-enter-no-execute',not names() and focused()['search'] and b.ev('!!document.querySelector('+q(P)+')'),focused());b.shot('desktop-en-empty')
 search('Apply');disabled=b.ev('Array.from(document.querySelectorAll('+q(L)+'),e=>({disabled:e.disabled,description:e.getAttribute("aria-describedby"),text:e.textContent}))');rec('all-unavailable-native-disabled',bool(disabled) and all(d['disabled'] for d in disabled),disabled)
 b.key('\ue015');b.key('\ue007');rec('all-unavailable-no-activation',focused()['search'] and b.ev('!!document.querySelector('+q(P)+')'))
 b.click(L);rec('disabled-pointer-no-execute',b.ev('!!document.querySelector('+q(P)+')'))
 rec('unavailable-described',all(d['description'] for d in disabled),disabled);b.shot('desktop-en-unavailable')
 search('Clear selection');b.key('\ue015');b.key('\ue007');b.wait('!document.querySelector('+q(P)+')')
 rec('native-enter-shared-clear',not b.ev('document.querySelector("[data-canvas-node][aria-pressed=true]")!==null'))
 palette();rec('removed-context-command-not-retained',not any('Inspect node' in n for n in names()),names())
 b.key('\ue00c');rec('escape-focus-return','Commands' in (focused()['text'] or ''),focused())
 # New target via real pointer, not direct Selection mutation
 b.click('[data-canvas-node="project-node"]');palette();rec('current-target-reprojected',any('Inspect node' in n for n in names()) and not any('Local composition note' in n for n in names()),names())
 search('Clear selection');b.key('\ue015');b.key(' ');b.wait('!document.querySelector('+q(P)+')');rec('native-space-clear',not b.ev('document.querySelector("[data-canvas-node][aria-pressed=true]")!==null'))
 b.locale('zh-CN');b.viewport(390,844);palette();rec('zh-search-focus',focused()['search'],focused());dims=layout();rec('narrow-layout-heading-search-visible',dims['dialog']['right']<=dims['width']+1 and dims['heading']<dims['height'] and dims['search']<dims['height'],dims)
 b.key('\ue013');rec('reverse-entry-last',focused()['text']==names()[-1],focused());b.shot('narrow-zh-focus')
 search('no-such-command-xyz');rec('zh-no-match-announced',b.ev('document.querySelector('+q(P+' [role=status]')+')?.textContent.includes("未") || document.querySelector('+q(P+' [role=status]')+')?.textContent.includes("没有")'),b.ev('document.querySelector('+q(P+' [role=status]')+')?.textContent'));b.shot('narrow-zh-empty')
 b.key('\ue00c');b.locale('en');b.viewport(1440,1000)
 # Long user-owned note title through the existing Inspector input.
 b.click('[data-canvas-node="note-node"]');b.click('input[maxlength="120"]')
 for typ,key,code,vk,mods in [('keyDown','Control','ControlLeft',17,2),('keyDown','a','KeyA',65,2),('keyUp','a','KeyA',65,2),('keyUp','Control','ControlLeft',17,0)]:b.raw('Input.dispatchKeyEvent',{'type':typ,'key':key,'code':code,'windowsVirtualKeyCode':vk,'modifiers':mods})
 b.raw('Input.insertText',{'text':'LongLocalNote_'+'LongTargetLabel'*6});b.viewport(390,844);palette();b.key('\ue015');dims=layout();rec('narrow-long-label-layout',dims['dialog']['right']<=dims['width']+1 and dims['search']<dims['height'],dims);b.shot('narrow-en-long-label-focus')
 special('End','End',35);v=b.ev('(()=>{const r=document.activeElement.getBoundingClientRect(),l=document.querySelector('+q(P+' ul')+').getBoundingClientRect();return {top:r.top,bottom:r.bottom,listTop:l.top,listBottom:l.bottom}})()');rec('focused-result-scrolled-visible',v['top']>=v['listTop']-1 and v['bottom']<=v['listBottom']+1,v);b.shot('narrow-en-end-focus')
 b.key('\ue00c')
except BaseException:
 rc=1;(R/'FAILURE.txt').write_text(traceback.format_exc());traceback.print_exc()
finally:
 try:b.shot('final-state')
 except BaseException:pass
 (R/'SMOKE_EXIT.json').write_text(json.dumps({'exit':rc,'checks':len(b.checks),'passed':sum(x['passed'] for x in b.checks),'tree':T,'physical_device':False,'screen_reader':False,'OS_IME':False},indent=2));b.ws.close()
sys.exit(rc)
