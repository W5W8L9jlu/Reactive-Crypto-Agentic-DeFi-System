from __future__ import annotations

import asyncio

import httpx
import pytest

from backend.data.providers import etherscan_provider, graph_provider, rpc_provider
from backend.data.providers._shared_http_client import (
    ProviderDomainError,
    ProviderRequest,
    ProviderResponse,
    ProviderUpstreamError,
    RetryPolicy,
    SharedHTTPClient,
)


def _run(coro):
    return asyncio.run(coro)


def test_shared_http_client_retries_retryable_status_and_returns_json():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"error": "retry"})
        assert request.url.path == "/api"
        return httpx.Response(200, json={"ok": True, "attempt": calls})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.test",
    )
    shared = SharedHTTPClient(
        client=client,
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_backoff_seconds=0,
            max_backoff_seconds=0,
            backoff_multiplier=1,
        ),
    )

    try:
        result = _run(shared.get("/api", params={"q": "1"}))
        assert result == {"ok": True, "attempt": 2}
        assert calls == 2
    finally:
        _run(shared.close())
        _run(client.aclose())


def test_shared_http_client_retries_timeout_before_raising():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("timed out", request=request)

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.test",
    )
    shared = SharedHTTPClient(
        client=client,
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_backoff_seconds=0,
            max_backoff_seconds=0,
            backoff_multiplier=1,
        ),
    )

    try:
        with pytest.raises(ProviderUpstreamError, match="upstream request failed after retries"):
            _run(shared.get("/api"))
        assert calls == 2
    finally:
        _run(shared.close())
        _run(client.aclose())


def test_rpc_provider_fetch_retries_and_returns_payload(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(rpc_provider, "_WEB3_IMPORT_ERROR", None)

    calls = 0

    class FakeHTTPProvider:
        def __init__(self, *, endpoint_uri: str, request_kwargs: dict[str, object]) -> None:
            self.endpoint_uri = endpoint_uri
            self.request_kwargs = request_kwargs

    class FakeWeb3:
        def __init__(self, provider: FakeHTTPProvider) -> None:
            self.provider = provider
            self.manager = self

        def request_blocking(self, method: str, params: list[object]) -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise TimeoutError("timed out")
            return {
                "method": method,
                "params": params,
                "attempt": calls,
            }

        def is_connected(self) -> bool:
            return True

    monkeypatch.setattr(rpc_provider, "HTTPProvider", FakeHTTPProvider)
    monkeypatch.setattr(rpc_provider, "Web3", FakeWeb3)

    provider = rpc_provider.RPCProvider(
        "https://rpc.test",
        request_timeout_seconds=4.5,
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_backoff_seconds=0,
            max_backoff_seconds=0,
            backoff_multiplier=1,
        ),
    )

    response = _run(
        provider.fetch(
            ProviderRequest(
                operation="eth_blockNumber",
                params={"params": ["latest"]},
            )
        )
    )

    assert response.provider == "rpc"
    assert response.operation == "eth_blockNumber"
    assert response.payload == {
        "method": "eth_blockNumber",
        "params": ["latest"],
        "attempt": 2,
    }
    assert response.metadata == {"endpoint": "https://rpc.test"}
    assert calls == 2


def test_graph_provider_fetch_retries_and_closes_transport(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(graph_provider, "_GQL_IMPORT_ERROR", None)

    calls = 0

    class FakeTransport:
        def __init__(self, *, url: str, timeout: float, headers: dict[str, str] | None) -> None:
            self.url = url
            self.timeout = timeout
            self.headers = headers
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    class FakeClient:
        def __init__(self, *, transport: FakeTransport, fetch_schema_from_transport: bool) -> None:
            self.transport = transport
            self.fetch_schema_from_transport = fetch_schema_from_transport

        async def execute_async(
            self,
            document: str,
            *,
            variable_values: dict[str, object],
            operation_name: str | None,
        ) -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise httpx.NetworkError("network glitch")
            return {
                "document": document,
                "variable_values": variable_values,
                "operation_name": operation_name,
                "attempt": calls,
            }

    monkeypatch.setattr(graph_provider, "HTTPXAsyncTransport", FakeTransport)
    monkeypatch.setattr(graph_provider, "Client", FakeClient)
    monkeypatch.setattr(graph_provider, "gql", lambda query_text: query_text)

    provider = graph_provider.GraphProvider(
        "https://graph.test",
        request_timeout_seconds=7.0,
        headers={"X-Test": "1"},
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_backoff_seconds=0,
            max_backoff_seconds=0,
            backoff_multiplier=1,
        ),
    )

    response = _run(
        provider.fetch(
            ProviderRequest(
                operation="query MyQuery { token(id: \"1\") { id } }",
                params={
                    "variables": {"id": "1"},
                    "operation_name": "MyQuery",
                },
            )
        )
    )

    assert response.provider == "the_graph"
    assert response.operation == "MyQuery"
    assert response.payload == {
        "document": 'query MyQuery { token(id: "1") { id } }',
        "variable_values": {"id": "1"},
        "operation_name": "MyQuery",
        "attempt": 2,
    }
    assert response.metadata == {"endpoint": "https://graph.test"}
    assert calls == 2

    _run(provider.close())
    assert provider._transport.closed is True


def test_etherscan_provider_falls_back_on_domain_error():
    class FakeSharedHTTPClient:
        def __init__(self) -> None:
            self.calls = 0

        async def get(self, path: str, *, params: dict[str, object]) -> dict[str, object]:
            self.calls += 1
            raise ProviderDomainError("rate limited")

        async def close(self) -> None:
            return None

    async def fallback(
        request: ProviderRequest,
        exc: Exception,
    ) -> ProviderResponse:
        assert request.operation == "account.balance"
        assert isinstance(exc, ProviderDomainError)
        return ProviderResponse(
            provider="rpc",
            operation="eth_getBalance",
            payload={"source": "fallback"},
            metadata={"origin": "rpc"},
        )

    shared_client = FakeSharedHTTPClient()
    provider = etherscan_provider.EtherscanProvider(
        "test-key",
        shared_http_client=shared_client,  # type: ignore[arg-type]
    )

    response = _run(
        provider.fetch_or_fallback(
            ProviderRequest(
                operation="account.balance",
                params={"query": {"address": "0xabc"}},
            ),
            fallback=fallback,
        )
    )

    assert shared_client.calls == 1
    assert response.provider == "rpc"
    assert response.operation == "eth_getBalance"
    assert response.payload == {"source": "fallback"}
    assert response.metadata == {
        "origin": "rpc",
        "fallback_from": "etherscan",
        "fallback_reason": "rate limited",
    }
