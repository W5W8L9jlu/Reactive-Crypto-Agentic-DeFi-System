from __future__ import annotations

import asyncio
import os
from decimal import Decimal

import pytest

from backend.data.context_builder import (
    CapitalFlow,
    DecisionContext,
    DecisionContextBuilder,
    ExecutionState,
    LiquidityDepth,
    MarketTrend,
    OnchainFlow,
    PositionState,
    RiskState,
    StrategyConstraints,
    TrendDirection,
)
from backend.data.providers._shared_http_client import ProviderRequest, RetryPolicy
from backend.data.providers.rpc_provider import RPCProvider


def _run(coro):
    return asyncio.run(coro)


def _require_rpc_url() -> str:
    rpc_url = os.environ.get("SEPOLIA_RPC_URL") or os.environ.get("BASE_SEPOLIA_RPC_URL")
    if not rpc_url:
        pytest.skip("SEPOLIA_RPC_URL or BASE_SEPOLIA_RPC_URL is required for live context integration")
    return rpc_url


def _retry_policy() -> RetryPolicy:
    return RetryPolicy(
        max_attempts=2,
        initial_backoff_seconds=0,
        max_backoff_seconds=0,
        backoff_multiplier=1,
    )


class _LiveMarketFetcher:
    def __init__(self, rpc_provider: RPCProvider) -> None:
        self._rpc_provider = rpc_provider

    async def fetch_market_trend(self, pair: str) -> MarketTrend:
        block_number = await self._rpc_provider.fetch(
            ProviderRequest(operation="eth_blockNumber", params={"params": []})
        )
        block_value = int(block_number.payload, 16)
        confidence = Decimal(str(min(max((block_value % 100) / 100, 0.5), 0.99)))
        return MarketTrend(
            direction=TrendDirection.UNKNOWN,
            confidence_score=confidence,
            timeframe_minutes=60,
        )

    async def fetch_capital_flow(self, pair: str) -> CapitalFlow:
        gas_price = await self._rpc_provider.fetch(
            ProviderRequest(operation="eth_gasPrice", params={"params": []})
        )
        block_number = await self._rpc_provider.fetch(
            ProviderRequest(operation="eth_blockNumber", params={"params": []})
        )
        gas_value = Decimal(int(gas_price.payload, 16))
        block_value = Decimal(int(block_number.payload, 16))
        return CapitalFlow(
            net_inflow_usd=block_value,
            volume_24h_usd=block_value * Decimal("100"),
            whale_inflow_usd=gas_value,
            retail_inflow_usd=block_value + gas_value,
        )


class _LiveLiquidityFetcher:
    def __init__(self, rpc_provider: RPCProvider) -> None:
        self._rpc_provider = rpc_provider

    async def fetch_liquidity_depth(self, pair: str, dex: str) -> LiquidityDepth:
        block_number = await self._rpc_provider.fetch(
            ProviderRequest(
                operation="eth_getBlockByNumber",
                params={"params": ["latest", False]},
            )
        )
        block_value = int(block_number.payload["number"], 16)
        return LiquidityDepth(
            pair=pair,
            dex=dex,
            depth_usd_2pct=Decimal(block_value % 1_000 + 1),
            total_tvl_usd=Decimal(block_value % 100_000 + 10_000),
        )


class _LiveOnchainFetcher:
    def __init__(self, rpc_provider: RPCProvider) -> None:
        self._rpc_provider = rpc_provider

    async def fetch_onchain_flow(self) -> OnchainFlow:
        block = await self._rpc_provider.fetch(
            ProviderRequest(
                operation="eth_getBlockByNumber",
                params={"params": ["latest", False]},
            )
        )
        gas_price = await self._rpc_provider.fetch(
            ProviderRequest(operation="eth_gasPrice", params={"params": []})
        )
        transaction_count = len(block.payload.get("transactions", []))
        return OnchainFlow(
            active_address_delta_24h=transaction_count,
            transaction_count_24h=transaction_count,
            gas_price_gwei=Decimal(int(gas_price.payload, 16)) / Decimal(10**9),
        )


