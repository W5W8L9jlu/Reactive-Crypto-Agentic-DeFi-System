from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping, Protocol, TypeVar

import httpx


class ProviderDomainError(Exception):
    """Base class for provider-layer errors."""


class ProviderConfigurationError(ProviderDomainError):
    """Raised when a provider is initialized with invalid configuration."""


class ProviderRequestError(ProviderDomainError):
    """Raised when caller inputs do not satisfy provider contract."""


class ProviderUpstreamError(ProviderDomainError):
    """Raised when an upstream provider response cannot be accepted."""


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    operation: str
    params: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    provider: str
    operation: str
    payload: Any
    metadata: Mapping[str, Any] = field(default_factory=dict)


class Provider(Protocol):
    provider_name: str

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        ...


@dataclass(frozen=True, slots=True)
class TimeoutPolicy:
    connect_seconds: float = 3.0
    read_seconds: float = 10.0
    write_seconds: float = 10.0
    pool_seconds: float = 3.0

    def to_httpx_timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            connect=self.connect_seconds,
            read=self.read_seconds,
            write=self.write_seconds,
            pool=self.pool_seconds,
        )


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_backoff_seconds: float = 0.2
    max_backoff_seconds: float = 1.5
    backoff_multiplier: float = 2.0
    retryable_status_codes: frozenset[int] = frozenset({429, 500, 502, 503, 504})


_T = TypeVar("_T")


async def run_with_retry(
    operation: Callable[[], Awaitable[_T]],
    *,
    retry_policy: RetryPolicy,
    is_retryable_error: Callable[[Exception], bool],
) -> _T:
    if retry_policy.max_attempts < 1:
        raise ProviderConfigurationError("retry_policy.max_attempts must be >= 1")

    delay = retry_policy.initial_backoff_seconds
    for attempt in range(1, retry_policy.max_attempts + 1):
        try:
            return await operation()
        except Exception as exc:
            final_attempt = attempt >= retry_policy.max_attempts
            if final_attempt or not is_retryable_error(exc):
                raise

            await asyncio.sleep(delay)
            delay = min(
                delay * retry_policy.backoff_multiplier,
                retry_policy.max_backoff_seconds,
            )

    raise ProviderConfigurationError("unreachable retry state")


class _RetryableHTTPStatusError(Exception):
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        super().__init__(f"retryable HTTP status: {response.status_code}")


class SharedHTTPClient:
    """Shared httpx AsyncClient with centralized timeout + retry policy."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        timeout_policy: TimeoutPolicy | None = None,
        retry_policy: RetryPolicy | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url
        self._default_headers = dict(default_headers or {})
        self._timeout_policy = timeout_policy or TimeoutPolicy()
        self._retry_policy = retry_policy or RetryPolicy()
        self._client = client
        self._owns_client = client is None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client

        self._client = httpx.AsyncClient(
            base_url=self._base_url or "",
            headers=self._default_headers,
            timeout=self._timeout_policy.to_httpx_timeout(),
        )
        return self._client

    async def __aenter__(self) -> "SharedHTTPClient":
        self._ensure_client()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client is None or not self._owns_client:
            return

        await self._client.aclose()
        self._client = None

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        client = self._ensure_client()

        async def _send() -> httpx.Response:
            response = await client.request(
                method=method.upper(),
                url=path,
                params=params,
                json=json_body,
                headers=headers,
            )
            if response.status_code in self._retry_policy.retryable_status_codes:
                raise _RetryableHTTPStatusError(response)
            return response

        try:
            response = await run_with_retry(
                _send,
                retry_policy=self._retry_policy,
                is_retryable_error=_is_retryable_http_error,
            )
        except _RetryableHTTPStatusError as exc:
            raise ProviderUpstreamError(
                f"upstream kept returning retryable status: {exc.response.status_code}"
            ) from exc
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderUpstreamError("upstream request failed after retries") from exc

        if response.is_error:
            raise ProviderUpstreamError(
                f"HTTP {response.status_code} from upstream: {response.text[:200]}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise ProviderUpstreamError("upstream payload is not valid JSON") from exc

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self.request(
            "GET",
            path,
            params=params,
            headers=headers,
        )

    async def post(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self.request(
            "POST",
            path,
            params=params,
            json_body=json_body,
            headers=headers,
        )


def _is_retryable_http_error(exc: Exception) -> bool:
    return isinstance(
        exc,
        (
            _RetryableHTTPStatusError,
            httpx.TimeoutException,
            httpx.NetworkError,
        ),
    )
