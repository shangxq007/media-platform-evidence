"""Independent parent receipt for the integrated fixture-only qualifier."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def manifest(root):
    return {str(path.absolute()): digest(path) for path in sorted(Path(root).rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts}
def exclusive(path, value, raw=False):
    body=value if raw else (json.dumps(value,indent=2,sort_keys=True)+"\n").encode()
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
    try:
        view=memoryview(body)
        while view:
            count=os.write(fd,view)
            if count<=0:raise OSError("ZERO_PARENT_RECEIPT_WRITE")
            view=view[count:]
        os.fsync(fd)
    finally:os.close(fd)
def snapshot(root,destination):
    root=Path(root).absolute();destination=Path(destination);destination.mkdir(mode=0o700)
    rows={}
    for source in sorted(root.rglob('*')):
        if not source.is_file() or '__pycache__' in source.parts:continue
        target=destination/source.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        exclusive(target,source.read_bytes(),True)
        rows[str(source)]={'source_sha256':digest(source),'snapshot':str(target.absolute()),
                           'snapshot_sha256':digest(target)}
    exclusive(destination/'SOURCE_SNAPSHOT.json',{'schema':'ep19-r9-immutable-source-snapshot-v1','files':rows})
    return rows
def main():
    p=argparse.ArgumentParser();p.add_argument("--tooling",type=Path,required=True)
    p.add_argument("--fixture-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--dependency-binding",type=Path,required=True)
    a=p.parse_args();tooling=a.tooling.absolute();output=a.output.absolute();output.mkdir(parents=True,mode=0o700)
    before=manifest(tooling);snapshot_before=snapshot(tooling,output/'sources.before')
    argv=[sys.executable,"-B",str(tooling/"qualification/build_integration_qualification.py"),
        "--output",str(output/"integrated"),"--fixture-root",str(a.fixture_root.absolute())]
    dependency=a.dependency_binding.absolute()
    env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1",
         "EP19_TEST_DEPENDENCY_BINDING":str(dependency.absolute())};started_wall=time.time_ns();started_mono=time.monotonic_ns()
    launch_cwd=tooling.parents[1]
    child=subprocess.Popen(argv,cwd=launch_cwd,env=env,stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,start_new_session=True)
    pid=child.pid;parent_pid_namespace=os.readlink('/proc/self/ns/pid')
    child_pid_namespace=os.readlink(f'/proc/{pid}/ns/pid')
    stdout,_=child.communicate(timeout=300);finished_mono=time.monotonic_ns();finished_wall=time.time_ns()
    after=manifest(tooling);snapshot_after=snapshot(tooling,output/'sources.after')
    copied_before={path:row['snapshot_sha256'] for path,row in snapshot_before.items()}
    copied_after={path:row['snapshot_sha256'] for path,row in snapshot_after.items()}
    stable=before==after==copied_before==copied_after;exclusive(output/"PARENT.native.log",stdout,True)
    receipt={"schema":"ep19-r9-integrated-parent-process-v1","argv":argv,
        "cwd":str(launch_cwd.absolute()),"pid":pid,"native_exit":child.returncode,
        "wrapper_exit":0 if stable else 125,"started_wall_ns":started_wall,"finished_wall_ns":finished_wall,
        "native_status":"PASS" if child.returncode==0 else "FAIL",
        "wrapper_status":"PASS" if stable else "FAIL",
        "parent_pid_namespace":parent_pid_namespace,"child_pid_namespace":child_pid_namespace,
        "started_monotonic_ns":started_mono,"finished_monotonic_ns":finished_mono,
        "duration_seconds":(finished_mono-started_mono)/1e9,"source_binding_before":before,
        "source_binding_after":after,"source_binding_stable":stable,
        "source_snapshot_before":snapshot_before,"source_snapshot_after":snapshot_after,
        "source_snapshot_stable":stable,
        "dependency_binding":str(dependency.absolute()),"dependency_sha256":digest(dependency),
        "raw_log":str((output/"PARENT.native.log").absolute()),
        "raw_log_sha256":digest(output/"PARENT.native.log"),"formal_attempt":False,
        "product_tests":False,"shared_preparation":False,"shared_probes":False,"shared_baseline":False}
    integrated=output/"integrated/RESULT.json"
    if integrated.is_file():receipt.update(result_receipt=str(integrated),result_sha256=digest(integrated))
    exclusive(output/"PARENT_PROCESS.json",receipt);sys.stdout.buffer.write(stdout)
    return child.returncode if stable else 125
if __name__=="__main__":raise SystemExit(main())
