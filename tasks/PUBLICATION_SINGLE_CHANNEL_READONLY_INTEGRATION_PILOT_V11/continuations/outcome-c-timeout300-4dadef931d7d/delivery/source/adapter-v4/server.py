"""Owner-configured loopback-only read server; never launched by offline gates."""
import select
import socket
import ssl
import threading
from datetime import datetime, timezone
from boundary import Authority, CONTRACT
from runtime_handle import _bound_handle
from model import Failure, PENDING, PostizProjector, ensure_redacted
from transport import Operation, read_head, send, upstream
from wire import MAX_HEADERS, parse_head, encode_response, build_request

def error_payload(error):
    return {'status':'restricted' if error.status in (401,403) else 'error', 'errorClass':error.code,
            'message':'The bounded read could not be completed.'}

class Server:
    def __init__(self, authority):
        self.authority = authority
        self.stop = threading.Event()
        self.ready = threading.Event()
        self.start_error = None
        self.active = 0
        self.handle = None
        # Certificate setup belongs to startup, before bounded requests.
        self.tls = ssl.create_default_context() if authority.config.endpoint[0] == 'https' else None

    def close(self):
        self.authority.retire()
        self.stop.set()

    def serve(self):
        listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            listener.bind(('127.0.0.1',0))
            self.handle = _bound_handle(listener.getsockname(),self.authority.revision)
            self.authority.attach(self.handle)
            listener.listen(4)
            listener.setblocking(False)
            self.ready.set()
            while not self.stop.is_set():
                if not select.select([listener],[],[],0.02)[0]:
                    continue
                connection,_ = listener.accept()
                connection.setblocking(False)
                self.active += 1
                try:
                    self.handle_request(connection)
                finally:
                    connection.close()
                    self.active -= 1
        except OSError:
            self.start_error = 'LOCAL_LISTENER_UNAVAILABLE'
            self.ready.set()
        finally:
            listener.close()

    def handle_request(self, caller):
        a = self.authority
        c = a.config
        op = Operation(c.timeout_seconds, 2*(c.max_bytes+MAX_HEADERS+1)+MAX_HEADERS)
        authorized = False
        def watch():
            a.check()
            if self.stop.is_set():
                raise Failure('ACCESS_RETIRED',403)
            if select.select([caller],[],[],0)[0]:
                data = caller.recv(1,socket.MSG_PEEK)
                raise Failure('BODY_DENIED',400) if data else Failure('CALLER_CANCELLED',499)
        def error_watch():
            if authorized:
                a.check()
                if self.stop.is_set():
                    raise Failure('ACCESS_RETIRED',403)
                if select.select([caller],[],[],0)[0] and not caller.recv(1,socket.MSG_PEEK):
                    raise Failure('CALLER_CANCELLED',499)
        try:
            method_target,headers = parse_head(read_head(caller,op))
            request_id = a.authorize(*method_target,headers)
            authorized = True
            op.cancel = watch
            op.check()
            if request_id is None:
                payload = a.receipt()
            else:
                # Both exact destinations/headers validated before any upstream acquisition.
                build_request(c,'integrations',a.upstream_key)
                build_request(c,'posts',a.upstream_key)
                a.reserve_snapshot()
                accounts = upstream(c,'integrations',a.upstream_key,op,self.tls)
                # Fail before consuming posts on a missing/ambiguous/disabled account.
                projector = PostizProjector(c,a.token,a.upstream_key)
                now = lambda: datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
                projector.project(accounts,{'posts':[]},request_id,now())
                posts = upstream(c,'posts',a.upstream_key,op,self.tls)
                op.check()
                snapshot = projector.project(accounts,posts,request_id,now())
                snapshot['evidence'] = 'synthetic-http-observation' if c.synthetic else 'authorized-instance-read'
                payload = {'contract':CONTRACT,'kind':'owner-local-snapshot-envelope','coreContract':PENDING,
                           'receipt':a.receipt(),'requestId':request_id,'snapshot':snapshot}
            ensure_redacted(payload,(a.token,a.upstream_key),c.max_bytes)
            data = encode_response(200,payload)
            op.check()
            # Every send checks retirement, expiry, disconnect, extra request bytes
            # and the original operation deadline; already-sent bytes cannot be recalled.
            a.publish(lambda: send(caller,data,op))
        except Failure as error:
            if error.code in ('CALLER_CANCELLED','DEADLINE_EXCEEDED') or authorized and error.code == 'ACCESS_RETIRED':
                # Do not start a new error-response deadline or publish a late result.
                return
            try:
                op.cancel = error_watch
                send(caller,encode_response(error.status,error_payload(error)),op)
            except (Failure,OSError):
                pass
        except (OSError,ValueError,TypeError,RecursionError):
            try:
                op.cancel = error_watch
                send(caller,encode_response(502,error_payload(Failure('TRANSPORT_FAILURE',502))),op)
            except (Failure,OSError):
                pass
        finally:
            a.bytes_read += op.volume

