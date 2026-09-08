from pathlib import Path
import hashlib,json,time,sys
OUT=Path(__file__).parent
C=OUT.parent.parent
O=C.parent
OLD=C/'prestart-boundary-20260907T181906Z'
def h(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
records=[];start=time.time_ns()
for src,base in [(C/'HISTORICAL_RUN_FILES_BEFORE.json',O),(OLD/'HISTORICAL_CONTINUATION_BASELINE.json',Path('/'))]:
    expected=json.loads(src.read_text());bad=[]
    for rel,r in expected.items():
        p=base/rel
        if not p.is_file() or p.is_symlink():bad.append({'path':str(p),'reason':'missing_or_link'});continue
        if p.stat().st_size!=r['size'] or h(p)!=r['sha256']:bad.append({'path':str(p),'reason':'size_or_sha256'})
    records.append({'source':str(src),'source_sha256':h(src),'files':len(expected),'differences':bad})
name='HISTORICAL_OPENING.json' if len(sys.argv)==1 else sys.argv[1]
assert '/' not in name
result={'start_ns':start,'end_ns':time.time_ns(),'checks':records,'result':'PASS' if all(not x['differences'] for x in records) else 'FAIL','claim':'Referenced historical file current byte comparison only, no writer attribution or continuous immutability','PACK_HISTORICAL_BYTE_IMMUTABILITY':'NOT_RECOVERABLE'}
with (OUT/name).open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
