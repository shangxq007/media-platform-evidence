from chromium_helpers import Browser,ROOT
import json
b=Browser();b.viewport(1440,1000);b.nav('/w/workspace-1/projects/project-1/edit?nleFixture=1');import time;time.sleep(2);b.shot('initial');(ROOT/'DOM.json').write_text(json.dumps(b.ev('({text:document.body.innerText,selects:[...document.querySelectorAll("select")].map(e=>({html:e.outerHTML})),buttons:[...document.querySelectorAll("button")].map(e=>({text:e.innerText,label:e.getAttribute("aria-label")}))})'),ensure_ascii=False,indent=2));b.raw('Browser.close',{})
