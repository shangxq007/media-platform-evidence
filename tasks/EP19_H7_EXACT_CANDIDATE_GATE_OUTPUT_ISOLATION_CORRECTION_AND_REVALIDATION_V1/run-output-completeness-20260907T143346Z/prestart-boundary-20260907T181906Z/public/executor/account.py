"""Exact structured identity accounting; synthetic inputs are qualification only."""
from pathlib import Path
from collections import Counter
import ast,csv,hashlib,json,os,re,xml.etree.ElementTree as ET

def canonical(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def fe_identity(file,ancestors,title,root):
 p=Path(file);root=Path(root)
 if not p.is_absolute():p=root/p
 rel=p.relative_to(root).as_posix()
 if '..' in Path(rel).parts:raise ValueError('INPUT_PATH_ESCAPE')
 if not isinstance(ancestors,list) or not all(isinstance(x,str) for x in ancestors) or not isinstance(title,str):raise ValueError('INVALID_STRUCTURED_IDENTITY')
 return canonical({'file':rel,'ancestorTitles':ancestors,'title':title})
def reconcile(expected,observed,expected_skips=()):
 e=Counter(expected);o=Counter(i for i,s in observed);statuses=Counter(s for i,s in observed)
 if any(v!=1 for v in e.values()) or not e:raise ValueError('EMPTY_OR_DUPLICATE_EXPECTATION')
 if set(statuses)-{'PASS','FAIL','ERROR','SKIPPED'}:raise ValueError('UNKNOWN_STATUS')
 skipped={i for i,s in observed if s=='SKIPPED'};wanted_skips=set(expected_skips)
 result={'expected':len(expected),'executed':len(observed),'passed':statuses['PASS'],'skipped':statuses['SKIPPED'],'expected_skipped':len(wanted_skips),'failed':statuses['FAIL'],'errored':statuses['ERROR'],'missing':sum((e-o).values()),'unexpected':sum(v for k,v in o.items() if k not in e),'duplicate':sum(v-1 for v in o.values() if v>1),'missing_identities':sorted(e.keys()-o.keys()),'unexpected_identities':sorted(o.keys()-e.keys()),'unexpected_skipped_identities':sorted(skipped-wanted_skips),'expected_skips_not_observed':sorted(wanted_skips-skipped)}
 result['result']='PASS' if not any(result[k] for k in ['failed','errored','missing','unexpected','duplicate','unexpected_skipped_identities','expected_skips_not_observed']) else 'FAIL'
 return result

def xml_rows(root):
 rows=[]
 for p in sorted(Path(root).glob('**/build/test-results/test/TEST-*.xml')):
  parts=p.relative_to(root).parts;i=parts.index('build');task=':'+':'.join(parts[:i])+':test';x=ET.parse(p).getroot()
  if x.tag!='testsuite':raise ValueError('UNSUPPORTED_XML_ROOT')
  cases=x.findall('testcase')
  if int(x.attrib['tests'])!=len(cases):raise ValueError('XML_COUNT_MISMATCH')
  counts=Counter()
  for c in cases:
   types=[s for s in ['error','failure','skipped'] if c.find(s) is not None]
   if len(types)>1:raise ValueError('AMBIGUOUS_XML_STATUS')
   status={'error':'ERROR','failure':'FAIL','skipped':'SKIPPED'}.get(types[0] if types else '', 'PASS');counts[status]+=1
   rows.append((canonical([task,c.attrib['classname'],c.attrib['name']]),status))
  for attr,status in [('failures','FAIL'),('errors','ERROR'),('skipped','SKIPPED')]:
   if int(x.attrib.get(attr,0))!=counts[status]:raise ValueError('XML_STATUS_COUNTER_MISMATCH')
 return rows

def frontend_rows(path,root):
 j=json.loads(Path(path).read_text());rows=[]
 if j.get('success') is not True or j.get('numRuntimeErrorTestSuites',0)!=0:raise ValueError('FRONTEND_REPORTER_NOT_SUCCESS')
 for suite in j['testResults']:
  for c in suite['assertionResults']:
   status={'passed':'PASS','failed':'FAIL','pending':'SKIPPED','todo':'SKIPPED'}.get(c['status'])
   if status is None:raise ValueError('UNKNOWN_FRONTEND_STATUS')
   rows.append((fe_identity(suite['name'],c['ancestorTitles'],c['title'],root),status))
 if j.get('numTotalTests')!=len(rows):raise ValueError('FRONTEND_TOTAL_MISMATCH')
 return rows

def unittest_rows(path):
 text=Path(path).read_text()
 rows=[(m.group(1),'PASS' if m.group(2)=='ok' else m.group(2)) for m in re.finditer(r'^(test_\S+)\s+\(.*?\)\s+\.\.\. (ok|FAIL|ERROR)$',text,re.M)]
 m=re.search(r'^Ran (\d+) tests? in ',text,re.M)
 if not m or int(m.group(1))!=len(rows):raise ValueError('UNITTEST_RAW_COUNT_MISMATCH')
 return rows
