from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar

from backend.data.context_builder.models import (
    CapitalFlow,
    DecisionContext,
    ExecutionState,
    LiquidityDepth,
    MarketTrend,
    OnchainFlow,
    PositionState,
    RiskState,
    StrategyConstraints,
)


class ContextBuilderError(Exception):
    """Base class for context builder domain errors."""


class ProviderDataUnavailableError(ContextBuilderError):
    """Raised when required provider data is unavailable or fails to fetch."""


class DataQualityError(ContextBuilderError):
    """Raised when provider data quality does not meet requirements."""


class MarketDataFetcher(Protocol):
    async def fetch_market_trend(self, pair: str) -> MarketTrend:
        ...

    async def fetch_capital_flow(self, pair: str) -> CapitalFlow:
        ...


class LiquidityFetcher(Protocol):
    async def fetch_liquidity_depth(self, pair: str, dex: str) -> LiquidityDepth:
        ...


class OnchainFetcher(Protocol):
    async def fetch_onchain_flow(self) -> OnchainFlow:
        ...


class RiskFetcher(Protocol):
    async def fetch_risk_state(self, pair: str) -> RiskState:
        ...


class PositionFetcher(Protocol):
    async def fetch_position_state(self, pair: str) -> PositionState:
        ...


class ExecutionStateFetcher(Protocol):
    async def fetch_execution_state(self) -> ExecutionState:
        ...


_T = TypeVar("_T")


class DecisionContextBuilder:
    """Build a normalized decision context from provider-backed fetchers."""

    def __init__(
        self,
        market_fetcher: MarketDataFetcher,
        liquidity_fetcher: LiquidityFetcher,
        onchain_fetcher: OnchainFetcher,
        risk_fetcher: RiskFetcher,
        position_fetcher: PositionFetcher,
        execution_fetcher: ExecutionStateFetcher,
    ) -> None:
        self._market_fetcher = market_fetcher
        self._liquidity_fetcher = liquidity_fetcher
        self._onchain_fetcher = onchain_fetcher
        self._risk_fetcher = risk_fetcher
        self._position_fetcher = position_fetcher
        self._execution_fetcher = execution_fetcher

    async def build(
        self,
        strategy_constraints: StrategyConstraints,
        context_id: str,
    ) -> DecisionContext:
        pair = strategy_constraints.pair
        dex = strategy_constraints.dex

        market_trend = await self._fetch_required(
            "market trend",
            lambda: self._market_fetcher.fetch_market_trend(pair),
            pair,
        )
        capital_flow = await self._fetch_required(
            "capital flow",
            lambda: self._market_fetcher.fetch_capital_flow(pair),
            pair,
        )
        liquidity_depth = await self._fetch_required(
            "liquidity depth",
            lambda: self._liquidity_fetcher.fetch_liquidity_depth(pair, dex),
            f"{pair} on {dex}",
        )
        onchain_flow = await self._fetch_required(
            "onchain flow",
            self._onchain_fetcher.fetch_onchain_flow,
        )
        risk_state = await self._fetch_required(
            "risk state",
            lambda: self._risk_fetcher.fetch_risk_state(pair),
            pair,
        )
        position_state = await self._fetch_required(
            "position state",
            lambda: self._position_fetcher.fetch_position_state(pair),
            pair,
        )
        execution_state = await self._fetch_required(
            "execution state",
            self._execution_fetcher.fetch_execution_state,
        )

        self._validate_data_quality(
            market_trend=market_trend,
            liquidity_depth=liquidity_depth,
            risk_state=risk_state,
        )

        return DecisionContext(
            market_trend=market_trend,
            capital_flow=capital_flow,
            liquidity_depth=liquidity_depth,
            onchain_flow=onchain_flow,
            risk_state=risk_state,
            position_state=position_state,
            execution_state=execution_state,
            strategy_constraints=strategy_constraints,
            context_id=context_id,
            sources={
                "market_trend": "market_fetcher",
                "capital_flow": "market_fetcher",
                "liquidity_depth": "liquidity_fetcher",
                "onchain_flow": "onchain_fetcher",
                "risk_state": "risk_fetcher",
                "position_state": "position_fetcher",
                "execution_state": "execution_fetcher",
            },
        )

    async def _fetch_required(
        self,
        label: str,
        fetcher: Callable[[], Awaitable[_T]],
        subject: str | None = None,
    ) -> _T:
        try:
            return await fetcher()
        except Exception as exc:
            if subject is None:
                raise ProviderDataUnavailableError(
                    f"Failed to fetch {label}"
                ) from exc

            raise ProviderDataUnavailableError(
                f"Failed to fetch {label} for {subject}"
            ) from exc

    def _validate_data_quality(
        self,
        *,
        market_trend: MarketTrend,
        liquidity_depth: LiquidityDepth,
        risk_state: RiskState,
    ) -> None:
        if market_trend.timeframe_minutes < 1:
            raise DataQualityError("Invalid market trend timeframe")

        if liquidity_depth.depth_usd_2pct <= 0:
            raise DataQualityError("Invalid liquidity depth")

        if risk_state.volatility_annualized < 0:
            raise DataQualityError("Invalid volatility")


__all__ = [
    "DecisionContextBuilder",
    "ContextBuilderError",
    "ProviderDataUnavailableError",
    "DataQualityError",
    "MarketDataFetcher",
    "LiquidityFetcher",
    "OnchainFetcher",
    "RiskFetcher",
    "PositionFetcher",
    "ExecutionStateFetcher",
]
