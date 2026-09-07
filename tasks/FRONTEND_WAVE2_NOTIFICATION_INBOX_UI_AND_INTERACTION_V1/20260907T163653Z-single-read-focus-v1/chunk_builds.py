"""Make additive, byte-exact review chunks without rebuilding either tree."""
from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;P=E/'public'
records=[]
for label,root in [('baseline-build',P/'baseline-build'),('final-build',P/'build')]:
 for original in sorted(root.rglob('*.js')):
  raw=original.read_bytes()
  if len(raw)<=90000:continue
  rel=str(original.relative_to(P));dest=P/'review-chunks'/label/original.name;dest.mkdir(parents=True,exist_ok=False)
  offset=0;parts=[]
  while offset<len(raw):
   end=min(offset+64000,len(raw))
   while True:
    try:raw[offset:end].decode('utf-8');break
    except UnicodeDecodeError as err:
     if err.start==0:raise
     end=offset+err.start
   payload=raw[offset:end];name=f'{len(parts)+1:04d}.txt';(dest/name).write_bytes(payload)
   parts.append({'order':len(parts)+1,'path':str((dest/name).relative_to(P)),'offset':offset,'end':end,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()});offset=end
  reconstructed=b''.join((P/x['path']).read_bytes() for x in parts);assert reconstructed==raw
  records.append({'original':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'parts':parts,'reconstructed_equal':True})
(P/'RECONSTRUCTION_MAP.json').write_text(json.dumps({'encoding':'UTF-8 boundary-aligned raw byte parts; concatenate strictly in order; no newline insertion','files':records},indent=2)+'\n')
print(json.dumps({'files':len(records),'parts':sum(len(r['parts']) for r in records),'all_byte_identical':True}))
