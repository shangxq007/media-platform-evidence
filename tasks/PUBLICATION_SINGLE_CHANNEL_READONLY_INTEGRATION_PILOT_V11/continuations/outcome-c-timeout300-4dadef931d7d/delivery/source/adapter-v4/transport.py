"""Actual synchronous bounded HTTP IO. Authoring only in the offline packet.

No DNS resolution, proxy, redirects, retries, event loops or graceful TLS shutdown.
Every wait shares one absolute deadline. Closing the descriptor never awaits a peer.
"""
import errno
import ipaddress
import select
import socket
import ssl
import time
from model import Failure
from wire import MAX_HEADERS, build_request, parse_head, parse_response

class Operation:
    def __init__(self, seconds, max_volume, cancel=None):
        self.deadline = time.monotonic() + seconds
        self.max_volume = max_volume
        self.volume = 0
        self.cancel = cancel or (lambda: None)

    def check(self):
        if time.monotonic() >= self.deadline:
            raise Failure('DEADLINE_EXCEEDED',504)
        self.cancel()

    def consume(self, n):
        self.volume += n
        if self.volume > self.max_volume:
            raise Failure('READ_VOLUME_EXHAUSTED',502)
        self.check()

    def wait(self, sock, writing=False):
        self.check()
        timeout = min(0.02, max(0,self.deadline-time.monotonic()))
        ready = select.select([] if writing else [sock], [sock] if writing else [], [sock], timeout)
        self.check()
        if ready[2]:
            raise Failure('TRANSPORT_FAILURE',502)
        return bool(ready[1] if writing else ready[0])

def connect(ip, port, op, tls_context=None, hostname=None):
    op.check()  # generation/deadline checked before descriptor acquisition
    address = ipaddress.ip_address(ip)  # literal only, no DNS
    sock = socket.socket(socket.AF_INET6 if address.version == 6 else socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    try:
        op.check()
        code = sock.connect_ex((str(address),port))
        if code not in (0,errno.EINPROGRESS,errno.EWOULDBLOCK,errno.EALREADY):
            raise Failure('TRANSPORT_FAILURE',502)
        while not op.wait(sock,True):
            pass
        if sock.getsockopt(socket.SOL_SOCKET,socket.SO_ERROR):
            raise Failure('TRANSPORT_FAILURE',502)
        if tls_context is not None:
            sock = tls_context.wrap_socket(sock,server_hostname=hostname,do_handshake_on_connect=False)
            sock.setblocking(False)
            while True:
                op.check()
                try:
                    sock.do_handshake()
                    break
                except ssl.SSLWantReadError:
                    op.wait(sock)
                except ssl.SSLWantWriteError:
                    op.wait(sock,True)
        return sock
    except BaseException:
        sock.close()
        raise

def send(sock, data, op):
    remaining = memoryview(data)
    while remaining:
        op.check()
        try:
            count = sock.send(remaining)
            if not count:
                raise Failure('TRANSPORT_FAILURE',502)
            remaining = remaining[count:]
        except (BlockingIOError,ssl.SSLWantWriteError):
            op.wait(sock,True)
        except ssl.SSLWantReadError:
            op.wait(sock)
    op.check()

def receive(sock, size, op):
    while True:
        op.check()
        try:
            data = sock.recv(size)
            op.consume(len(data))
            return data
        except (BlockingIOError,ssl.SSLWantReadError):
            op.wait(sock)
        except ssl.SSLWantWriteError:
            op.wait(sock,True)

def read_head(sock, op):
    # One byte at a time prevents unbounded read-ahead beyond header cap.
    head = bytearray()
    while not head.endswith(b'\r\n\r\n'):
        if len(head) >= MAX_HEADERS:
            raise Failure('HEADERS_TOO_LARGE',431)
        chunk = receive(sock,1,op)
        if not chunk:
            raise Failure('INCOMPLETE_HTTP',400)
        head.extend(chunk)
    return bytes(head)

def read_response(sock, op, max_bytes):
    status, headers = parse_head(read_head(sock,op),response=True)
    size = int(headers['content-length'])
    if size > max_bytes:
        raise Failure('RESPONSE_TOO_LARGE',502)
    body = bytearray()
    while len(body) < size:
        data = receive(sock,min(16384,size-len(body)),op)
        if not data:
            raise Failure('INCOMPLETE_HTTP',502)
        body.extend(data)
    # Only one message per connection; require EOF, rejecting trailing framing/data.
    if receive(sock,1,op):
        raise Failure('INVALID_HTTP_FRAMING',502)
    return status,headers,bytes(body)

def upstream(config, route, key, op, tls_context):
    request = build_request(config,route,key)
    _, hostname, port, _ = config.endpoint
    sock = None
    try:
        sock = connect(config.approved_ip,port,op,tls_context,hostname)
        send(sock,request,op)
        status,headers,body = read_response(sock,op,config.max_bytes)
        return parse_response(status,headers,body,config.max_bytes)
    except Failure:
        raise
    except (OSError,ValueError,UnicodeError):
        raise Failure('UPSTREAM_TRANSPORT',502) from None
    finally:
        if sock is not None:
            sock.close()
