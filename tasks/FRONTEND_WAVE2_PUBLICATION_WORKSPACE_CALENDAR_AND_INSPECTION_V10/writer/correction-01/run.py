import sys,subprocess,datetime,json,pathlib
root=pathlib.Path(__file__).parent
name=sys.argv[1]; command=sys.argv[2:]; d=root/name; d.mkdir(exist_ok=False)
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (d/'output.log').open('w') as f:
 result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
(d/'command.json').write_text(json.dumps({'command':command,'cwd':str(pathlib.Path.cwd()),'start':start,'end':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':result.returncode},indent=2))
print(name, 'exit', result.returncode); print((d/'output.log').read_text()[-6500:])
sys.exit(result.returncode)
