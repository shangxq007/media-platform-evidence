"""Independent offline integrity verifier; never executes packaged code."""
from pathlib import Path,PurePosixPath
import hashlib,json,zipfile,stat,sys

def sha(b): return hashlib.sha256(b).hexdigest()
def verify(root):
 root=Path(root).resolve(); mb=(root/'MANIFEST.json').read_bytes();m=json.loads(mb)
 entries=m['files']; names=[e['path'] for e in entries]
 assert len(names)==len(set(names))==m['file_count']
 for n in names:
  p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts
  assert not any(x in ('private','tools','__pycache__') for x in p.parts)
 expected=set(names)|{'MANIFEST.json'}
 zpath=root/'V11_OUTCOME_C_LOCAL_REVIEW.zip'
 with zipfile.ZipFile(zpath) as z:
  infos=z.infolist(); assert len(infos)==len(expected)
  assert len({i.filename for i in infos})==len(infos)
  assert {i.filename for i in infos}==expected
  assert z.testzip() is None
  for i in infos: assert not stat.S_ISLNK(i.external_attr>>16)
  assert z.read('MANIFEST.json')==mb
  for e in entries:
   disk=root/'payload'/e['path'];assert not disk.is_symlink()
   b=disk.read_bytes(); zb=z.read(e['path'])
   assert b==zb and len(b)==e['bytes'] and sha(b)==e['sha256'],e['path']
 actual={str(p.relative_to(root/'payload')) for p in (root/'payload').rglob('*') if p.is_file()}
 assert actual==set(names)
 selection=json.loads((root/'payload/SOURCE_SELECTION.json').read_text())
 deploy=[r for r in selection['source_files'] if r['path'].startswith('deployment/')]
 assert len(deploy)==19 and len(selection['source_files'])==42
 byname={e['path']:e for e in entries}
 for r in selection['source_files']:
  assert r['sha256']==byname[r['path']]['sha256'] and r['bytes']==byname[r['path']]['bytes']
 machine=json.loads((root/'payload/REPORT.machine.json').read_text())
 assert machine['outcome']=='C' and machine['synthetic_validation']['behavioral_assertions_executed']==0
 assert machine['synthetic_validation']['setup_errors']==1
 assert len(machine['endpoint_allowlist'])==2
 assert all(v=='NOT_YET_PUBLISHED' for v in machine['publication'].values())
 result={'status':'PASS','scope':'PACKAGE_INTEGRITY_ONLY_NOT_PRODUCT_ACCEPTANCE','payload_file_count':len(entries),'zip_member_count':len(infos),'payload_total_bytes':sum(e['bytes'] for e in entries),'deployment_allowlist_count':len(deploy),'selected_source_count':len(selection['source_files']),'zip_bytes':zpath.stat().st_size,'sha256':{'zip':sha(zpath.read_bytes()),'manifest':sha(mb),'report':sha((root/'payload/REPORT.zh-CN.md').read_bytes()),'machine_report':sha((root/'payload/REPORT.machine.json').read_bytes()),'verifier':sha((root/'verify_integrity.py').read_bytes())},'checks':{'exact_members_no_duplicates':True,'zip_crc':True,'all_payload_bytes_hashes':True,'disk_payload_exact_members':True,'no_private_tools_members':True,'source_selection_matches_payload':True,'outcome_c_and_zero_behavior_assertions':True,'all_publication_fields_not_yet_published':True},'not_verified':['adapter behavior','deployment runtime','product acceptance','remote publication','cryptographic authenticity against an independently trusted manifest'],'self_hash_policy':'This verification receipt is external to the zip; its hash is delivered separately.'}
 (root/'integrity-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': verify(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent)
