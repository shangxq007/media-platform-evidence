"""Exclusive native process log and receipt. Does not retry or interpret success."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'executor'))
from sequence import durable

def main():
    if len(sys.argv)<4 or sys.argv[2]!='--':raise SystemExit('usage: run_logged.py LABEL -- COMMAND [ARG ...]')
    label=sys.argv[1]
    if not label.replace('-','').replace('_','').isalnum():raise RuntimeError('INVALID_LOG_LABEL')
    directory=ROOT/'parent-logs';directory.mkdir(exist_ok=True)
    log=directory/(label+'.native.log');start=time.time_ns();argv=sys.argv[3:]
    code=1;pid=None;exception=None
    try:
        with log.open('xb') as output:
            process=subprocess.Popen(argv,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT);pid=process.pid;code=process.wait()
            output.flush();os.fsync(output.fileno())
    except Exception as exc:
        exception={'type':type(exc).__name__,'reason':str(exc)}
        raise
    finally:
        result={'argv':argv,'pid':pid,'native_exit':code,'exception':exception,'started_ns':start,'finished_ns':time.time_ns(),
                'raw_log':str(log),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest() if log.is_file() else None}
        try:durable(directory/(label+'.process.json'),result)
        except Exception as exc:
            print('PROCESS_RECEIPT_WRITE_FAILED '+json.dumps({'process':result,'reason':str(exc)}),file=sys.stderr,flush=True)
            raise
        print(json.dumps(result),flush=True)
    return code
if __name__=='__main__':raise SystemExit(main())
