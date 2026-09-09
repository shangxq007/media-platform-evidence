"""Pure metadata for a trusted owner-local runtime; no discovery or IO.

Only owner runtime glue calls _bound_handle after getsockname(). This is a local
object capability, not a network deserializer or protection from hostile Python
code in the owner process. No token/key is stored in metadata.
"""
from dataclasses import dataclass, field
from model import Failure, identifier

LOCAL_HOST = '127.0.0.1'
_ISSUER = object()

@dataclass(frozen=True)
class RuntimeHandle:
    port: int
    revision: str
    _issuer: object = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        if self._issuer is not _ISSUER or type(self.port) is not int or not 1 <= self.port <= 65535:
            raise Failure('INVALID_RUNTIME_HANDLE',403)
        identifier(self.revision)

    @property
    def host_header(self):
        return f'{LOCAL_HOST}:{self.port}'


def require_handle(handle):
    if type(handle) is not RuntimeHandle:
        raise Failure('INVALID_RUNTIME_HANDLE',403)
    handle.__post_init__()
    return handle


def _bound_handle(address, revision):
    """Owner-only issuance from the bound listener's actual getsockname tuple."""
    if type(address) is not tuple or len(address) != 2 or address[0] != LOCAL_HOST:
        raise Failure('INVALID_RUNTIME_HANDLE',403)
    return RuntimeHandle(address[1], revision, _ISSUER)
