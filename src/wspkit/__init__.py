"""wspkit: Workflow Server Protocol (WSP) library.

Re-exports the public API for tools that take a direct dependency on
``wspkit``. Programmatic users build a :class:`HandlerRegistry`, register
:data:`Handler` callables for the WSP methods they implement, and call
:func:`run_stdio` to serve the protocol over stdin/stdout. Users who only
need the bundled CLI or the Config_File flow do not need to import from
this top-level module.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from wspkit.endpoints import (
    PROTOCOL_VERSION,
    Capabilities,
    DeleteAck,
    Environment,
    ExecuteResult,
    Package,
)
from wspkit.errors import (
    DuplicateRegistrationError,
    JsonRpcErrorCode,
    ProtocolError,
    WspError,
    WspErrorCode,
)
from wspkit.protocol import (
    JsonRpcError,
    JsonRpcRequest,
    JsonRpcResponse,
)
from wspkit.registry import Handler, HandlerRegistry
from wspkit.server import run_stdio

try:
    __version__: str = _pkg_version("wspkit")
except PackageNotFoundError:  # pragma: no cover - source checkout
    __version__ = "0.0.0+unknown"

del PackageNotFoundError, _pkg_version

__all__ = [
    "PROTOCOL_VERSION",
    "Capabilities",
    "DeleteAck",
    "DuplicateRegistrationError",
    "Environment",
    "ExecuteResult",
    "Handler",
    "HandlerRegistry",
    "JsonRpcError",
    "JsonRpcErrorCode",
    "JsonRpcRequest",
    "JsonRpcResponse",
    "Package",
    "ProtocolError",
    "WspError",
    "WspErrorCode",
    "__version__",
    "run_stdio",
]
