"""Pure owner-local authorization and lifecycle state; no platform grants."""
import copy
import hmac
import json
import threading
import time
from urllib.parse import urlencode
from model import Config, Failure, PENDING, identifier, ensure_redacted, _safe_header_credential
from wire import strict_json, MAX_HEADERS

from runtime_handle import LOCAL_HOST, require_handle
CONTRACT = 'owner-local-external-observations-v4'

def identity(config):
    return {'binding':copy.deepcopy(config.binding), 'provider':config.provider, 'instance':config.instance_id,
            'account':config.external_account_id, 'startInclusive':config.start_inclusive, 'endExclusive':config.end_exclusive}

def snapshot_target(config, request_id):
    return '/observations/snapshot?' + urlencode({'requestId':identifier(request_id), 'startInclusive':config.start_inclusive, 'endExclusive':config.end_exclusive})

def parse_config(raw):
    if type(raw) is not bytes or len(raw) > MAX_HEADERS:
        raise Failure("INVALID_CONFIGURATION", 403)
    return Config.from_mapping(strict_json(raw))

def load_config(path):
    try:
        with open(path, 'rb') as f:
            raw = f.read(MAX_HEADERS + 1)
        return parse_config(raw)
    except (OSError, ValueError, TypeError):
        raise Failure('INVALID_CONFIGURATION', 403) from None

class Authority:
    def __init__(self, config, token, upstream_key, revision, clock=time.monotonic):
        # Detach owner-supplied mutable mappings; configuration cannot change behind a receipt.
        self.config = Config.from_mapping(copy.deepcopy(config.__dict__))
        self.token = _safe_header_credential(token)
        self.upstream_key = _safe_header_credential(upstream_key)
        if self.token == self.upstream_key:
            raise Failure('INVALID_CREDENTIAL_CONFIGURATION',403)
        self.revision = identifier(revision)
        self.clock = clock
        self.expires = clock() + 1800
        self.retired = threading.Event()
        self.reads = 0
        self.bytes_read = 0
        self.published = 0
        self.lock = threading.Lock()
        self._handle = None
        ensure_redacted(self.receipt(), (token,upstream_key), self.config.max_bytes)

    def check(self):
        if self.retired.is_set() or self.clock() >= self.expires:
            raise Failure('ACCESS_RETIRED',403)

    def retire(self):
        self.retired.set()

    def receipt(self):
        self.check()
        return {'contract':CONTRACT, 'kind':'owner-local-access-receipt', 'identity':identity(self.config),
                'revision':self.revision, 'authority':'owner-local-single-user', 'coreContract':PENDING,
                'list':True, 'content':self.config.content_allowed, 'lifetimeSeconds':1800}

    def attach(self, handle):
        require_handle(handle)
        if self._handle is not None or handle.revision != self.revision:
            raise Failure('INVALID_RUNTIME_HANDLE',403)
        self._handle = handle

    def authorize(self, method, target, headers):
        if method != 'GET':
            raise Failure('METHOD_DENIED',405)
        if target != '/observations/access' and not target.startswith('/observations/snapshot?'):
            raise Failure('ROUTE_DENIED',404)
        allowed = {'host','authorization','x-observation-identity','x-observation-revision','accept','accept-encoding','connection','content-length'}
        if set(headers) - allowed:
            raise Failure('HEADER_DENIED',400)
        if headers.get('content-length','0') != '0':
            raise Failure('BODY_DENIED',400)
        if self._handle is None or headers.get('host') != self._handle.host_header:
            raise Failure('HOST_DENIED',403)
        value = headers.get('authorization','')
        if not value.isascii() or not hmac.compare_digest(value,self.token):
            raise Failure('LOCAL_AUTH_REQUIRED',401)
        self.check()
        try:
            supplied = strict_json(headers.get('x-observation-identity',''))
        except Failure:
            raise Failure('IDENTITY_DENIED',403) from None
        if supplied != identity(self.config):
            raise Failure('IDENTITY_DENIED',403)
        if target == '/observations/access':
            if 'x-observation-revision' in headers:
                raise Failure('QUERY_DENIED',403)
            return None
        if headers.get('x-observation-revision') != self.revision:
            raise Failure('ACCESS_RETIRED',403)
        # Canonical exact target rejects extra/duplicate/query URL/body control inputs.
        from urllib.parse import parse_qsl
        try:
            query = parse_qsl(target.split('?',1)[1], strict_parsing=True, max_num_fields=3)
            request_id = dict(query).get('requestId')
            identifier(request_id)
        except (ValueError, Failure):
            raise Failure('QUERY_DENIED',403) from None
        if target != snapshot_target(self.config,request_id):
            raise Failure('QUERY_DENIED',403)
        return request_id

    def reserve_snapshot(self):
        with self.lock:
            self.check()
            if self.reads + 2 > self.config.max_reads:
                raise Failure('READ_BUDGET_EXHAUSTED',429)
            # Reserve both requests before the first IO. Failed reads never refund or retry.
            self.reads += 2

    def publish(self, callback):
        with self.lock:
            self.check()
            callback()
            self.published += 1

