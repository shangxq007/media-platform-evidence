"""Supported FE mount/PID isolation; backend gates remain host-native."""
from pathlib import Path
import os,subprocess,hashlib,json
D=Path(__file__).resolve().parents[1]
O=D.parent
H=D/'executor'
BASE='86d6aef94fd5e58da552e97c11473cff6eca734e'
SHA='689ab9456461a8d19a72d059f5157092efc43aff';TREE='6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6'
def git(root,*args):
 return subprocess.check_output(['git','--no-optional-locks','-C',str(root),*args],env={**{k:v for k,v in os.environ.items() if not k.startswith('GIT_')},'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'})
def exact(root,sha=SHA,tree=TREE):
 if git(root,'rev-parse','HEAD').decode().strip()!=sha or git(root,'rev-parse','HEAD^{tree}').decode().strip()!=tree:raise RuntimeError('CANDIDATE_IDENTITY_MISMATCH')
 if git(root,'rev-parse','HEAD^').decode().strip()!=BASE:raise RuntimeError('CANDIDATE_BASE_MISMATCH')
 paths=[]
 for row in git(root,'ls-tree','-rz',sha).split(b'\0'):
  if not row:continue
  meta,name=row.split(b'\t',1);mode,kind,blob=meta.decode().split();p=Path(root)/os.fsdecode(name)
  from preservation import parent_fd
  with parent_fd(p) as (fd,leaf):
   if p.is_symlink():raise RuntimeError('SYMLINK_TRACKED_INPUT')
   f=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
   try:
    with os.fdopen(f,'rb',closefd=False) as stream:b=stream.read()
   finally:os.close(f)
  m='120000' if p.is_symlink() else '100755' if p.stat().st_mode&0o111 else '100644'
  if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=blob or m!=mode:raise RuntimeError('TRACKED_INPUT_MISMATCH '+os.fsdecode(name))
  paths.append(p)
 expected_index=b''.join(row.split(b'\t',1)[0].split()[0]+b' '+row.split(b'\t',1)[0].split()[2]+b' 0\t'+row.split(b'\t',1)[1]+b'\0' for row in git(root,'ls-tree','-rz',sha).split(b'\0') if row)
 if git(root,'ls-files','--stage','-z')!=expected_index:raise RuntimeError('STAGED_INPUT_MISMATCH')
 if (Path(root)/'.git/objects/info/alternates').exists():raise RuntimeError('ALTERNATE_OBJECT_DATABASE')
 return paths

def environment(lane,run=None):
 base=Path(run)/'runtime' if run else D
 cache=base/'cache'/lane;tmp=base/'tmp'/lane
 values={k:os.environ[k] for k in ['PATH','LANG','LC_ALL','USER','LOGNAME','SHELL','JAVA_HOME','LD_LIBRARY_PATH','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy','XDG_RUNTIME_DIR'] if k in os.environ}
 values.update(HOME=str(cache/'home'),XDG_CACHE_HOME=str(cache/'xdg'),TMPDIR=str(tmp),TMP=str(tmp),TEMP=str(tmp),GRADLE_USER_HOME=str(cache/'gradle'),npm_config_cache=str(cache/'npm'),PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',H7_SOURCE_TREE=TREE,JAVA_TOOL_OPTIONS='-Djava.io.tmpdir='+str(tmp),DOCKER_HOST='unix:///run/user/1000/podman/podman.sock',CONTAINER_HOST='unix:///run/user/1000/podman/podman.sock')
 for p in [cache/'home',cache/'xdg',cache/'gradle',cache/'npm',tmp]:p.mkdir(parents=True,exist_ok=True)
 if run:
  runtime=cache/'xdg-runtime'
  if runtime.resolve()!=runtime:raise RuntimeError('XDG_RUNTIME_NAMESPACE_SYMLINK')
  runtime.mkdir(parents=True,mode=0o700,exist_ok=True)
  if runtime.stat().st_uid!=os.getuid() or runtime.stat().st_mode&0o777!=0o700:
   raise RuntimeError('XDG_RUNTIME_OWNER_OR_MODE')
  values['XDG_RUNTIME_DIR']=str(runtime)
 return values

def frontend_sandbox(argv,cwd,writable,run=None):
 from isolation import validate_output
 result=['bwrap','--die-with-parent','--unshare-pid','--ro-bind','/','/']
 for p in map(Path,writable):
  if not p.is_absolute() or p.resolve()!=p or not p.is_relative_to(D):raise RuntimeError('INVALID_WRITABLE_NAMESPACE')
  namespaces=([Path(run)/'sources/frontend/frontend/node_modules',Path(run)/'runtime/cache/frontend',Path(run)/'runtime/tmp/frontend',Path(run)/'runtime/outputs/frontend',Path(run)/'runtime/outputs/frontend-evidence',Path(run)/'runtime/gates'] if run else [])+[D/'owner-clarified-execution-20260907T1120Z/fixtures',D/'fixtures',D/'qualification',D/'cache/frontend',D/'tmp/frontend',D/'outputs/frontend',D/'outputs/frontend-evidence',D/'outputs/qualification',D/'sources/frontend/frontend/node_modules']
  if not any(p==base or p.is_relative_to(base) for base in namespaces):raise RuntimeError('CROSS_LANE_WRITE_NAMESPACE')
  result+=['--bind',str(p),str(p)]
 return result+['--proc','/proc','--dev','/dev','--chdir',str(cwd),*argv]

def require_evidence(receipt,evidence,sha=SHA,tree=TREE):
 if not receipt or receipt.get('candidate')!=sha or receipt.get('tree')!=tree:raise RuntimeError('MISSING_OR_MISMATCHED_GATE_IDENTITY')
 if receipt.get('native_exit')!=0 or receipt.get('wrapper_exit')!=0 or receipt.get('result')!='PASS':raise RuntimeError('GATE_NOT_PASS')
 if not evidence or any(not Path(p).is_file() for p in evidence):raise RuntimeError('MISSING_REQUIRED_EVIDENCE')

def required_complete(required,results):
 if set(results)!=set(required):raise RuntimeError('MISSING_OR_UNEXPECTED_GATE_EXECUTION')
 for name in required:require_evidence(results[name],results[name].get('required_evidence',[]))
 return True


def formal_sandbox(argv,cwd,run,env):
 """Exact FORMAL mount invocation, shared by the runner and bounded probes."""
 run=Path(run);tmp=Path(env['TMPDIR'])
 if run.resolve()!=run or tmp.resolve()!=tmp or not tmp.is_relative_to(run/'runtime'):
  raise RuntimeError('FORMAL_OUTPUT_NAMESPACE')
 return ['bwrap','--die-with-parent','--unshare-pid','--ro-bind','/','/',
         '--bind',str(run/'runtime'),str(run/'runtime'),'--bind',str(tmp),'/tmp',
         '--proc','/proc','--dev','/dev','--chdir',str(cwd),*argv]
