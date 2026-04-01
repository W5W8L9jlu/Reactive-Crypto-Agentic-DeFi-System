from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping

from backend.data.context_builder.models import (
    CapitalFlow,
    ExecutionState,
    LiquidityDepth,
    MarketTrend,
    OnchainFlow,
    PositionState,
    RiskState,
    TrendDirection,
)
from backend.data.providers._shared_http_client import (
    ProviderDomainError,
    ProviderRequest,
    ProviderResponse,
    ProviderUpstreamError,
)
from pydantic import ValidationError


class _ProviderAdapter:
    def __init__(self, primary_provider: Any, fallback_provider: Any | None = None) -> None:
        self._primary = primary_provider
        self._fallback = fallback_provider

    async def _fetch_parsed(
        self,
        operation: str,
        params: Mapping[str, Any],
        parser: Callable[[Mapping[str, Any]], Any],
    ) -> Any:
        primary_error: Exception | None = None

        try:
            payload = await self._fetch_from_provider(self._primary, operation, params)
            return parser(payload)
        except (ProviderDomainError, ProviderUpstreamError, ValidationError, ValueError) as exc:
            primary_error = exc

        if self._fallback is None:
            raise primary_error

        try:
            payload = await self._fetch_from_provider(self._fallback, operation, params)
            return parser(payload)
        except (ProviderDomainError, ProviderUpstreamError, ValidationError, ValueError) as exc:
            raise ProviderDomainError(
                f"All providers failed for {operation}"
            ) from exc

    async def _fetch_from_provider(
        self,
        provider: Any,
        operation: str,
        params: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        response = await provider.fetch(ProviderRequest(operation=operation, params=params))
        return _require_mapping_payload(response, operation)


class AggregatedMarketFetcher(_ProviderAdapter):
    async def fetch_market_trend(self, pair: str) -> MarketTrend:
        return await self._fetch_parsed(
            "market_trend",
            {"pair": pair},
            self._parse_market_trend,
        )

    async def fetch_capital_flow(self, pair: str) -> CapitalFlow:
        return await self._fetch_parsed(
            "capital_flow",
            {"pair": pair},
            self._parse_capital_flow,
        )

    def _parse_market_trend(self, payload: Mapping[str, Any]) -> MarketTrend:
        return MarketTrend(
            direction=TrendDirection(_require_str(payload, "direction", "market_trend")),
            confidence_score=_require_decimal(payload, "confidence", "market_trend"),
            timeframe_minutes=_require_int(payload, "timeframe_minutes", "market_trend"),
            **_aggregated_at_kwargs(payload),
        )

    def _parse_capital_flow(self, payload: Mapping[str, Any]) -> CapitalFlow:
        return CapitalFlow(
            net_inflow_usd=_require_decimal(payload, "net_inflow_usd", "capital_flow"),
            volume_24h_usd=_require_decimal(payload, "volume_24h_usd", "capital_flow"),
            whale_inflow_usd=_require_decimal(payload, "whale_inflow_usd", "capital_flow"),
            retail_inflow_usd=_require_decimal(payload, "retail_inflow_usd", "capital_flow"),
            **_aggregated_at_kwargs(payload),
        )


class AggregatedLiquidityFetcher(_ProviderAdapter):
    async def fetch_liquidity_depth(self, pair: str, dex: str) -> LiquidityDepth:
        return await self._fetch_parsed(
            "liquidity_depth",
            {"pair": pair, "dex": dex},
            lambda payload: LiquidityDepth(
                pair=pair,
                dex=dex,
                depth_usd_2pct=_require_decimal(payload, "depth_2pct", "liquidity_depth"),
                total_tvl_usd=_require_decimal(payload, "tvl", "liquidity_depth"),
                **_aggregated_at_kwargs(payload),
            ),
        )


class AggregatedOnchainFetcher(_ProviderAdapter):
    async def fetch_onchain_flow(self) -> OnchainFlow:
        try:
            return await self._fetch_parsed(
                "onchain_flow",
                {},
                lambda payload: OnchainFlow(
                    active_address_delta_24h=_require_int(
                        payload, "active_address_delta_24h", "onchain_flow"
                    ),
                    transaction_count_24h=_require_int(
                        payload, "transaction_count_24h", "onchain_flow"
                    ),
                    gas_price_gwei=_require_decimal(payload, "gas_price_gwei", "onchain_flow"),
                    **_aggregated_at_kwargs(payload),
                ),
            )
        except (ProviderDomainError, ProviderUpstreamError) as exc:
            raise ProviderDomainError("Failed to fetch onchain flow data") from exc


class AggregatedRiskFetcher(_ProviderAdapter):
    async def fetch_risk_state(self, pair: str) -> RiskState:
        return await self._fetch_parsed(
            "risk_state",
            {"pair": pair},
            lambda payload: RiskState(
                volatility_annualized=_require_decimal(
                    payload, "volatility_annualized", "risk_state"
                ),
                var_95_usd=_require_decimal(payload, "var_95_usd", "risk_state"),
                correlation_to_market=_require_decimal(
                    payload, "correlation_to_market", "risk_state"
                ),
                **_aggregated_at_kwargs(payload),
            ),
        )


class AggregatedPositionFetcher(_ProviderAdapter):
    async def fetch_position_state(self, pair: str) -> PositionState:
        return await self._fetch_parsed(
            "position_state",
            {"pair": pair},
            lambda payload: PositionState(
                current_position_usd=_require_decimal(
                    payload, "current_position_usd", "position_state"
                ),
                unrealized_pnl_usd=_require_decimal(
                    payload, "unrealized_pnl_usd", "position_state"
                ),
                entry_price_usd=_optional_decimal(payload, "entry_price_usd", "position_state"),
                position_opened_at=_optional_datetime(payload, "position_opened_at"),
                **_aggregated_at_kwargs(payload),
            ),
        )


class AggregatedExecutionFetcher(_ProviderAdapter):
    async def fetch_execution_state(self) -> ExecutionState:
        return await self._fetch_parsed(
            "execution_state",
            {},
            lambda payload: ExecutionState(
                daily_trades_executed=_require_int(
                    payload, "daily_trades_executed", "execution_state"
                ),
                daily_volume_usd=_require_decimal(
                    payload, "daily_volume_usd", "execution_state"
                ),
                last_execution_at=_optional_datetime(payload, "last_execution_at"),
                **_aggregated_at_kwargs(payload),
            ),
        )


def _require_mapping_payload(
    response: ProviderResponse,
    operation: str,
) -> Mapping[str, Any]:
    payload = response.payload
    if not isinstance(payload, Mapping):
        raise ProviderDomainError(
            f"{response.provider} returned non-mapping payload for {operation}"
        )
    return payload


def _require_field(payload: Mapping[str, Any], field: str, operation: str) -> Any:
    if field not in payload:
        raise ProviderDomainError(
            f"Missing required field {field} in {operation} payload"
        )
    return payload[field]


def _require_decimal(payload: Mapping[str, Any], field: str, operation: str) -> Decimal:
    raw_value = _require_field(payload, field, operation)
    try:
        return Decimal(str(raw_value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ProviderDomainError(
            f"Invalid decimal field {field} in {operation} payload"
        ) from exc


def _require_int(payload: Mapping[str, Any], field: str, operation: str) -> int:
    raw_value = _require_field(payload, field, operation)
    try:
        return int(raw_value)
    except (ValueError, TypeError) as exc:
        raise ProviderDomainError(
            f"Invalid integer field {field} in {operation} payload"
        ) from exc


def _require_str(payload: Mapping[str, Any], field: str, operation: str) -> str:
    raw_value = _require_field(payload, field, operation)
    if not isinstance(raw_value, str) or raw_value == "":
        raise ProviderDomainError(
            f"Invalid string field {field} in {operation} payload"
        )
    return raw_value


def _optional_decimal(
    payload: Mapping[str, Any],
    field: str,
    operation: str,
) -> Decimal | None:
    if field not in payload or payload[field] is None:
        return None
    return _require_decimal(payload, field, operation)


def _optional_datetime(payload: Mapping[str, Any], field: str) -> datetime | None:
    if field not in payload or payload[field] is None:
        return None

    raw_value = payload[field]
    if isinstance(raw_value, datetime):
        return raw_value

    if isinstance(raw_value, str):
        try:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ProviderDomainError(f"Invalid datetime field {field}") from exc

    raise ProviderDomainError(f"Invalid datetime field {field}")


def _aggregated_at_kwargs(payload: Mapping[str, Any]) -> dict[str, datetime]:
    aggregated_at = _optional_datetime(payload, "aggregated_at")
    if aggregated_at is None:
        return {}
    return {"aggregated_at": aggregated_at}