def validate_snapshot(value, config, request_id):
    """Client-side closed projection validation; external references stay scoped."""
    from model import CONTRACT as SNAPSHOT_CONTRACT, PINNED_VERSION, PINNED_SOURCE_COMMIT, _instant
    required = {'contract','status','requestId','binding','access','providerVersion','providerSourceCommit','evidence','window','observedAt','completeness','omissions','externalAccount','observations'}
    if type(value) is not dict or set(value) != required:
        raise Failure('INVALID_LOCAL_SNAPSHOT',502)
    expected_access = {'authority':'owner-local-single-user','scope':'narrower-than-platform-effective-access','list':True,'content':config.content_allowed}
    expected_window = {'semantics':'half-open','startInclusive':config.start_inclusive,'endExclusive':config.end_exclusive,'upstreamEndInclusive':config.upstream_end_inclusive}
    if value['contract'] != SNAPSHOT_CONTRACT or value['status'] != 'ok' or value['requestId'] != request_id or value['binding'] != config.binding or value['access'] != expected_access or value['window'] != expected_window or value['providerVersion'] != PINNED_VERSION or value['providerSourceCommit'] != PINNED_SOURCE_COMMIT or value['evidence'] != ('synthetic-http-observation' if config.synthetic else 'authorized-instance-read'):
        raise Failure('INVALID_LOCAL_SNAPSHOT',502)
    if type(value['access']) is not dict or type(value['access'].get('list')) is not bool or type(value['access'].get('content')) is not bool:
        raise Failure('INVALID_LOCAL_SNAPSHOT',502)
    _instant(value['observedAt'])
    omissions = value['omissions']
    if type(omissions) is not dict or set(omissions) != {'recurrence','outsideWindow','recordCap'} or any(type(n) is not int or n < 0 for n in omissions.values()) or value['completeness'] != ('partial' if any(omissions.values()) else 'bounded'):
        raise Failure('INVALID_LOCAL_SNAPSHOT',502)
    refs = {'provider':config.provider,'instance':config.instance_id,'account':config.external_account_id}
    account = value['externalAccount']
    if type(account) is not dict or set(account) != {'externalReferences','label','providerLabel','coreBinding'} or account['externalReferences'] != refs or account['coreBinding'] != {'status':PENDING} or any(type(account[k]) is not str or not account[k] for k in ('label','providerLabel')):
        raise Failure('INVALID_LOCAL_SNAPSHOT',502)
    rows = value['observations']
    if type(rows) is not list or len(rows) > config.max_records:
        raise Failure('INVALID_LOCAL_SNAPSHOT',502)
    seen = set()
    for row in rows:
        base = {'kind','externalReferences','coreBinding','displayStatus','statusMapping','timeField','relationships'}
        if type(row) is not dict or not base <= set(row) or set(row)-base-{'scheduledAt','summary'}:
            raise Failure('INVALID_LOCAL_SNAPSHOT',502)
        external = row['externalReferences']
        if type(external) is not dict or set(external) != set(refs)|{'post'} or any(external[k] != v for k,v in refs.items()):
            raise Failure('INVALID_LOCAL_SNAPSHOT',502)
        post_id = identifier(external['post'])
        if post_id in seen:
            raise Failure('INVALID_LOCAL_SNAPSHOT',502)
        seen.add(post_id)
        status = row['displayStatus']
        expected_time = {'scheduled':'scheduledAt','draft':'unscheduled','published':'unknown','unknown':'unknown'}
        if row['kind'] != 'external-publication-observation' or row['coreBinding'] != {'status':PENDING} or type(status) is not str or status not in expected_time or row['statusMapping'] != ('unmapped' if status == 'unknown' else 'bounded-display-only') or row['timeField'] != expected_time[status] or row['relationships'] != {k:{'status':PENDING} for k in ('project','artifacts','attempts','externalOutcomes')}:
            raise Failure('INVALID_LOCAL_SNAPSHOT',502)
        if ('scheduledAt' in row) != (status == 'scheduled') or ('summary' in row) != config.content_allowed:
            raise Failure('INVALID_LOCAL_SNAPSHOT',502)
        if status == 'scheduled' and not _instant(config.start_inclusive) <= _instant(row['scheduledAt']) < _instant(config.end_exclusive):
            raise Failure('INVALID_LOCAL_SNAPSHOT',502)
        if 'summary' in row and (type(row['summary']) is not str or not 0 < len(row['summary']) <= 4000):
            raise Failure('INVALID_LOCAL_SNAPSHOT',502)
    return value
