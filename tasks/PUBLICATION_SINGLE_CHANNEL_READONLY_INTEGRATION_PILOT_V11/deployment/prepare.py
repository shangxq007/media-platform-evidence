#!/usr/bin/env python3
"""Generate task-only hardened compose; never start services or expose secrets."""
import os, json, hashlib, secrets, shutil, socket, subprocess
from pathlib import Path
import yaml
D=Path(__file__).resolve().parent
R=D.parent/'research'
def save(name, data):
    (D/name).write_text(json.dumps(data,indent=2)+'\n')
identity=D/'identity.json'
assert not identity.exists(), 'Refuse to overwrite an existing deployment identity/secrets'
project='postiz-v11-empty-'+secrets.token_hex(5)
(D/'private').mkdir(mode=0o700)
os.chmod(D/'private',0o700)
(D/'dynamicconfig').mkdir()
pins=json.loads((R/'deployment-pin.json').read_text())
images=json.loads((R/'deployment-images.json').read_text())
assert images==pins['images']
manifest=json.loads((R/'source-manifest.json').read_text())
provenance=[]
for rel in [pins['official_compose'],*pins['dynamicconfig']]:
    raw=(R/rel).read_bytes()
    name=rel.removeprefix('sources/')
    expected=next(x for x in manifest if x['name']==name)
    digest=hashlib.sha256(raw).hexdigest()
    assert digest==expected['sha256']
    provenance.append({'path':rel,'sha256':digest,'url':expected['url']})
    if '/dynamicconfig/' in rel:
        (D/'dynamicconfig'/Path(rel).name).write_bytes(raw)
compose=yaml.safe_load((R/pins['official_compose']).read_text())
compose['name']=project
for im in images:
    raw=(R/'sources/registry'/f"{im['service']}.json").read_bytes()
    assert 'sha256:'+hashlib.sha256(raw).hexdigest()==im['registry_digest']==im['computed_digest']
    assert im['digest_verified']
    assert any(p['platform']=={'architecture':'amd64','os':'linux'} for p in im['platforms'])
    svc=compose['services'][im['service']]
    assert svc['image']==im['official_compose_reference']
    ref=im['candidate_immutable_reference']
    if not ref.startswith('ghcr.io/'):
        ref='docker.io/'+('library/' if '/' not in ref.split('@')[0] else '')+ref
    svc['image']=ref
    svc['platform']='linux/amd64'
    svc['container_name']=project+'-'+im['service']
    svc['restart']='no'
    svc['pull_policy']='missing'
    svc['security_opt']=['no-new-privileges:true']
    svc['cap_drop']=['NET_RAW','NET_ADMIN']
    svc['pids_limit']=512
    svc['mem_limit']='4g' if im['service']=='postiz' else '2g'
    svc['labels']={'audit.task':'PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11','audit.instance':project}
    env=svc.get('environment',{})
    if isinstance(env,list): env=dict(x.split('=',1) for x in env)
    svc['environment']={k:str(v).lower() if isinstance(v,bool) else str(v) for k,v in env.items()}
    svc.pop('ports',None)
ports={ 'postiz':45071, 'spotlight':45072, 'temporal-ui':45073 }
for svc,port in ports.items():
    with socket.socket() as s: s.bind(('127.0.0.1',port))
    target={'postiz':5000,'spotlight':8969,'temporal-ui':8080}[svc]
    compose['services'][svc]['ports']=[f'127.0.0.1:{port}:{target}']
for svc in ['spotlight','temporal-ui','temporal-admin-tools']:
    compose['services'][svc]['profiles']=['disabled-auxiliary']
app=compose['services']['postiz']['environment']
app.update(MAIN_URL='http://127.0.0.1:45071',FRONTEND_URL='http://127.0.0.1:45071',NEXT_PUBLIC_BACKEND_URL='http://127.0.0.1:45071/api',JWT_SECRET='${V11_JWT_SECRET:?private env required}',DATABASE_URL='postgresql://postiz-user:${V11_POSTGRES_PASSWORD:?private env required}@postiz-postgres:5432/postiz-db-local',DISABLE_REGISTRATION='true',RUN_CRON='false',MASTODON_URL='',NEXT_TELEMETRY_DISABLED='1',DO_NOT_TRACK='1')
compose['services']['postiz-postgres']['environment']['POSTGRES_PASSWORD']='${V11_POSTGRES_PASSWORD:?private env required}'
compose['services']['temporal-postgresql']['environment']['POSTGRES_PASSWORD']='${V11_TEMPORAL_PASSWORD:?private env required}'
compose['services']['temporal']['environment']['POSTGRES_PWD']='${V11_TEMPORAL_PASSWORD:?private env required}'
compose['services']['temporal']['volumes']=['./dynamicconfig:/etc/temporal/config/dynamicconfig:ro']
compose['services']['temporal-ui']['environment']['TEMPORAL_CORS_ORIGINS']='http://127.0.0.1:45073'
for kind in ['networks','volumes']:
    for key in compose[kind]:
        compose[kind][key]={'name':project+'-'+key,'external':False,'labels':{'audit.instance':project}}
        if kind=='networks': compose[kind][key].update(driver='bridge',internal=True)
secret_path=D/'private/local.env'
fd=os.open(secret_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'w') as f:
    for key in ['V11_JWT_SECRET','V11_POSTGRES_PASSWORD','V11_TEMPORAL_PASSWORD']:
        f.write(key+'='+secrets.token_hex(48)+'\n')
(D/'compose.yaml').write_text(yaml.safe_dump(compose,sort_keys=False))
save('identity.json',{'project':project,'app_release':pins['app_release'],'app_source_commit':pins['app_commit'],'compose_source_commit':pins['compose_commit'],'ports':ports,'containers':[s['container_name'] for s in compose['services'].values()],'volumes':[v['name'] for v in compose['volumes'].values()],'networks':[v['name'] for v in compose['networks'].values()],'secret_file':str(secret_path),'secret_mode':oct(secret_path.stat().st_mode & 0o777),'status':'PREPARED_NOT_STARTED'})
save('source-and-image-validation.json',{'result':'PASS','source_files':provenance,'images':[{'service':i['service'],'reference':compose['services'][i['service']]['image'],'registry_manifest_sha256':i['computed_digest']} for i in images],'qualification':pins['qualification']})
print(json.dumps({'project':project,'source_hashes_verified':len(provenance),'image_manifest_hashes_verified':len(images),'secrets_mode':'0600','secrets_printed':False}))
