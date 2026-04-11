from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

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
    TrendDirection,
)
from backend.decision.adapters.cryptoagents_runner import (
    CryptoAgentsRunnerDependencyError,
    CryptoAgentsStructuredOutputMissingError,
    ProductionCryptoAgentsRunner,
)


def _context() -> DecisionContext:
    return DecisionContext(
        market_trend=MarketTrend(
            direction=TrendDirection.UP,
            confidence_score=Decimal("0.72"),
            timeframe_minutes=240,
        ),
        capital_flow=CapitalFlow(
            net_inflow_usd=Decimal("1500000"),
            volume_24h_usd=Decimal("53000000"),
            whale_inflow_usd=Decimal("500000"),
            retail_inflow_usd=Decimal("1000000"),
        ),
        liquidity_depth=LiquidityDepth(
            pair="ETH/USDC",
            dex="uniswap_v3",
            depth_usd_2pct=Decimal("30000000"),
            total_tvl_usd=Decimal("800000000"),
        ),
        onchain_flow=OnchainFlow(
            active_address_delta_24h=2800,
            transaction_count_24h=1220000,
            gas_price_gwei=Decimal("18.3"),
        ),
        risk_state=RiskState(
            volatility_annualized=Decimal("0.44"),
            var_95_usd=Decimal("2200"),
            correlation_to_market=Decimal("0.81"),
        ),
        position_state=PositionState(
            current_position_usd=Decimal("0"),
            unrealized_pnl_usd=Decimal("0"),
        ),
        execution_state=ExecutionState(
            daily_trades_executed=0,
            daily_volume_usd=Decimal("0"),
        ),
        strategy_constraints=StrategyConstraints(
            pair="ETH/USDC",
            dex="uniswap_v3",
            max_position_usd=Decimal("5000"),
            max_slippage_bps=30,
            stop_loss_bps=150,
            take_profit_bps=300,
            ttl_seconds=7200,
            daily_trade_limit=2,
        ),
        context_id="ctx-graph-runtime-smoke",
    )


def main() -> int:
    runner = ProductionCryptoAgentsRunner()
    try:
        output = runner.run(_context())
    except (CryptoAgentsRunnerDependencyError, CryptoAgentsStructuredOutputMissingError) as exc:
        print(f"CryptoAgents graph runtime check: FAILED ({exc})")
        return 1
    print("CryptoAgents graph runtime check: OK")
    print(f"output keys: {sorted(output.keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
