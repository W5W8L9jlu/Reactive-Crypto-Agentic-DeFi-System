from __future__ import annotations

import asyncio
from typing import Any

from ._shared_http_client import (
    ProviderConfigurationError,
    ProviderRequest,
    ProviderRequestError,
    ProviderResponse,
    ProviderUpstreamError,
    RetryPolicy,
    run_with_retry,
)

try:
    from web3 import Web3
    from web3.providers.rpc import HTTPProvider
except ImportError as import_error:  # pragma: no cover - environment dependent
    Web3 = None  # type: ignore[assignment]
    HTTPProvider = None  # type: ignore[assignment]
    _WEB3_IMPORT_ERROR = import_error
else:
    _WEB3_IMPORT_ERROR = None


class RPCProvider:
    provider_name = "rpc"

    def __init__(
        self,
        rpc_url: str,
        *,
        request_timeout_seconds: float = 10.0,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        if not rpc_url:
            raise ProviderConfigurationError("rpc_url is required for RPCProvider")
        if _WEB3_IMPORT_ERROR is not None:
            raise ProviderConfigurationError(
                "web3.py is required for RPCProvider. Please install dependency 'web3'."
            ) from _WEB3_IMPORT_ERROR

        self._rpc_url = rpc_url
        self._retry_policy = retry_policy or RetryPolicy()
        self._web3 = Web3(
            HTTPProvider(
                endpoint_uri=rpc_url,
                request_kwargs={"timeout": request_timeout_seconds},
            )
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        method = request.operation.strip()
        if not method:
            raise ProviderRequestError("RPC request.operation must be a non-empty method")

        params = _extract_rpc_params(request)

        async def _call_rpc() -> Any:
            return await asyncio.to_thread(
                self._web3.manager.request_blocking,
                method,
                params,
            )

        try:
            payload = await run_with_retry(
                _call_rpc,
                retry_policy=self._retry_policy,
                is_retryable_error=_is_retryable_rpc_error,
            )
        except Exception as exc:
            raise ProviderUpstreamError(f"RPC call failed for method '{method}'") from exc
        return ProviderResponse(
            provider=self.provider_name,
            operation=method,
            payload=payload,
            metadata={"endpoint": self._rpc_url},
        )

    async def is_available(self) -> bool:
        return await asyncio.to_thread(self._web3.is_connected)


def _extract_rpc_params(request: ProviderRequest) -> list[Any]:
    params_raw = request.params.get("params", [])
    if not isinstance(params_raw, (list, tuple)):
        raise ProviderRequestError("RPC request.params['params'] must be a list/tuple")
    return list(params_raw)


def _is_retryable_rpc_error(exc: Exception) -> bool:
    retryable_names = {
        "ConnectionError",
        "Timeout",
        "RequestException",
        "HTTPError",
    }
    return isinstance(exc, (TimeoutError, OSError)) or exc.__class__.__name__ in retryable_names
