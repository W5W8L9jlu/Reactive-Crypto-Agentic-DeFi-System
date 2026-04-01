from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal

import pytest

from backend.data.context_builder import (
    CapitalFlow,
    DataQualityError,
    DecisionContext,
    DecisionContextBuilder,
    ExecutionState,
    LiquidityDepth,
    MarketTrend,
    OnchainFlow,
    PositionState,
    ProviderDataUnavailableError,
    RiskState,
    StrategyConstraints,
    TrendDirection,
)


class MockMarketFetcher:
    async def fetch_market_trend(self, pair: str) -> MarketTrend:
        return MarketTrend(
            direction=TrendDirection.UP,
            confidence_score=Decimal("0.75"),
            timeframe_minutes=60,
        )

    async def fetch_capital_flow(self, pair: str) -> CapitalFlow:
        return CapitalFlow(
            net_inflow_usd=Decimal("1000000"),
            volume_24h_usd=Decimal("50000000"),
            whale_inflow_usd=Decimal("800000"),
            retail_inflow_usd=Decimal("200000"),
        )


class MockLiquidityFetcher:
    async def fetch_liquidity_depth(self, pair: str, dex: str) -> LiquidityDepth:
        return LiquidityDepth(
            pair=pair,
            dex=dex,
            depth_usd_2pct=Decimal("5000000"),
            total_tvl_usd=Decimal("100000000"),
        )


class MockOnchainFetcher:
    async def fetch_onchain_flow(self) -> OnchainFlow:
        return OnchainFlow(
            active_address_delta_24h=150,
            transaction_count_24h=50000,
            gas_price_gwei=Decimal("25.5"),
        )


class MockRiskFetcher:
    async def fetch_risk_state(self, pair: str) -> RiskState:
        return RiskState(
            volatility_annualized=Decimal("0.8"),
            var_95_usd=Decimal("50000"),
            correlation_to_market=Decimal("0.75"),
        )


class MockPositionFetcher:
    async def fetch_position_state(self, pair: str) -> PositionState:
        return PositionState(
            current_position_usd=Decimal("50000"),
            unrealized_pnl_usd=Decimal("2500"),
        )


class MockExecutionFetcher:
    async def fetch_execution_state(self) -> ExecutionState:
        return ExecutionState(
            daily_trades_executed=3,
            daily_volume_usd=Decimal("150000"),
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


@pytest.fixture
def builder() -> DecisionContextBuilder:
    return DecisionContextBuilder(
        market_fetcher=MockMarketFetcher(),
        liquidity_fetcher=MockLiquidityFetcher(),
        onchain_fetcher=MockOnchainFetcher(),
        risk_fetcher=MockRiskFetcher(),
        position_fetcher=MockPositionFetcher(),
        execution_fetcher=MockExecutionFetcher(),
    )


class TestContextCompleteness:
    def test_build_returns_complete_context(
        self, builder: DecisionContextBuilder, strategy_constraints: StrategyConstraints
    ) -> None:
        context = asyncio.run(
            builder.build(
                strategy_constraints=strategy_constraints,
                context_id="test-context-001",
            )
        )

        assert isinstance(context, DecisionContext)
        assert context.context_id == "test-context-001"
        assert isinstance(context.market_trend, MarketTrend)
        assert isinstance(context.capital_flow, CapitalFlow)
        assert isinstance(context.liquidity_depth, LiquidityDepth)
        assert isinstance(context.onchain_flow, OnchainFlow)
        assert isinstance(context.risk_state, RiskState)
        assert isinstance(context.position_state, PositionState)
        assert isinstance(context.execution_state, ExecutionState)
        assert isinstance(context.strategy_constraints, StrategyConstraints)
        assert context.strategy_constraints.pair == "ETH/USDC"
        assert context.strategy_constraints.dex == "uniswap_v3"

    def test_context_has_timestamp(
        self, builder: DecisionContextBuilder, strategy_constraints: StrategyConstraints
    ) -> None:
        context = asyncio.run(
            builder.build(
                strategy_constraints=strategy_constraints,
                context_id="test-context-002",
            )
        )

        assert isinstance(context.generated_at, datetime)
        assert context.generated_at.tzinfo is not None


class TestProviderFailureHandling:
    class FailingMarketFetcher:
        async def fetch_market_trend(self, pair: str) -> MarketTrend:
            raise Exception("Network timeout")

        async def fetch_capital_flow(self, pair: str) -> CapitalFlow:
            raise Exception("Network timeout")

    def test_market_fetcher_failure_raises_clear_error(
        self, strategy_constraints: StrategyConstraints
    ) -> None:
        builder = DecisionContextBuilder(
            market_fetcher=self.FailingMarketFetcher(),
            liquidity_fetcher=MockLiquidityFetcher(),
            onchain_fetcher=MockOnchainFetcher(),
            risk_fetcher=MockRiskFetcher(),
            position_fetcher=MockPositionFetcher(),
            execution_fetcher=MockExecutionFetcher(),
        )

        with pytest.raises(ProviderDataUnavailableError) as exc_info:
            asyncio.run(
                builder.build(
                    strategy_constraints=strategy_constraints,
                    context_id="test-fail-001",
                )
            )

        assert "market trend" in str(exc_info.value).lower()
        assert exc_info.value.__cause__ is not None


class TestDataQuality:
    class InvalidLiquidityFetcher:
        async def fetch_liquidity_depth(self, pair: str, dex: str) -> LiquidityDepth:
            return LiquidityDepth(
                pair=pair,
                dex=dex,
                depth_usd_2pct=Decimal("0"),
                total_tvl_usd=Decimal("0"),
            )

    def test_invalid_liquidity_depth_raises_data_quality_error(
        self, strategy_constraints: StrategyConstraints
    ) -> None:
        builder = DecisionContextBuilder(
            market_fetcher=MockMarketFetcher(),
            liquidity_fetcher=self.InvalidLiquidityFetcher(),
            onchain_fetcher=MockOnchainFetcher(),
            risk_fetcher=MockRiskFetcher(),
            position_fetcher=MockPositionFetcher(),
            execution_fetcher=MockExecutionFetcher(),
        )

        with pytest.raises(DataQualityError) as exc_info:
            asyncio.run(
                builder.build(
                    strategy_constraints=strategy_constraints,
                    context_id="test-quality-001",
                )
            )

        assert "liquidity" in str(exc_info.value).lower()


class TestModelValidation:
    def test_strategy_constraints_validation(self) -> None:
        constraints = StrategyConstraints(
            pair="ETH/USDC",
            dex="uniswap_v3",
            max_position_usd=Decimal("100000"),
            max_slippage_bps=50,
            stop_loss_bps=200,
            take_profit_bps=500,
            ttl_seconds=3600,
            daily_trade_limit=10,
        )
        assert constraints.max_position_usd == Decimal("100000")

    def test_negative_slippage_rejected(self) -> None:
        with pytest.raises(Exception):
            StrategyConstraints(
                pair="ETH/USDC",
                dex="uniswap_v3",
                max_position_usd=Decimal("100000"),
                max_slippage_bps=-1,
                stop_loss_bps=200,
                take_profit_bps=500,
                ttl_seconds=3600,
                daily_trade_limit=10,
            )

    def test_zero_max_position_rejected(self) -> None:
        with pytest.raises(Exception):
            StrategyConstraints(
                pair="ETH/USDC",
                dex="uniswap_v3",
                max_position_usd=Decimal("0"),
                max_slippage_bps=50,
                stop_loss_bps=200,
                take_profit_bps=500,
                ttl_seconds=3600,
                daily_trade_limit=10,
            )
