"""Socket-free HTTP grammar, fixed request builders and strict JSON boundary."""
import json
import re
from urllib.parse import urlencode
from model import Failure, _safe_header_credential

MAX_HEADERS = 16384
TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")

def strict_json(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise Failure('INVALID_JSON')
            result[k] = v
        return result
    def constant(_):
        raise Failure('INVALID_JSON')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError):
        raise Failure('INVALID_JSON') from None

def parse_head(raw, response=False):
    if type(raw) is not bytes or len(raw) > MAX_HEADERS:
        raise Failure('HEADERS_TOO_LARGE', 431)
    if not raw.endswith(b'\r\n\r\n'):
        raise Failure('INVALID_HTTP', 400)
    try:
        lines = raw[:-4].decode('ascii').split('\r\n')
    except UnicodeError:
        raise Failure('INVALID_HTTP', 400) from None
    if response:
        if not re.fullmatch(r'HTTP/1\.[01] [1-5][0-9]{2} [\x20-\x7e]*', lines[0]):
            raise Failure('INVALID_HTTP', 400)
        first = int(lines[0].split(' ')[1])
    else:
        if not re.fullmatch(r'[A-Z]+ /[\x21-\x7e]* HTTP/1\.1', lines[0]):
            raise Failure('INVALID_HTTP', 400)
        method, target, _ = lines[0].split(' ')
        first = (method, target)
    headers = {}
    for line in lines[1:]:
        k, sep, v = line.partition(':')
        if not sep or not TOKEN.fullmatch(k) or any(ord(c) < 32 or ord(c) > 126 for c in v):
            raise Failure('INVALID_HTTP_HEADERS', 400)
        k = k.lower()
        if k in headers:
            raise Failure('DUPLICATE_HEADER', 400)
        headers[k] = v.strip(' ')
    if 'transfer-encoding' in headers or 'trailer' in headers:
        raise Failure('INVALID_HTTP_FRAMING', 400)
    length = headers.get('content-length')
    if length is not None and not re.fullmatch(r'0|[1-9][0-9]{0,7}', length):
        raise Failure('INVALID_HTTP_FRAMING', 400)
    if response and length is None:
        raise Failure('INVALID_HTTP_FRAMING', 400)
    return first, headers

def build_request(config, semantic_route, upstream_key):
    config.validate()
    key = _safe_header_credential(upstream_key)
    if semantic_route == 'integrations':
        suffix = '/integrations'
    elif semantic_route == 'posts':
        suffix = '/posts?' + urlencode({'startDate': config.start_inclusive, 'endDate': config.upstream_end_inclusive})
    else:
        raise Failure('ROUTE_DENIED', 403)
    scheme, host, port, base = config.endpoint
    if ':' in host:
        host = '[' + host + ']'
    authority = host if port == (443 if scheme == 'https' else 80) else f'{host}:{port}'
    return (f'GET {base}{suffix} HTTP/1.1\r\nHost: {authority}\r\nAuthorization: {key}\r\n'
            'Accept: application/json\r\nAccept-Encoding: identity\r\nConnection: close\r\n\r\n').encode('ascii')

def upstream_failure(status):
    if 300 <= status <= 399:
        return Failure('UPSTREAM_REDIRECT', 502)
    return Failure({400:'UPSTREAM_BAD_REQUEST',401:'UPSTREAM_AUTH',403:'UPSTREAM_AUTH',404:'UPSTREAM_NOT_FOUND',429:'UPSTREAM_RATE_LIMIT'}.get(status,'UPSTREAM_FAILURE'),
                   403 if status in (401,403) else 429 if status == 429 else 502)

def parse_response(status, headers, body, max_bytes):
    if status != 200:
        raise upstream_failure(status)
    if len(body) > max_bytes:
        raise Failure('RESPONSE_TOO_LARGE', 502)
    if headers.get('content-type','').lower() not in ('application/json','application/json; charset=utf-8') or headers.get('content-encoding','identity') != 'identity':
        raise Failure('INVALID_UPSTREAM_CONTENT', 502)
    return strict_json(body)

def encode_response(status, payload):
    body = json.dumps(payload, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')
    return (f'HTTP/1.1 {status} Result\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n'
            'Cache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nConnection: close\r\n\r\n').encode('ascii') + body