class _LiveRiskFetcher:
    def __init__(self, rpc_provider: RPCProvider) -> None:
        self._rpc_provider = rpc_provider

    async def fetch_risk_state(self, pair: str) -> RiskState:
        gas_price = await self._rpc_provider.fetch(
            ProviderRequest(operation="eth_gasPrice", params={"params": []})
        )
        gas_value = Decimal(int(gas_price.payload, 16)) / Decimal(10**9)
        return RiskState(
            volatility_annualized=gas_value / Decimal("100"),
            var_95_usd=gas_value * Decimal("10"),
            correlation_to_market=Decimal("0.50"),
        )


class _LivePositionFetcher:
    def __init__(self, rpc_provider: RPCProvider) -> None:
        self._rpc_provider = rpc_provider

    async def fetch_position_state(self, pair: str) -> PositionState:
        balance = await self._rpc_provider.fetch(
            ProviderRequest(
                operation="eth_getBalance",
                params={"params": ["0x0000000000000000000000000000000000000000", "latest"]},
            )
        )
        balance_wei = Decimal(int(balance.payload, 16))
        return PositionState(
            current_position_usd=balance_wei / Decimal(10**18),
            unrealized_pnl_usd=Decimal("0"),
        )


class _LiveExecutionFetcher:
    def __init__(self, rpc_provider: RPCProvider) -> None:
        self._rpc_provider = rpc_provider

    async def fetch_execution_state(self) -> ExecutionState:
        block_number = await self._rpc_provider.fetch(
            ProviderRequest(operation="eth_blockNumber", params={"params": []})
        )
        block_value = int(block_number.payload, 16)
        return ExecutionState(
            daily_trades_executed=block_value % 7,
            daily_volume_usd=Decimal(block_value) * Decimal("10"),
        )


def test_live_context_builder_uses_real_rpc_backed_fetchers():
    rpc_url = _require_rpc_url()
    rpc_provider = RPCProvider(rpc_url, retry_policy=_retry_policy())
    builder = DecisionContextBuilder(
        market_fetcher=_LiveMarketFetcher(rpc_provider),
        liquidity_fetcher=_LiveLiquidityFetcher(rpc_provider),
        onchain_fetcher=_LiveOnchainFetcher(rpc_provider),
        risk_fetcher=_LiveRiskFetcher(rpc_provider),
        position_fetcher=_LivePositionFetcher(rpc_provider),
        execution_fetcher=_LiveExecutionFetcher(rpc_provider),
    )
    strategy_constraints = StrategyConstraints(
        pair="ETH/USDC",
        dex="uniswap_v3",
        max_position_usd=Decimal("5000"),
        max_slippage_bps=30,
        stop_loss_bps=150,
        take_profit_bps=300,
        ttl_seconds=7200,
        daily_trade_limit=2,
    )

    context = _run(
        builder.build(
            strategy_constraints=strategy_constraints,
            context_id="live-context-smoke",
        )
    )

    assert isinstance(context, DecisionContext)
    assert context.context_id == "live-context-smoke"
    assert context.sources == {
        "market_trend": "market_fetcher",
        "capital_flow": "market_fetcher",
        "liquidity_depth": "liquidity_fetcher",
        "onchain_flow": "onchain_fetcher",
        "risk_state": "risk_fetcher",
        "position_state": "position_fetcher",
        "execution_state": "execution_fetcher",
    }
    assert context.market_trend.direction is TrendDirection.UNKNOWN
    assert context.market_trend.confidence_score >= Decimal("0.5")
    assert context.liquidity_depth.depth_usd_2pct > 0
    assert context.onchain_flow.gas_price_gwei > 0
    assert context.risk_state.volatility_annualized >= 0
    assert context.position_state.current_position_usd >= 0
    assert context.execution_state.daily_trades_executed >= 0
