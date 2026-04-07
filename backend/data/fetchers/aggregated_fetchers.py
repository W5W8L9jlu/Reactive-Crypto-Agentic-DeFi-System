from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from backend.data.context_builder.models import (
    CapitalFlow,
    LiquidityDepth,
    MarketTrend,
    OnchainFlow,
    PositionState,
    RiskState,
    ExecutionState,
    TrendDirection,
)
from backend.data.providers._shared_http_client import (
    ProviderDomainError,
    ProviderRequest,
    ProviderUpstreamError,
)


class AggregatedMarketFetcher:
    """聚合市场数据 fetcher，屏蔽底层 provider 差异。

    职责：
    - 从多个 provider 获取市场趋势和资金流数据
    - 统一处理失败和降级
    - 输出趋势/资金流视角，不返回 tick 级数据
    """
    
    def __init__(self, primary_provider: Any, fallback_provider: Any | None = None) -> None:
        self._primary = primary_provider
        self._fallback = fallback_provider
    
    async def fetch_market_trend(self, pair: str) -> MarketTrend:
        """获取市场趋势（趋势视角，非 tick）。"""
        try:
            trend_data = await self._fetch_from_provider(
                self._primary, "market_trend", {"pair": pair}
            )
            return self._parse_market_trend(trend_data)
        except (ProviderUpstreamError, ProviderDomainError):
            if self._fallback is not None:
                trend_data = await self._fetch_from_provider(
                    self._fallback, "market_trend", {"pair": pair}
                )
                return self._parse_market_trend(trend_data)
            raise
    
    async def fetch_capital_flow(self, pair: str) -> CapitalFlow:
        """获取资金流数据（资金流视角）。"""
        try:
            flow_data = await self._fetch_from_provider(
                self._primary, "capital_flow", {"pair": pair}
            )
            return self._parse_capital_flow(flow_data)
        except (ProviderUpstreamError, ProviderDomainError):
            if self._fallback is not None:
                flow_data = await self._fetch_from_provider(
                    self._fallback, "capital_flow", {"pair": pair}
                )
                return self._parse_capital_flow(flow_data)
            raise
    
    async def _fetch_from_provider(
        self, provider: Any, operation: str, params: dict[str, Any]
    ) -> Any:
        """统一 provider 调用封装。"""
        request = ProviderRequest(operation=operation, params=params)
        response = await provider.fetch(request)
        return response.payload
    
    def _parse_market_trend(self, data: dict[str, Any]) -> MarketTrend:
        """解析市场趋势数据。"""
        _require_fields(data, "market_trend", "direction", "confidence", "timeframe_minutes")
        direction_str = data["direction"]
        return MarketTrend(
            direction=TrendDirection(direction_str),
            confidence_score=Decimal(str(data["confidence"])),
            timeframe_minutes=int(data["timeframe_minutes"]),
        )
    
    def _parse_capital_flow(self, data: dict[str, Any]) -> CapitalFlow:
        """解析资金流数据。"""
        _require_fields(
            data,
            "capital_flow",
            "net_inflow_usd",
            "volume_24h_usd",
            "whale_inflow_usd",
            "retail_inflow_usd",
        )
        return CapitalFlow(
            net_inflow_usd=Decimal(str(data["net_inflow_usd"])),
            volume_24h_usd=Decimal(str(data["volume_24h_usd"])),
            whale_inflow_usd=Decimal(str(data["whale_inflow_usd"])),
            retail_inflow_usd=Decimal(str(data["retail_inflow_usd"])),
        )


class AggregatedLiquidityFetcher:
    """聚合流动性数据 fetcher。"""
    
    def __init__(self, primary_provider: Any, fallback_provider: Any | None = None) -> None:
        self._primary = primary_provider
        self._fallback = fallback_provider
    
    async def fetch_liquidity_depth(self, pair: str, dex: str) -> LiquidityDepth:
        """获取流动性深度。"""
        try:
            data = await self._fetch_from_provider(
                self._primary, "liquidity_depth", {"pair": pair, "dex": dex}
            )
            return self._parse_liquidity_depth(pair, dex, data)
        except ProviderUpstreamError:
            if self._fallback is not None:
                data = await self._fetch_from_provider(
                    self._fallback, "liquidity_depth", {"pair": pair, "dex": dex}
                )
                return self._parse_liquidity_depth(pair, dex, data)
            raise
    
    async def _fetch_from_provider(
        self, provider: Any, operation: str, params: dict[str, Any]
    ) -> Any:
        request = ProviderRequest(operation=operation, params=params)
        response = await provider.fetch(request)
        return response.payload
    
    def _parse_liquidity_depth(
        self, pair: str, dex: str, data: dict[str, Any]
    ) -> LiquidityDepth:
        _require_fields(data, "liquidity_depth", "depth_2pct", "tvl")
        return LiquidityDepth(
            pair=pair,
            dex=dex,
            depth_usd_2pct=Decimal(str(data["depth_2pct"])),
            total_tvl_usd=Decimal(str(data["tvl"])),
        )


