"""Task-local client; destination comes only from the owner runtime handle."""
from boundary import snapshot_target
from client_state import ClientState, validate_receipt, validate_envelope
from model import Failure
from runtime_handle import LOCAL_HOST
from transport import Operation, connect, read_response, send
from wire import MAX_HEADERS, parse_response

class Client:
    def __init__(self, config, token, handle):
        self._state = ClientState(config,token,handle)

    @property
    def config(self):
        return self._state.config

    @property
    def snapshot(self):
        return self._state.snapshot

    def retire(self):
        self._state.retire()

    def request(self, method, target, op, generation, revision=None):
        # Pure default-deny validation precedes every socket acquisition.
        data = self._state.prepare(method,target,generation,revision)
        op.check()
        sock = None
        try:
            sock = connect(LOCAL_HOST,self._state.handle.port,op)
            send(sock,data,op)
            status,headers,body = read_response(sock,op,self.config.max_bytes)
            op.check()
            if status != 200:
                raise Failure('LOCAL_READ_DENIED',403 if status in (401,403) else 429 if status == 429 else 502)
            value = parse_response(status,headers,body,self.config.max_bytes)
            op.check()
            return value
        except (OSError,ValueError):
            op.check()
            raise Failure('LOCAL_TRANSPORT',502) from None
        finally:
            if sock is not None:
                sock.close()

    def read(self, request_id):
        state = self._state
        generation = state.begin(request_id)
        config = state.config
        op = Operation(config.timeout_seconds,2*(config.max_bytes+MAX_HEADERS+1),lambda:state.check(generation))
        receipt = validate_receipt(self.request('GET','/observations/access',op,generation),config,state.handle)
        op.check()
        value = self.request('GET',snapshot_target(config,request_id),op,generation,receipt['revision'])
        validate_envelope(value,receipt,config,state.handle,request_id,state.token)
        state.publish(generation,value,op.check)
        return value
