from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter
import hashlib,json
EXPECTED=frozenset([
 'com.example.platform.sandbox.BubblewrapSandboxProcessLauncherIntegrationTest#real_bubblewrap_enforces_the_advertised_host_binary_boundaries()',
 'com.example.platform.sandbox.ContainerSandboxProcessLauncherIntegrationTest#rootful_engine_unavailability_diagnostic_classification_is_exact()',
 'com.example.platform.sandbox.ContainerSandboxProcessLauncherIntegrationTest#rootless_container_mechanically_enforces_the_advertised_boundaries()'])
EXPECTED_HASH=hashlib.sha256(('\n'.join(sorted(EXPECTED))+'\n').encode()).hexdigest()
def summarize(paths):
 rows=[];malformed=[]
 for p in sorted(map(Path,paths)):
  try:root=ET.parse(p).getroot()
  except (ET.ParseError,OSError) as e:malformed.append({'path':str(p),'error':str(e)});continue
  for t in root.iter('testcase'):
   c=t.get('classname','');name=t.get('name','');identity=c+'#'+name
   status='ERROR' if t.find('error') is not None else 'FAIL' if t.find('failure') is not None else 'SKIP' if t.find('skipped') is not None else 'PASS'
   rows.append({'class':c,'identity':name,'key':identity,'result':status,'raw_xml':str(p),'detail':'\n'.join((x.get('message','')+'\n'+(x.text or '')) for x in list(t))})
 actual=Counter(r['key'] for r in rows);counts=Counter(r['result'] for r in rows);missing=sorted(EXPECTED-set(actual));unexpected=sorted(set(actual)-EXPECTED);duplicates=sum(n-1 for n in actual.values() if n>1)
 classification='FAIL_MALFORMED_XML' if malformed else 'FAIL_DUPLICATE_IDENTITY' if duplicates else 'FAIL_UNEXPECTED_IDENTITY' if unexpected else 'FAIL_MISSING_IDENTITY' if missing else 'FAIL_TEST_ERROR' if counts['ERROR'] else 'FAIL_TEST_FAILURE' if counts['FAIL'] else 'FAIL_TEST_SKIP' if counts['SKIP'] else 'PASS'
 def subset_pass(prefix):
  required={k for k in EXPECTED if k.startswith(prefix)}
  return all(actual[k]==1 and any(r['key']==k and r['result']=='PASS' for r in rows) for k in required)
 return {'result':classification,'expected_identities':sorted(EXPECTED),'H02_EXPECTED_IDENTITY_SET_HASH':EXPECTED_HASH,'H02_EXPECTED_IDENTITY_COUNT':len(EXPECTED),'H02_ACTUAL_IDENTITY_COUNT':len(rows),'H02_MISSING_IDENTITY_COUNT':len(missing),'H02_UNEXPECTED_IDENTITY_COUNT':len(unexpected),'H02_FAILED_IDENTITY_COUNT':counts['FAIL'],'H02_ERROR_IDENTITY_COUNT':counts['ERROR'],'H02_SKIPPED_IDENTITY_COUNT':counts['SKIP'],'H02_DUPLICATE_IDENTITY_COUNT':duplicates,'malformed_xml':malformed,'missing':missing,'unexpected':unexpected,'identities':rows,'BWRAP_RUNTIME_PREFLIGHT':'PASS' if subset_pass('com.example.platform.sandbox.Bubblewrap') else 'FAIL','CONTAINER_RUNTIME_PREFLIGHT':'PASS' if subset_pass('com.example.platform.sandbox.Container') else 'FAIL','RUNTIME_CAPABILITY_PREFLIGHT':'PASS' if classification=='PASS' else 'FAIL','RAW_RUNTIME_TEST_EXPECTED_COUNT':len(EXPECTED),'RAW_RUNTIME_TEST_ACTUAL_COUNT':len(rows),'RAW_RUNTIME_TEST_PASSED_COUNT':counts['PASS'],'RAW_RUNTIME_TEST_FAILED_COUNT':counts['FAIL'],'RAW_RUNTIME_TEST_ERROR_COUNT':counts['ERROR'],'RAW_RUNTIME_TEST_SKIPPED_COUNT':counts['SKIP']}
