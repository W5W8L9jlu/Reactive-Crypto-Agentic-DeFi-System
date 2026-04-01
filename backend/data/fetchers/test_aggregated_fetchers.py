from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

import pytest

from backend.data.context_builder import DecisionContextBuilder, StrategyConstraints
from backend.data.fetchers import (
    AggregatedExecutionFetcher,
    AggregatedLiquidityFetcher,
    AggregatedMarketFetcher,
    AggregatedOnchainFetcher,
    AggregatedPositionFetcher,
    AggregatedRiskFetcher,
)
from backend.data.providers._shared_http_client import (
    ProviderDomainError,
    ProviderRequest,
    ProviderResponse,
    ProviderUpstreamError,
)


class RecordingProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        payloads: dict[str, Any] | None = None,
        errors: dict[str, Exception] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self._payloads = payloads or {}
        self._errors = errors or {}
        self.calls: list[ProviderRequest] = []

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        self.calls.append(request)
        if request.operation in self._errors:
            raise self._errors[request.operation]

        if request.operation not in self._payloads:
            raise ProviderDomainError(
                f"{self.provider_name} has no payload for operation {request.operation}"
            )

        return ProviderResponse(
            provider=self.provider_name,
            operation=request.operation,
            payload=self._payloads[request.operation],
        )


@pytest.fixture
def strategy_constraints() -> StrategyConstraints:
    return StrategyConstraints(
        pair="ETH/USDC",
        dex="uniswap_v3",
        max_position_usd=Decimal("100000"),
        max_slippage_bps=50,
        stop_loss_bps=200,
        take_profit_bps=500,
        ttl_seconds=3600,
        daily_trade_limit=10,
    )


def test_builder_builds_complete_context_from_provider_backed_fetchers(
    strategy_constraints: StrategyConstraints,
) -> None:
    market_provider = RecordingProvider(
        provider_name="market-primary",
        payloads={
            "market_trend": {
                "direction": "up",
                "confidence": "0.81",
                "timeframe_minutes": 240,
            },
            "capital_flow": {
                "net_inflow_usd": "2500000",
                "volume_24h_usd": "70000000",
                "whale_inflow_usd": "1800000",
                "retail_inflow_usd": "700000",
            },
        },
    )
    liquidity_provider = RecordingProvider(
        provider_name="liquidity-primary",
        payloads={
            "liquidity_depth": {
                "depth_2pct": "5500000",
                "tvl": "120000000",
            }
        },
    )
    onchain_provider = RecordingProvider(
        provider_name="rpc-primary",
        payloads={
            "onchain_flow": {
                "active_address_delta_24h": 150,
                "transaction_count_24h": 42000,
                "gas_price_gwei": "24.5",
            }
        },
    )
    risk_provider = RecordingProvider(
        provider_name="risk-primary",
        payloads={
            "risk_state": {
                "volatility_annualized": "0.62",
                "var_95_usd": "35000",
                "correlation_to_market": "0.74",
            }
        },
    )
    position_provider = RecordingProvider(
        provider_name="position-primary",
        payloads={
            "position_state": {
                "current_position_usd": "40000",
                "unrealized_pnl_usd": "1800",
                "entry_price_usd": "3120.5",
            }
        },
    )
    execution_provider = RecordingProvider(
        provider_name="execution-primary",
        payloads={
            "execution_state": {
                "daily_trades_executed": 2,
                "daily_volume_usd": "90000",
            }
        },
    )

    builder = DecisionContextBuilder(
        market_fetcher=AggregatedMarketFetcher(market_provider),
        liquidity_fetcher=AggregatedLiquidityFetcher(liquidity_provider),
        onchain_fetcher=AggregatedOnchainFetcher(onchain_provider),
        risk_fetcher=AggregatedRiskFetcher(risk_provider),
        position_fetcher=AggregatedPositionFetcher(position_provider),
        execution_fetcher=AggregatedExecutionFetcher(execution_provider),
    )

    context = asyncio.run(
        builder.build(
            strategy_constraints=strategy_constraints,
            context_id="ctx-provider-backed-001",
        )
    )

    assert context.market_trend.timeframe_minutes == 240
    assert context.capital_flow.net_inflow_usd == Decimal("2500000")
    assert context.liquidity_depth.depth_usd_2pct == Decimal("5500000")
    assert context.onchain_flow.gas_price_gwei == Decimal("24.5")
    assert context.risk_state.volatility_annualized == Decimal("0.62")
    assert context.position_state.entry_price_usd == Decimal("3120.5")
    assert context.execution_state.daily_trades_executed == 2


def test_market_fetcher_falls_back_on_invalid_primary_payload() -> None:
    primary = RecordingProvider(
        provider_name="market-primary",
        payloads={"market_trend": {"direction": "up"}},
    )
    fallback = RecordingProvider(
        provider_name="market-fallback",
        payloads={
            "market_trend": {
                "direction": "down",
                "confidence": "0.91",
                "timeframe_minutes": 120,
            }
        },
    )

    fetcher = AggregatedMarketFetcher(primary, fallback)
    trend = asyncio.run(fetcher.fetch_market_trend("ETH/USDC"))

    assert trend.direction.value == "down"
    assert trend.confidence_score == Decimal("0.91")
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1


def test_market_fetcher_raises_clear_error_when_payload_is_missing_fields() -> None:
    provider = RecordingProvider(
        provider_name="market-primary",
        payloads={"capital_flow": {"net_inflow_usd": "1"}},
    )

    fetcher = AggregatedMarketFetcher(provider)

    with pytest.raises(ProviderDomainError) as exc_info:
        asyncio.run(fetcher.fetch_capital_flow("ETH/USDC"))

    assert "capital_flow" in str(exc_info.value)
    assert "volume_24h_usd" in str(exc_info.value)


def test_onchain_fetcher_raises_clear_error_on_timeout() -> None:
    provider = RecordingProvider(
        provider_name="rpc-primary",
        errors={
            "onchain_flow": ProviderUpstreamError("upstream request failed after retries")
        },
    )

    fetcher = AggregatedOnchainFetcher(provider)

    with pytest.raises(ProviderDomainError) as exc_info:
        asyncio.run(fetcher.fetch_onchain_flow())

    assert "onchain flow" in str(exc_info.value).lower()
    assert exc_info.value.__cause__ is not None
