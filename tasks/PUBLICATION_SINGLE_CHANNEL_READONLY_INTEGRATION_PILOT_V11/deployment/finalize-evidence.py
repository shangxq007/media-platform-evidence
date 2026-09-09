#!/usr/bin/env python3
"""Read back scoped engine state and write nonsecret final evidence."""
import json,subprocess,hashlib,socket,os,stat
from pathlib import Path
import yaml
D=Path(__file__).resolve().parent
I=json.loads((D/'identity.json').read_text())
records=[]
for args in [['ps','-a','--format','{{.Names}} {{.Status}} {{.Ports}}'],['volume','ls','--format','{{.Name}}'],['network','ls','--format','{{.Name}}'],['images','--format','{{.ID}} {{.Repository}} {{.Digest}}'],['image','exists',yaml.safe_load((D/'compose.yaml').read_text())['services']['postiz']['image']]]:
    p=subprocess.run([str(D/'podman-isolated'),*args],text=True,capture_output=True,timeout=60)
    records.append({'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
listeners=subprocess.run(['ss','-H','-ltn'],text=True,capture_output=True,timeout=30)
ports={str(port):[line for line in listeners.stdout.splitlines() if line.split()[3].rsplit(':',1)[-1]==str(port)] for port in I['ports'].values()}
processes=[]
# Command-line scope only; no environ or unrelated command lines retained.
for entry in Path('/proc').iterdir():
    if not entry.name.isdigit(): continue
    try:
        cmd=(entry/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        if str(D) in cmd and ('/usr/bin/podman ' in cmd or 'conmon ' in cmd):
            processes.append({'pid':int(entry.name),'command':cmd})
    except (OSError,PermissionError): pass
result={'status':'PREPARED_ONLY_IMAGE_PULL_BLOCKED','LOCAL_EMPTY_INSTANCE_CHECK':'NOT_RUN_NO_POSTIZ_INSTANCE','engine_inventory':records,'port_readback':ports,'scoped_engine_processes':processes,'postiz_containers_started':False,'auth':'NO_CREDENTIALS_NO_ACCOUNTS_CREATED','public_api_calls':0,'db_reads':0,'oauth_or_connect_calls':0,'public_social_sends':0,'retained':'task-private engine image cache, generated throwaway secrets, tooling and configuration; preflight network removed and route container --rm cleaned'}
(D/'final-runtime-state.json').write_text(json.dumps(result,indent=2)+'\n')
# No secret hashes are published; only file paths and mode.
public=[]
secret_values=[x.split('=',1)[1] for x in (D/'private/local.env').read_text().splitlines()]
for f in sorted(D.rglob('*')):
    rel=f.relative_to(D)
    if any(x in {'private','tools','pip-cache','__pycache__'} for x in rel.parts) or not f.is_file() or f.name=='public-artifact-manifest.json': continue
    raw=f.read_bytes()
    assert not any(v.encode() in raw for v in secret_values),str(rel)
    public.append({'path':str(f),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
(D/'public-artifact-manifest.json').write_text(json.dumps({'files':public,'secrets_excluded':True,'secret_paths_and_modes':[{'path':str(D/'private/local.env'),'mode':oct(stat.S_IMODE((D/'private/local.env').stat().st_mode))} ]},indent=2)+'\n')
print(json.dumps(result,indent=2))
print('Public nonsecret artifacts hashed:',len(public))
