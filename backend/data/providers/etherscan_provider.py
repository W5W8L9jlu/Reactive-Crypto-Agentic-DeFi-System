from __future__ import annotations

from typing import Any, Awaitable, Callable, Mapping

from ._shared_http_client import (
    ProviderConfigurationError,
    ProviderDomainError,
    ProviderRequest,
    ProviderRequestError,
    ProviderResponse,
    RetryPolicy,
    SharedHTTPClient,
    TimeoutPolicy,
)


FallbackCallable = Callable[[ProviderRequest, Exception], Awaitable[ProviderResponse]]


class EtherscanProvider:
    provider_name = "etherscan"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.etherscan.io",
        timeout_policy: TimeoutPolicy | None = None,
        retry_policy: RetryPolicy | None = None,
        shared_http_client: SharedHTTPClient | None = None,
    ) -> None:
        if not api_key:
            raise ProviderConfigurationError("api_key is required for EtherscanProvider")

        self._api_key = api_key
        self._owns_http_client = shared_http_client is None
        self._http_client = shared_http_client or SharedHTTPClient(
            base_url=base_url,
            timeout_policy=timeout_policy,
            retry_policy=retry_policy,
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        module, action = _resolve_module_action(request)
        query = _resolve_query(request.params)

        params = {
            "module": module,
            "action": action,
            "apikey": self._api_key,
            **query,
        }
        payload = await self._http_client.get("/api", params=params)

        # TODO(provider_architecture): source-of-truth/business status checks live outside provider layer.
        return ProviderResponse(
            provider=self.provider_name,
            operation=f"{module}.{action}",
            payload=payload,
            metadata={"fallback_capable": True},
        )

    async def fetch_or_fallback(
        self,
        request: ProviderRequest,
        *,
        fallback: FallbackCallable | None = None,
    ) -> ProviderResponse:
        try:
            return await self.fetch(request)
        except ProviderDomainError as exc:
            if fallback is None:
                raise

            fallback_response = await fallback(request, exc)
            metadata = dict(fallback_response.metadata)
            metadata["fallback_from"] = self.provider_name
            metadata["fallback_reason"] = str(exc)
            return ProviderResponse(
                provider=fallback_response.provider,
                operation=fallback_response.operation,
                payload=fallback_response.payload,
                metadata=metadata,
            )

    async def close(self) -> None:
        if self._owns_http_client:
            await self._http_client.close()


def _resolve_module_action(request: ProviderRequest) -> tuple[str, str]:
    module = request.params.get("module")
    action = request.params.get("action")
    if isinstance(module, str) and isinstance(action, str):
        return module, action

    if "." not in request.operation:
        raise ProviderRequestError(
            "Etherscan request requires params.module + params.action "
            "or operation in '<module>.<action>' format"
        )
    module_from_op, action_from_op = request.operation.split(".", 1)
    if not module_from_op or not action_from_op:
        raise ProviderRequestError("invalid Etherscan operation format")
    return module_from_op, action_from_op


def _resolve_query(params: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(params, Mapping):
        raise ProviderRequestError("Etherscan request.params must be a mapping")

    query_raw = params.get("query", {})
    if not isinstance(query_raw, Mapping):
        raise ProviderRequestError("Etherscan request.params['query'] must be a mapping")
    return dict(query_raw)
