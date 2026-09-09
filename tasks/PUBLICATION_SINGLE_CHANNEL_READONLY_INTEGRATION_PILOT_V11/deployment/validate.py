#!/usr/bin/env python3
"""Real config validation, redacted evidence, engine prerequisite probe."""
import subprocess,os,json,hashlib,stat,shutil,socket
from pathlib import Path
import yaml
D=Path(__file__).resolve().parent
os.chdir(D)
os.chmod(D/'podman-isolated',0o755)
I=json.loads((D/'identity.json').read_text())
env=os.environ.copy()
env.update(PYTHONPATH=str(D/'tools'),PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(D/'private/tmp'))
(D/'private/tmp').mkdir(mode=0o700,exist_ok=True)
# Disallow ambient compose/project/interpolation overrides.
for k in list(env):
    if k.startswith(('COMPOSE_','V11_')): env.pop(k)
base=['python3','-m','podman_compose','--podman-path',str(D/'podman-isolated'),'--env-file',str(D/'private/local.env'),'-p',I['project'],'-f',str(D/'compose.yaml')]
p=subprocess.run(base+['config'],env=env,text=True,capture_output=True,timeout=60)
# Rendered config contains throwaway secrets: never print or store publicly.
values=[l.split('=',1)[1] for l in (D/'private/local.env').read_text().splitlines()]
redact=lambda t: __import__('functools').reduce(lambda a,v:a.replace(v,'[REDACTED]'),values,t)
result={'compose_config_exit':p.returncode,'compose_config_stderr':redact(p.stderr),'provider':'podman-compose 1.5.0','local_tool_dependencies':{'PyYAML':'6.0.3','python-dotenv':'1.2.3'},'checks':[]}
if p.returncode==0:
    c=yaml.safe_load(p.stdout)
    assert c['name']==I['project']
    for key,s in c['services'].items():
        assert '@sha256:' in s['image']
        assert s['container_name']==I['project']+'-'+key
        assert not s.get('privileged') and not s.get('network_mode')
        assert set(s['networks'])<=set(c['networks'])
        for port in s.get('ports',[]):
            assert str(port).startswith('127.0.0.1:')
        for volume in s.get('volumes',[]):
            assert volume.split(':')[0] in c['volumes'] or ('dynamicconfig' in volume and volume.endswith(':ro'))
        assert set(s.get('depends_on',{}))<=set(c['services'])
    assert all(n['internal'] and not n['external'] for n in c['networks'].values())
    assert all(v['name'].startswith(I['project']+'-') and not v['external'] for v in c['volumes'].values())
    assert c['services']['postiz']['environment']['DISABLE_REGISTRATION']=='true'
    assert c['services']['postiz']['environment']['RUN_CRON']=='false'
    assert stat.S_IMODE((D/'private/local.env').stat().st_mode)==0o600
    assert stat.S_IMODE((D/'private').stat().st_mode)==0o700
    result['checks']=['digest pins','unique project resource names','loopback-only published ports','no host networking/privilege','internal-only networks','fresh nonexternal volumes','dependency references','readonly task dynamicconfig bind','registration disabled','cron disabled','secret mode 0600 and parent 0700']
    (D/'compose.config.redacted.yaml').write_text(redact(p.stdout))
(D/'compose-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert p.returncode==0
records=[]
for args in [['info','--format','{{.Host.Security.Rootless}} {{.Host.NetworkBackend}} {{.Store.GraphRoot}}'],['ps','-a','--format','{{.Names}}'],['volume','ls','--format','{{.Name}}'],['network','ls','--format','{{.Name}}']]:
    q=subprocess.run([str(D/'podman-isolated'),*args],text=True,capture_output=True,timeout=60)
    records.append({'args':args,'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr})
    if q.returncode: break
(D/'engine-preflight.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
