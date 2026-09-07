"""Bounded URI scheme regression controls; no network or product gates."""
from pathlib import Path
import json, os, sys, unittest, uuid
D=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(D/'executor'))
import execution, parsers, vite_closure

class SchemeControls(unittest.TestCase):
 def setUp(self):
  self.root=Path(os.environ['EP19_QUALIFICATION_ROOT'])/(self._testMethodName+'-'+uuid.uuid4().hex[:8]);self.root.mkdir()
 def check(self,raw,context,base='/',accept=False):
  case=self.root/uuid.uuid4().hex[:8];run=case/'run';out=run/'runtime/outputs/frontend';gate=run/'runtime/gates/FRONTEND_BUILD'
  (out/'assets').mkdir(parents=True);(out/'.vite').mkdir();gate.mkdir(parents=True)
  html='<script src="/assets/main.js"></script>';js='export default 1';css='a{color:red}'
  manifest={'index.html':{'file':'assets/main.js','isEntry':True,'css':['assets/main.css']}}
  if context=='html':html+='<script src="'+raw+'"></script>'
  elif context=='js':js='import '+json.dumps(raw)+';'
  elif context=='dynamic':js='import('+json.dumps(raw)+');'
  elif context=='url':js='new URL('+json.dumps(raw)+', import.meta.url);'
  elif context=='url_base':js='new URL("x.js", '+json.dumps(raw)+');'
  elif context=='css':css='a{background:url("'+raw+'")}'
  elif context=='css_import':css='@import "'+raw+'";'
  elif context=='manifest':manifest['index.html']['assets']=[raw]
  elif context=='base':base=raw
  (out/'assets/local image.js').write_text('export default 1');(out/'assets/local image.css').write_text('x{color:red}')
  (out/'index.html').write_text(html);(out/'assets/main.js').write_text(js);(out/'assets/main.css').write_text(css)
  (out/'.vite/manifest.json').write_text(json.dumps(manifest));(gate/'native.log').write_text('built in 1s\n')
  (gate/'resolution.json').write_text(json.dumps({'outDir':str(out),'base':base,'emptyOutDir':True}))
  outcomes=[]
  for name,fn in [('closure',lambda:vite_closure.validate(out,base,D/'tools',case/'closure.json')),('parser',lambda:parsers.parse('FRONTEND_BUILD',run,gate,case))]:
   try:fn();actual='PASS'
   except RuntimeError as ex:
    actual='REJECT'
    logs=list(case.rglob('*.native.log'));self.assertTrue(any('VITE_UNSUPPORTED_SCHEME' in p.read_text() or 'VITE_URL_CONTROL' in p.read_text() for p in logs),str(ex))
   outcomes.append({'path':name,'expected':'PASS' if accept else 'REJECT','actual':actual})
  (case/'control.json').write_text(json.dumps({'raw':raw,'context':context,'outcomes':outcomes},indent=2)+'\n')
  self.assertTrue(all(x['actual']==x['expected'] for x in outcomes),outcomes)
 def test_file_and_unsupported_schemes_rejected(self):
  for context in ['html','js','dynamic','url','url_base','css','css_import','manifest','base']:
   for raw in ['file:///tmp/outside.js','FiLe:///tmp/outside.js','ftp://example.test/a','javascript:alert(1)','blob:https://example.test/id','custom:asset']:
    with self.subTest(context=context,raw=raw):self.check(raw,context)
 def test_url_controls_and_nonhierarchical_bases_rejected(self):
  for raw,context in [('fi\tle:///tmp/a','html'),('data:text/plain,a','base'),('data:text/plain,a','url_base'),('data:text/plain,a','manifest')]:
   with self.subTest(raw=raw,context=context):self.check(raw,context)
 def test_supported_external_and_data_references(self):
  for raw in ['http://example.test/x','https://example.test/x','//example.test/x','data:text/javascript,export default 1']:
   for context in ['html','js','dynamic','url','css','css_import']:
    with self.subTest(raw=raw,context=context):self.check(raw,context,accept=True)
  self.check('https://example.test/', 'url_base',accept=True)
  self.check('/assets/local image.js', 'html',accept=True)
  self.check('/assets/local%20image.css', 'css_import',accept=True)

if __name__=='__main__':unittest.main(verbosity=2)
