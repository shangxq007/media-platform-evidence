from pathlib import Path
import os,sys,json,csv,hashlib as H,subprocess as S,shutil,time
A=Path(__file__).resolve().parent
R=Path('USER_HOME/Documents/workspace/projects/media-platform');X=R
SHA='86d6aef94fd5e58da552e97c11473cff6eca734e';T='dba5e1e457af28cfca865e44f48eedabcc28aebb';B='2321ab36308a95e5ccb2faf99eefdf5765654a89';REF='refs/heads/candidate/ep19-entitlement-query-authority-86d6aef94fd5'
GH=Path('USER_HOME/Documents/workspace/tmp/ep19-publication-gradle-home');TMP=Path('USER_HOME/Documents/workspace/tmp/ep19-publication-tmp');SHADOW=None
ENV=dict(os.environ);ENV.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',GRADLE_USER_HOME=str(GH),TMPDIR=str(TMP));ENV['JAVA_TOOL_OPTIONS']=os.environ.get('JAVA_TOOL_OPTIONS','')+' -Djava.io.tmpdir='+str(TMP)
for key in ['EP19_GIT_TOKEN','GITHUB_TOKEN','GH_TOKEN','BWS_ACCESS_TOKEN']:ENV.pop(key,None)
def h(p):return H.sha256(Path(p).read_bytes()).hexdigest()
def g(*args,cwd=R):return S.check_output(['git','-C',str(cwd),*args],env=ENV)
def j(n,o):(A/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def load(n):return json.loads((A/n).read_text())
def record(cid,argv,kind='HELPER'):
 with (A/'SANITY_COMMAND_LOG.jsonl').open('a') as f:f.write(json.dumps({'command_id':cid,'command':argv,'kind':kind,'epoch':time.time()})+'\n')
def completed(cid,result='PASS'):
 with (A/'SANITY_COMPLETIONS.jsonl').open('a') as f:f.write(json.dumps({'command_id':cid,'result':result,'epoch':time.time()})+'\n')
def checked_manifest(root,n):
 rows=[]
 for item in g('ls-tree','-rz',SHA,cwd=root).split(b'\0'):
  if not item:continue
  meta,name=item.split(b'\t');mode,kind,blob=meta.decode().split();p=root/os.fsdecode(name);b=os.readlink(p).encode() if p.is_symlink() else p.read_bytes() if p.is_file() else b''
  actual=H.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();actual_mode='120000' if p.is_symlink() else '100755' if p.exists() and p.stat().st_mode&0o111 else '100644'
  rows.append({'path':os.fsdecode(name),'git_blob_sha':blob,'filesystem_sha256':H.sha256(b).hexdigest(),'mode':actual_mode,'matches_git_blob':actual==blob and mode==actual_mode})
 with (A/n).open('w') as f:
  w=csv.DictWriter(f,list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
 return rows
