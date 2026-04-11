from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal

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
from backend.decision.adapters import CryptoAgentsAdapter
from backend.decision.orchestrator.main_chain_service import MainChainRequest, MainChainService
from backend.execution.compiler.models import ChainStateSnapshot, RegistrationContext
from backend.reactive.adapters.models import InvestmentPositionState, ReactiveTrigger, ReactiveTriggerType
from backend.strategy import StrategyBoundaryService, StrategyTemplate
from backend.strategy.models import BpsRange
from backend.validation.pre_registration_check import RPCStateSnapshot


class _FakeDecisionAdapter:
    def build_decision_or_raise(self, *, decision_context: DecisionContext, strategy_template: StrategyTemplate):
        from backend.decision.schemas.cryptoagents_adapter import (
            AgentTrace,
            AgentTraceStep,
            CryptoAgentsDecision,
            DecisionMeta,
        )
        from backend.strategy.models import StrategyIntent, TradeIntent

        return CryptoAgentsDecision(
            strategy_intent=StrategyIntent(
                strategy_intent_id="si-ctx-001",
                template_id=strategy_template.template_id,
                template_version=strategy_template.version,
                execution_mode="conditional",
                projected_daily_trade_count=1,
            ),
            trade_intent=TradeIntent(
                trade_intent_id="ti-ctx-001",
                strategy_intent_id="si-ctx-001",
                pair=decision_context.strategy_constraints.pair,
                dex=decision_context.strategy_constraints.dex,
                position_usd=Decimal("1200"),
                max_slippage_bps=20,
                stop_loss_bps=90,
                take_profit_bps=250,
                entry_conditions=["price_below:3000"],
                ttl_seconds=3600,
            ),
            decision_meta=DecisionMeta(
                investment_thesis="等待触发后执行入场。",
                confidence_score=Decimal("0.78"),
                generated_at=datetime.now(tz=timezone.utc),
            ),
            agent_trace=AgentTrace(
                steps=(
                    AgentTraceStep(
                        agent="portfolio_manager",
                        summary="条件单通过",
                        timestamp=datetime.now(tz=timezone.utc),
                    ),
                )
            ),
        )


class _FakeCryptoAgentsRunner:
    def run(self, context: DecisionContext) -> dict[str, object]:
        return {
            "pair": context.strategy_constraints.pair,
            "dex": context.strategy_constraints.dex,
            "position_usd": "1200",
            "max_slippage_bps": 20,
            "stop_loss_bps": 90,
            "take_profit_bps": 250,
            "entry_conditions": ["price_below:3000"],
            "ttl_seconds": 3600,
            "projected_daily_trade_count": 1,
            "investment_thesis": "趋势仍在，回撤分批布局。",
            "confidence_score": "0.82",
            "agent_trace_steps": [
                {
                    "agent": "portfolio_manager",
                    "summary": "给出条件入场意图",
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }
            ],
        }


class _InMemoryContractGateway:
    def __init__(self) -> None:
        self._states: dict[str, InvestmentPositionState] = {}
        self._receipts: dict[str, dict[str, object]] = {}
        self._seq = 0
        self.last_registered_intent_id: str | None = None

    def register_investment_intent(self, *, call_inputs):
        intent_id = call_inputs.intent_id
        self._states[intent_id] = InvestmentPositionState.PENDING_ENTRY
        self.last_registered_intent_id = intent_id
        tx_hash = self._next_tx_hash()
        self._receipts[tx_hash] = {
            "tx_hash": tx_hash,
            "status": "success",
            "block_number": 20_000_001,
            "gas_used": 160000,
            "logs": [{"event": "InvestmentIntentRegistered", "intent_id": intent_id}],
        }
        return {"tx_hash": tx_hash}

    def get_position_state(self, *, intent_id: str) -> InvestmentPositionState:
        return self._states[intent_id]

    def execute_reactive_trigger(self, *, intent_id: str, trigger_type, observed_out: int):
        current = self._states[intent_id]
        if current is InvestmentPositionState.PENDING_ENTRY:
            self._states[intent_id] = InvestmentPositionState.ACTIVE_POSITION
            event = "InvestmentStateAdvanced:Entry"
        else:
            self._states[intent_id] = InvestmentPositionState.CLOSED
            event = "InvestmentStateAdvanced:Exit"
        tx_hash = self._next_tx_hash()
        self._receipts[tx_hash] = {
            "tx_hash": tx_hash,
            "status": "success",
            "block_number": 20_000_002,
            "gas_used": 190000,
            "logs": [
                {
                    "event": event,
                    "intent_id": intent_id,
                    "trigger_type": str(trigger_type),
                    "observed_out": observed_out,
                }
            ],
        }
        return {"tx_hash": tx_hash}

    def get_transaction_receipt(self, *, tx_hash: str):
        return self._receipts[tx_hash]

    def _next_tx_hash(self) -> str:
        self._seq += 1
        return f"0x{self._seq:064x}"


