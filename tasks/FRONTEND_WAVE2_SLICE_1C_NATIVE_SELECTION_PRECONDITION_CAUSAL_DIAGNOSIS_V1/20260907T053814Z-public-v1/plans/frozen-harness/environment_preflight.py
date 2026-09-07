"""External fail-closed environment wrapper; frozen scenarios remain untouched."""
import sys,json,hashlib,site,importlib,importlib.metadata,inspect,zipfile,ast,threading
from pathlib import Path

def qualify(c):
    assert sys.executable == c['interpreter'], 'WRONG_INTERPRETER'
    assert sys.prefix != sys.base_prefix, 'NOT_VENV'
    assert not site.ENABLE_USER_SITE, 'USER_SITE_ENABLED'
    assert all(str(Path(p)).startswith(sys.prefix) for p in sys.path if 'site-packages' in p), 'EXTERNAL_SITE'
    d=importlib.metadata.distribution('websockets')
    assert d.version == c['version'], 'VERSION_MISMATCH'
    wheel=Path(c['wheel'])
    assert hashlib.sha256(wheel.read_bytes()).hexdigest()==c['wheel_sha256'], 'WHEEL_HASH_MISMATCH'
    checked=0
    with zipfile.ZipFile(wheel) as z:
        for n in z.namelist():
            if n.endswith('/') or n.endswith('.dist-info/RECORD'): continue
            assert d.locate_file(n).read_bytes()==z.read(n), 'INSTALLED_BYTES_MISMATCH:'+n
            checked+=1
    for name,h in c['sources'].items():
        p=Path(__file__).parent/name
        assert p.is_file(), 'MISSING_SOURCE:'+name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==h, 'SOURCE_HASH_MISMATCH:'+name
        if p.suffix=='.py': compile(p.read_bytes(),str(p),'exec')
    client=importlib.import_module('websockets.sync.client')
    assert callable(getattr(client,c['connect_api'],None)), 'INCOMPATIBLE_SYNC_API'
    from websockets.sync.client import connect,ClientConnection
    assert 'timeout' in inspect.signature(ClientConnection.recv).parameters, 'RECV_TIMEOUT_API'
    for name in ['send','recv','close']: assert callable(getattr(ClientConnection,name,None)), name
    for name in ['scope_check','control','browser_helpers','chromium_helpers','native_common']: importlib.import_module(name)
    # Scenario modules have top-level browser side effects: compile them and import their complete dependencies, never run them in preflight.
    from websockets.sync.server import serve
    def echo(ws): ws.send(ws.recv(timeout=3))
    with serve(echo,'127.0.0.1',0) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with connect('ws://127.0.0.1:'+str(server.socket.getsockname()[1]),proxy=None) as ws:
                ws.send('bounded-api-qualification'); assert ws.recv(timeout=3)=='bounded-api-qualification'
        finally: server.shutdown();thread.join(timeout=3)
    return {'status':'PASS','executable':sys.executable,'python_version':sys.version,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'sys_path':sys.path,'websockets_version':d.version,'wheel_entries_verified':checked,'source_pins_verified':len(c['sources']),'sync_client_import':'PASS','api_exchange':'PASS','scenario_import_mode':'compiled; complete dependency closure imported without starting browser scenarios'}

if __name__=='__main__':
    try:
        result=qualify(json.loads(Path(sys.argv[1]).read_text()))
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({'status':'FAIL','error_type':type(e).__name__,'error':str(e)}));sys.exit(1)
