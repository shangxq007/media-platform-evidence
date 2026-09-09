"""Socket-free client input validation, immutable owner config and generations."""
import copy
import json
import threading
from dataclasses import dataclass
from boundary import CONTRACT, identity, snapshot_target, validate_snapshot
from model import Config, Failure, PENDING, identifier, _safe_header_credential, ensure_redacted
from runtime_handle import require_handle
from wire import MAX_HEADERS

@dataclass(frozen=True)
class OwnerConfig:
    encoded: str

    @classmethod
    def capture(cls, config):
        if type(config) is not Config:
            raise Failure('INVALID_CONFIGURATION',403)
        detached = Config.from_mapping(copy.deepcopy(config.__dict__))
        return cls(json.dumps(detached.__dict__,sort_keys=True,separators=(',',':')))

    def view(self):
        # Config itself is frozen; its nested mappings are disposable copies.
        return Config.from_mapping(json.loads(self.encoded))

@dataclass(frozen=True)
class ReadGeneration:
    owner: object
    number: int
    request_id: str

class ClientState:
    def __init__(self, config, token, handle):
        self._owner_config = OwnerConfig.capture(config)
        self.token = _safe_header_credential(token)
        self.handle = require_handle(handle)
        self.lock = threading.RLock()
        self._owner = object()
        self._generation = 0
        self._retired = False
        self._snapshot = None

    @property
    def config(self):
        return self._owner_config.view()

    @property
    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self._snapshot)

    def begin(self, request_id):
        # Validate complete read intent before even constructing an IO operation.
        identifier(request_id)
        snapshot_target(self.config,request_id)
        with self.lock:
            if self._retired:
                raise Failure('CLIENT_RETIRED',403)
            self._generation += 1
            generation = ReadGeneration(self._owner,self._generation,request_id)
            # Both HTTP requests are validated before access acquisition.
            self.prepare('GET','/observations/access',generation)
            self.prepare('GET',snapshot_target(self.config,request_id),generation,self.handle.revision)
            return generation

    def check(self, generation):
        with self.lock:
            if self._retired:
                raise Failure('CLIENT_RETIRED',403)
            if type(generation) is not ReadGeneration or generation.owner is not self._owner or type(generation.number) is not int or generation.number != self._generation:
                raise Failure('READ_SUPERSEDED',409)
            identifier(generation.request_id)

    def retire(self):
        with self.lock:
            self._retired = True
            self._generation += 1
            self._snapshot = None

    def prepare(self, method, target, generation, revision=None):
        self.check(generation)
        if method != 'GET':
            raise Failure('METHOD_DENIED',405)
        if type(target) is not str:
            raise Failure('ROUTE_DENIED',404)
        if target == '/observations/access':
            if revision is not None:
                raise Failure('QUERY_DENIED',403)
        elif target == snapshot_target(self.config,generation.request_id):
            identifier(revision)
            if revision != self.handle.revision:
                raise Failure('ACCESS_RETIRED',403)
        else:
            raise Failure('ROUTE_DENIED',404)
        head = (f'GET {target} HTTP/1.1\r\nHost: {self.handle.host_header}\r\nAuthorization: {self.token}\r\n'
                'X-Observation-Identity: '+json.dumps(identity(self.config),separators=(',',':'))+'\r\n')
        if revision is not None:
            head += 'X-Observation-Revision: '+revision+'\r\n'
        data = (head+'Connection: close\r\n\r\n').encode('ascii')
        if len(data) > MAX_HEADERS:
            raise Failure('HEADERS_TOO_LARGE',431)
        self.check(generation)
        return data

    def publish(self, generation, value, deadline_check):
        # The generation check and assignment are atomic with begin/retire.
        with self.lock:
            self.check(generation)
            detached = copy.deepcopy(value)
            deadline_check()
            self.check(generation)
            self._snapshot = detached


def validate_receipt(receipt, config, handle):
    require_handle(handle)
    expected = {'contract':CONTRACT,'kind':'owner-local-access-receipt','identity':identity(config),
                'revision':handle.revision,'authority':'owner-local-single-user','coreContract':PENDING,
                'list':True,'content':config.content_allowed,'lifetimeSeconds':1800}
    if type(receipt) is not dict or receipt != expected:
        raise Failure('INVALID_LOCAL_RECEIPT',502)
    if type(receipt['list']) is not bool or type(receipt['content']) is not bool or type(receipt['lifetimeSeconds']) is not int:
        raise Failure('INVALID_LOCAL_RECEIPT',502)
    identifier(receipt['revision'])
    return copy.deepcopy(receipt)


def validate_envelope(value, receipt, config, handle, request_id, token):
    validate_receipt(receipt,config,handle)
    if type(value) is not dict or set(value) != {'contract','kind','coreContract','receipt','requestId','snapshot'} or value['contract'] != CONTRACT or value['kind'] != 'owner-local-snapshot-envelope' or value['coreContract'] != PENDING or value['receipt'] != receipt or value['requestId'] != request_id:
        raise Failure('INVALID_LOCAL_ENVELOPE',502)
    # Echoed receipt also needs exact types: Python True == 1 is insufficient.
    validate_receipt(value['receipt'],config,handle)
    validate_snapshot(value['snapshot'],config,request_id)
    ensure_redacted(value,(token,),config.max_bytes)
    return value