def main():
 from control import A,T,load,j,h,ENV
 import csv,time
 paths=list((A/'runtime-preflight-xml').glob('TEST-*.xml'));s=summarize(paths);rec=load('RUNTIME_CAPABILITY_PREFLIGHT_RAW_LOG.txt.receipt.json')
 # Independent direct raw-node reconciliation, never selecting whichever representation says PASS.
 direct=[]
 for p in sorted(paths):
  for t in ET.parse(p).getroot().iter('testcase'):
   direct.append((t.get('classname','')+'#'+t.get('name',''),'ERROR' if t.find('error') is not None else 'FAIL' if t.find('failure') is not None else 'SKIP' if t.find('skipped') is not None else 'PASS'))
 contradiction=int(sorted(direct)!=sorted((r['key'],r['result']) for r in s['identities']))
 passed=s['result']=='PASS' and rec['exit_code']==0 and not rec['tracked_write_events'] and not contradiction
 s.update({'RUNTIME_CAPABILITY_PREFLIGHT':'PASS' if passed else 'FAIL','RAW_XML_SUMMARY_CONTRADICTION_COUNT':contradiction,'PRIMARY_TRACKED_WRITE_EVENT_COUNT_DURING_RUNTIME_PREFLIGHT':len(rec['tracked_write_events']),'ATTEMPT_7_NATIVE_CONTAINER_RUNTIME':'PASS' if passed else 'FAIL','execution_tree':T,'host_runtime_inventory_sha256':h(A/'HOST_RUNTIME_INVENTORY.json'),'PRIMARY_HOST_NATIVE_RUNTIME_SEMANTICS':'YES','OUTER_SANDBOX_USED':'NO','DOCKER_HOST':ENV.get('DOCKER_HOST'),'preflight_results_count_toward_full_suite':False})
 for r in s['identities']:r['raw_xml']=str(Path(r['raw_xml']).relative_to(A))
 j('RUNTIME_CAPABILITY_PREFLIGHT.json',s)
 j('CONTAINER_RUNTIME_DIAGNOSTIC.json',{'ATTEMPT_3_CONTAINER_DIAGNOSTIC':'CLOSED_BY_ATTEMPT_5_RAW_NATIVE_XML','ATTEMPT_3_CONTAINER_DIAGNOSTIC_CLOSED':'YES','ATTEMPT_7_NATIVE_CONTAINER_RUNTIME':'PASS' if passed else 'FAIL','CONTAINER_RUNTIME_DIAGNOSTIC_CLASSIFICATION':'HOST_NATIVE_RUNTIME_PREFLIGHT_PASS' if passed else s['result'],'UNRESOLVED_CONTAINER_FAILURE_DIAGNOSTIC_COUNT':0 if passed else 1,'raw_xml_summary_contradiction_count':contradiction,'historical_diagnostic_is_not_reopened_by_a_derived_summary':True})
 cols=['expected_class','expected_identity','expected','observed','result','raw_xml','missing','unexpected','notes'];rows=[]
 for k in sorted(EXPECTED|{r['key'] for r in s['identities']}):
  observed=[r for r in s['identities'] if r['key']==k];c,n=k.split('#',1)
  rows.append([c,n,'YES' if k in EXPECTED else 'NO','YES' if observed else 'NO',observed[0]['result'] if observed else 'MISSING',';'.join(r['raw_xml'] for r in observed),'YES' if not observed else 'NO','YES' if k not in EXPECTED else 'NO','exact identity set; occurrences='+str(len(observed))])
 with (A/'RUNTIME_PREFLIGHT_IDENTITY_RECONCILIATION.tsv').open('w') as f:
  w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(cols);w.writerows(rows)
 if not passed:j('STOP.json',{'result':'FAIL_HARNESS' if contradiction else 'FAIL_RUNTIME_PREFLIGHT','gate':'H02','reason':'RAW_XML_SUMMARY_CONTRADICTION' if contradiction else s['result'],'time':time.time()})
 print(json.dumps(s,indent=2))
if __name__=='__main__':main()