class AggregatedOnchainFetcher:
    """聚合链上数据 fetcher。"""
    
    def __init__(self, rpc_provider: Any) -> None:
        self._rpc = rpc_provider
    
    async def fetch_onchain_flow(self) -> OnchainFlow:
        """获取链上流数据。"""
        request = ProviderRequest(
            operation="onchain_flow",
            params={},
        )
        try:
            response = await self._rpc.fetch(request)
            return self._parse_onchain_flow(response.payload)
        except ProviderUpstreamError as exc:
            raise ProviderDomainError("Failed to fetch onchain flow from RPC") from exc

    def _parse_onchain_flow(self, data: dict[str, Any]) -> OnchainFlow:
        _require_fields(
            data,
            "onchain_flow",
            "active_address_delta_24h",
            "transaction_count_24h",
            "gas_price_gwei",
        )
        return OnchainFlow(
            active_address_delta_24h=int(data["active_address_delta_24h"]),
            transaction_count_24h=int(data["transaction_count_24h"]),
            gas_price_gwei=Decimal(str(data["gas_price_gwei"])),
        )


class AggregatedRiskFetcher:
    """聚合风险数据 fetcher。"""
    
    def __init__(self, primary_provider: Any) -> None:
        self._primary = primary_provider
    
    async def fetch_risk_state(self, pair: str) -> RiskState:
        """获取风险状态。"""
        data = await self._fetch_from_provider(self._primary, "risk_state", {"pair": pair})
        return self._parse_risk_state(data)

    async def _fetch_from_provider(
        self, provider: Any, operation: str, params: dict[str, Any]
    ) -> Any:
        request = ProviderRequest(operation=operation, params=params)
        response = await provider.fetch(request)
        return response.payload

    def _parse_risk_state(self, data: dict[str, Any]) -> RiskState:
        _require_fields(
            data,
            "risk_state",
            "volatility_annualized",
            "var_95_usd",
            "correlation_to_market",
        )
        return RiskState(
            volatility_annualized=Decimal(str(data["volatility_annualized"])),
            var_95_usd=Decimal(str(data["var_95_usd"])),
            correlation_to_market=Decimal(str(data["correlation_to_market"])),
        )


class AggregatedPositionFetcher:
    """聚合仓位数据 fetcher。"""
    
    def __init__(self, rpc_provider: Any) -> None:
        self._rpc = rpc_provider
    
    async def fetch_position_state(self, pair: str) -> PositionState:
        """获取仓位状态。"""
        request = ProviderRequest(operation="position_state", params={"pair": pair})
        response = await self._rpc.fetch(request)
        return self._parse_position_state(response.payload)

    def _parse_position_state(self, data: dict[str, Any]) -> PositionState:
        _require_fields(data, "position_state", "current_position_usd", "unrealized_pnl_usd")
        return PositionState(
            current_position_usd=Decimal(str(data["current_position_usd"])),
            unrealized_pnl_usd=Decimal(str(data["unrealized_pnl_usd"])),
            entry_price_usd=(
                Decimal(str(data["entry_price_usd"])) if "entry_price_usd" in data else None
            ),
        )


class AggregatedExecutionFetcher:
    """聚合执行状态 fetcher。"""

    def __init__(self, provider: Any) -> None:
        if provider is None:
            raise ValueError("Execution state provider is required")

        self._provider = provider

    async def fetch_execution_state(self) -> ExecutionState:
        """获取今日执行状态。"""
        request = ProviderRequest(operation="execution_state", params={})
        try:
            response = await self._provider.fetch(request)
        except ProviderUpstreamError as exc:
            raise ProviderDomainError("Failed to fetch execution state") from exc

        return self._parse_execution_state(response.payload)

    def _parse_execution_state(self, data: dict[str, Any]) -> ExecutionState:
        _require_fields(data, "execution_state", "daily_trades_executed", "daily_volume_usd")
        return ExecutionState(
            daily_trades_executed=int(data["daily_trades_executed"]),
            daily_volume_usd=Decimal(str(data["daily_volume_usd"])),
        )


def _require_fields(data: dict[str, Any], payload_name: str, *required_fields: str) -> None:
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise ProviderDomainError(
            f"{payload_name} payload is missing required fields: {', '.join(sorted(missing))}"
        )
