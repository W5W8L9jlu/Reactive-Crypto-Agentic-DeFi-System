from __future__ import annotations

import httpx

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
    from gql import Client, gql
    from gql.transport.httpx import HTTPXAsyncTransport
except ImportError as import_error:  # pragma: no cover - environment dependent
    Client = None  # type: ignore[assignment]
    gql = None  # type: ignore[assignment]
    HTTPXAsyncTransport = None  # type: ignore[assignment]
    _GQL_IMPORT_ERROR = import_error
else:
    _GQL_IMPORT_ERROR = None


class GraphProvider:
    provider_name = "the_graph"

    def __init__(
        self,
        graph_endpoint: str,
        *,
        retry_policy: RetryPolicy | None = None,
        request_timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        if not graph_endpoint:
            raise ProviderConfigurationError("graph_endpoint is required for GraphProvider")
        if _GQL_IMPORT_ERROR is not None:
            raise ProviderConfigurationError(
                "gql is required for GraphProvider. Please install dependencies "
                "'gql[httpx]' or equivalent gql HTTPX transport support."
            ) from _GQL_IMPORT_ERROR

        self._graph_endpoint = graph_endpoint
        self._retry_policy = retry_policy or RetryPolicy()
        self._transport = HTTPXAsyncTransport(
            url=graph_endpoint,
            timeout=request_timeout_seconds,
            headers=headers,
        )
        self._client = Client(
            transport=self._transport,
            fetch_schema_from_transport=False,
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        query_text = request.operation.strip()
        if not query_text:
            raise ProviderRequestError("Graph request.operation must be GraphQL query text")

        variables = request.params.get("variables", {})
        if not isinstance(variables, dict):
            raise ProviderRequestError("Graph request.params['variables'] must be a dict")

        operation_name_raw = request.params.get("operation_name")
        operation_name = operation_name_raw if isinstance(operation_name_raw, str) else None
        document = gql(query_text)

        async def _execute() -> dict:
            return await self._client.execute_async(
                document,
                variable_values=variables,
                operation_name=operation_name,
            )

        try:
            payload = await run_with_retry(
                _execute,
                retry_policy=self._retry_policy,
                is_retryable_error=_is_retryable_graph_error,
            )
        except Exception as exc:
            raise ProviderUpstreamError("The Graph query failed after retries") from exc
        return ProviderResponse(
            provider=self.provider_name,
            operation=operation_name or "query",
            payload=payload,
            metadata={"endpoint": self._graph_endpoint},
        )

    async def close(self) -> None:
        await self._transport.close()


def _is_retryable_graph_error(exc: Exception) -> bool:
    retryable_transport_errors = {
        "TransportConnectionFailed",
        "TransportClosed",
        "TransportServerError",
    }
    return isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)) or (
        exc.__class__.__name__ in retryable_transport_errors
    )