def _decision_context() -> DecisionContext:
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
        context_id="ctx-001",
    )


def _strategy_template() -> StrategyTemplate:
    return StrategyTemplate(
        template_id="tpl-eth-swing",
        version=1,
        auto_allowed_pairs=frozenset({"ETH/USDC"}),
        manual_allowed_pairs=frozenset(),
        auto_allowed_dexes=frozenset({"uniswap_v3"}),
        manual_allowed_dexes=frozenset(),
        auto_max_position_usd=Decimal("5000"),
        hard_max_position_usd=Decimal("10000"),
        auto_max_slippage_bps=30,
        hard_max_slippage_bps=100,
        auto_stop_loss_bps_range=BpsRange(min_bps=50, max_bps=200),
        manual_stop_loss_bps_range=BpsRange(min_bps=20, max_bps=300),
        auto_take_profit_bps_range=BpsRange(min_bps=100, max_bps=600),
        manual_take_profit_bps_range=BpsRange(min_bps=50, max_bps=1200),
        auto_daily_trade_limit=2,
        hard_daily_trade_limit=8,
        execution_mode="conditional",
    )


class MainChainServiceTestCase(unittest.TestCase):
    def test_run_main_chain_overrides_trigger_trade_intent_id_with_decision_output(self) -> None:
        gateway = _InMemoryContractGateway()
        service = MainChainService(
            decision_adapter=_FakeDecisionAdapter(),
            boundary_service=StrategyBoundaryService([_strategy_template()]),
            contract_gateway=gateway,
        )

        result = service.run_or_raise(
            MainChainRequest(
                decision_context=_decision_context(),
                strategy_template=_strategy_template(),
                rpc_state_snapshot=RPCStateSnapshot(
                    block_number=20_000_000,
                    block_timestamp=1_710_000_000,
                    input_token_usd_price=Decimal("1"),
                    input_token_reserve=Decimal("1000000"),
                    output_token_reserve=Decimal("500"),
                    wallet_input_balance=Decimal("10000"),
                    wallet_input_allowance=Decimal("10000"),
                    base_fee_gwei=20,
                    max_priority_fee_gwei=2,
                    max_gas_price_gwei=50,
                    estimated_gas_used=230000,
                    native_token_usd_price=Decimal("3000"),
                    expected_profit_usd=Decimal("200"),
                    ttl_buffer_seconds=60,
                ),
                chain_state=ChainStateSnapshot(
                    base_fee_gwei=20,
                    max_priority_fee_gwei=2,
                    block_number=20_000_000,
                    block_timestamp=1_710_000_000,
                    input_token_decimals=6,
                    output_token_decimals=18,
                    input_output_price=Decimal("0.0005"),
                    input_token_usd_price=Decimal("1"),
                ),
                registration_context=RegistrationContext(
                    intent_id="0x" + "1" * 64,
                    owner="0x0000000000000000000000000000000000000001",
                    input_token="0x0000000000000000000000000000000000000002",
                    output_token="0x0000000000000000000000000000000000000003",
                ),
                reactive_trigger=ReactiveTrigger(
                    trigger_type=ReactiveTriggerType.ENTRY,
                    intent_id="0x" + "1" * 64,
                    trade_intent_id="ti-request-mismatch",
                    metadata={"observed_out": 600_000_000_000_000_000},
                ),
                memo_brief="request trigger id mismatch should be normalized by decision output",
            )
        )

        self.assertEqual(result.decision.trade_intent.trade_intent_id, "ti-ctx-001")
        self.assertEqual(result.reactive_runtime_result.trade_intent_id, "ti-ctx-001")
        self.assertEqual(result.execution_record.status, "executed")

    def test_run_main_chain_with_cryptoagents_adapter_runner_path(self) -> None:
        gateway = _InMemoryContractGateway()
        service = MainChainService(
            decision_adapter=CryptoAgentsAdapter(runner=_FakeCryptoAgentsRunner()),
            boundary_service=StrategyBoundaryService([_strategy_template()]),
            contract_gateway=gateway,
        )

        result = service.run_or_raise(
            MainChainRequest(
                decision_context=_decision_context(),
                strategy_template=_strategy_template(),
                rpc_state_snapshot=RPCStateSnapshot(
                    block_number=20_000_000,
                    block_timestamp=1_710_000_000,
                    input_token_usd_price=Decimal("1"),
                    input_token_reserve=Decimal("1000000"),
                    output_token_reserve=Decimal("500"),
                    wallet_input_balance=Decimal("10000"),
                    wallet_input_allowance=Decimal("10000"),
                    base_fee_gwei=20,
                    max_priority_fee_gwei=2,
                    max_gas_price_gwei=50,
                    estimated_gas_used=230000,
                    native_token_usd_price=Decimal("3000"),
                    expected_profit_usd=Decimal("200"),
                    ttl_buffer_seconds=60,
                ),
                chain_state=ChainStateSnapshot(
                    base_fee_gwei=20,
                    max_priority_fee_gwei=2,
                    block_number=20_000_000,
                    block_timestamp=1_710_000_000,
                    input_token_decimals=6,
                    output_token_decimals=18,
                    input_output_price=Decimal("0.0005"),
                    input_token_usd_price=Decimal("1"),
                ),
                registration_context=RegistrationContext(
                    intent_id="0x" + "1" * 64,
                    owner="0x0000000000000000000000000000000000000001",
                    input_token="0x0000000000000000000000000000000000000002",
                    output_token="0x0000000000000000000000000000000000000003",
                ),
                reactive_trigger=ReactiveTrigger(
                    trigger_type=ReactiveTriggerType.ENTRY,
                    intent_id="0x" + "1" * 64,
                    trade_intent_id="ti-ctx-001",
                    metadata={"observed_out": 600_000_000_000_000_000},
                ),
                memo_brief="该意图在模板内，按条件单执行。",
            )
        )

        self.assertEqual(result.decision.trade_intent.pair, "ETH/USDC")
        self.assertEqual(result.boundary_result.boundary_decision.value, "auto_register")
        self.assertEqual(result.execution_record.status, "executed")

    def test_run_main_chain_happy_path_returns_export_bundle(self) -> None:
        gateway = _InMemoryContractGateway()
        service = MainChainService(
            decision_adapter=_FakeDecisionAdapter(),
            boundary_service=StrategyBoundaryService([_strategy_template()]),
            contract_gateway=gateway,
        )

        result = service.run_or_raise(
            MainChainRequest(
                decision_context=_decision_context(),
                strategy_template=_strategy_template(),
                rpc_state_snapshot=RPCStateSnapshot(
                    block_number=20_000_000,
                    block_timestamp=1_710_000_000,
                    input_token_usd_price=Decimal("1"),
                    input_token_reserve=Decimal("1000000"),
                    output_token_reserve=Decimal("500"),
                    wallet_input_balance=Decimal("10000"),
                    wallet_input_allowance=Decimal("10000"),
                    base_fee_gwei=20,
                    max_priority_fee_gwei=2,
                    max_gas_price_gwei=50,
                    estimated_gas_used=230000,
                    native_token_usd_price=Decimal("3000"),
                    expected_profit_usd=Decimal("200"),
                    ttl_buffer_seconds=60,
                ),
                chain_state=ChainStateSnapshot(
                    base_fee_gwei=20,
                    max_priority_fee_gwei=2,
                    block_number=20_000_000,
                    block_timestamp=1_710_000_000,
                    input_token_decimals=6,
                    output_token_decimals=18,
                    input_output_price=Decimal("0.0005"),
                    input_token_usd_price=Decimal("1"),
                ),
                registration_context=RegistrationContext(
                    intent_id="0x" + "1" * 64,
                    owner="0x0000000000000000000000000000000000000001",
                    input_token="0x0000000000000000000000000000000000000002",
                    output_token="0x0000000000000000000000000000000000000003",
                ),
                reactive_trigger=ReactiveTrigger(
                    trigger_type=ReactiveTriggerType.ENTRY,
                    intent_id="0x" + "1" * 64,
                    trade_intent_id="ti-ctx-001",
                    metadata={"observed_out": 600_000_000_000_000_000},
                ),
                memo_brief="该意图在模板内，按条件单执行。",
            )
        )

        self.assertEqual(result.boundary_result.boundary_decision.value, "auto_register")
        self.assertTrue(result.validation_result_pre.is_valid)
        self.assertTrue(result.validation_result_post.is_valid)
        self.assertTrue(result.pre_registration_result.is_allowed)
        self.assertEqual(gateway.last_registered_intent_id, "0x" + "1" * 64)
        self.assertTrue(result.reactive_runtime_result.is_executed)
        self.assertEqual(result.execution_record.status, "executed")
        machine_truth = json.loads(result.export_outputs.machine_truth_json)
        self.assertEqual(machine_truth["execution_record"]["status"], "executed")
        self.assertIn("# Investment Memo", result.export_outputs.investment_memo)


if __name__ == "__main__":
    unittest.main()
