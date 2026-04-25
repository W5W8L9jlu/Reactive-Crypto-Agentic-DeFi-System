"""Phase 1 real RPC / fork RPC gate for Uniswap V3 live reads.

Required env:
- PHASE1_GATE_NETWORK=sepolia|base_sepolia
- PHASE1_GATE_RPC_URL or SEPOLIA_RPC_URL or BASE_SEPOLIA_RPC_URL
- PHASE1_GATE_WALLET_ADDRESS
- PHASE1_GATE_INPUT_TOKEN_ADDRESS
- PHASE1_GATE_OUTPUT_TOKEN_ADDRESS
- PHASE1_GATE_POOL_ADDRESS
- PHASE1_GATE_ALLOWANCE_SPENDER_ADDRESS
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import os

import pytest

try:
    from web3 import Web3
except ImportError:  # pragma: no cover - environment dependent
    Web3 = None  # type: ignore[assignment]

from backend.data.context_builder import (
    CapitalFlow,
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
from backend.strategy.models import StrategyIntent, TradeIntent
from backend.validation.pre_registration_check import RPCStateSnapshot, run_pre_registration_check


ERC20_ABI = [
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


UNISWAP_V3_POOL_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]


Q96 = Decimal(1 << 96)

DEFAULT_PHASE1_GATE_WALLET_ADDRESS = "0xAf3fDAac647cE7ED56Ba8D98bC9bF77bb768594B"
DEFAULT_PHASE1_GATE_INPUT_TOKEN_ADDRESS = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
DEFAULT_PHASE1_GATE_OUTPUT_TOKEN_ADDRESS = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14"
DEFAULT_PHASE1_GATE_POOL_ADDRESS = "0x6Ce0896eAE6D4BD668fDe41BB784548fb8F59b50"
DEFAULT_PHASE1_GATE_ALLOWANCE_SPENDER_ADDRESS = "0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E"

BASE_SEPOLIA_GATE_WALLET_ADDRESS = DEFAULT_PHASE1_GATE_WALLET_ADDRESS
BASE_SEPOLIA_GATE_INPUT_TOKEN_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
BASE_SEPOLIA_GATE_OUTPUT_TOKEN_ADDRESS = "0x4200000000000000000000000000000000000006"
BASE_SEPOLIA_GATE_POOL_ADDRESS = "0x46880b404CD35c165EDdefF7421019F8dD25F4Ad"
BASE_SEPOLIA_GATE_ALLOWANCE_SPENDER_ADDRESS = "0x492E6456D9528771018DeB9E87ef7750EF184104"

DEFAULT_GATE_ADDRESSES = {
    "sepolia": {
        "PHASE1_GATE_WALLET_ADDRESS": DEFAULT_PHASE1_GATE_WALLET_ADDRESS,
        "PHASE1_GATE_INPUT_TOKEN_ADDRESS": DEFAULT_PHASE1_GATE_INPUT_TOKEN_ADDRESS,
        "PHASE1_GATE_OUTPUT_TOKEN_ADDRESS": DEFAULT_PHASE1_GATE_OUTPUT_TOKEN_ADDRESS,
        "PHASE1_GATE_POOL_ADDRESS": DEFAULT_PHASE1_GATE_POOL_ADDRESS,
        "PHASE1_GATE_ALLOWANCE_SPENDER_ADDRESS": DEFAULT_PHASE1_GATE_ALLOWANCE_SPENDER_ADDRESS,
    },
    "base_sepolia": {
        "PHASE1_GATE_WALLET_ADDRESS": BASE_SEPOLIA_GATE_WALLET_ADDRESS,
        "PHASE1_GATE_INPUT_TOKEN_ADDRESS": BASE_SEPOLIA_GATE_INPUT_TOKEN_ADDRESS,
        "PHASE1_GATE_OUTPUT_TOKEN_ADDRESS": BASE_SEPOLIA_GATE_OUTPUT_TOKEN_ADDRESS,
        "PHASE1_GATE_POOL_ADDRESS": BASE_SEPOLIA_GATE_POOL_ADDRESS,
        "PHASE1_GATE_ALLOWANCE_SPENDER_ADDRESS": BASE_SEPOLIA_GATE_ALLOWANCE_SPENDER_ADDRESS,
    },
}


@dataclass(frozen=True)
class GateConfig:
    rpc_url: str
    wallet_address: str
    input_token_address: str
    output_token_address: str
    pool_address: str
    allowance_spender_address: str
    position_usd: Decimal
    max_slippage_bps: int
    expected_profit_usd: Decimal
    input_token_usd_price: Decimal
    native_token_usd_price: Decimal
    max_gas_price_gwei: int
    max_priority_fee_gwei: int
    estimated_gas_used: int
    ttl_buffer_seconds: int

def _require_web3() -> type[Web3]:
    if Web3 is None:
        pytest.skip("web3 is required for the phase1 real RPC gate")
    return Web3


def _resolve_network() -> str:
    network = os.environ.get("PHASE1_GATE_NETWORK", "sepolia").strip().lower()
    if network not in DEFAULT_GATE_ADDRESSES:
        pytest.skip("PHASE1_GATE_NETWORK must be sepolia or base_sepolia")
    return network


def _require_rpc_url() -> str:
    rpc_url = os.environ.get("PHASE1_GATE_RPC_URL")
    if not rpc_url:
        network = _resolve_network()
        if network == "base_sepolia":
            rpc_url = os.environ.get("BASE_SEPOLIA_RPC_URL") or os.environ.get("SEPOLIA_RPC_URL")
        else:
            rpc_url = os.environ.get("SEPOLIA_RPC_URL") or os.environ.get("BASE_SEPOLIA_RPC_URL")
    if not rpc_url:
        pytest.skip("PHASE1_GATE_RPC_URL or SEPOLIA_RPC_URL or BASE_SEPOLIA_RPC_URL is required")
    return rpc_url


def _require_address(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        network = _resolve_network()
        default_value = DEFAULT_GATE_ADDRESSES[network].get(name)
        if default_value is not None:
            return default_value
        pytest.skip(f"{name} is required for the phase1 real RPC gate")
    return value


def _env_decimal(name: str, default: str) -> Decimal:
    raw = os.environ.get(name, default)
    return Decimal(raw)


def _env_int(name: str, default: str) -> int:
    raw = os.environ.get(name, default)
    return int(raw)


def _load_gate_config() -> GateConfig:
    _resolve_network()
    return GateConfig(
        rpc_url=_require_rpc_url(),
        wallet_address=_require_address("PHASE1_GATE_WALLET_ADDRESS"),
        input_token_address=_require_address("PHASE1_GATE_INPUT_TOKEN_ADDRESS"),
        output_token_address=_require_address("PHASE1_GATE_OUTPUT_TOKEN_ADDRESS"),
        pool_address=_require_address("PHASE1_GATE_POOL_ADDRESS"),
        allowance_spender_address=_require_address("PHASE1_GATE_ALLOWANCE_SPENDER_ADDRESS"),
        position_usd=_env_decimal("PHASE1_GATE_POSITION_USD", "200"),
        max_slippage_bps=_env_int("PHASE1_GATE_MAX_SLIPPAGE_BPS", "50"),
        expected_profit_usd=_env_decimal("PHASE1_GATE_EXPECTED_PROFIT_USD", "20"),
        input_token_usd_price=_env_decimal("PHASE1_GATE_INPUT_TOKEN_USD_PRICE", "1"),
        native_token_usd_price=_env_decimal("PHASE1_GATE_NATIVE_TOKEN_USD_PRICE", "3000"),
        max_gas_price_gwei=_env_int("PHASE1_GATE_MAX_GAS_PRICE_GWEI", "200"),
        max_priority_fee_gwei=_env_int("PHASE1_GATE_MAX_PRIORITY_FEE_GWEI", "2"),
        estimated_gas_used=_env_int("PHASE1_GATE_ESTIMATED_GAS_USED", "150000"),
        ttl_buffer_seconds=_env_int("PHASE1_GATE_TTL_BUFFER_SECONDS", "60"),
    )


def _erc20_contract(web3: Web3, token_address: str):
    return web3.eth.contract(address=web3.to_checksum_address(token_address), abi=ERC20_ABI)


def _v3_pool_contract(web3: Web3, pool_address: str):
    return web3.eth.contract(address=web3.to_checksum_address(pool_address), abi=UNISWAP_V3_POOL_ABI)


def _to_human_amount(raw_amount: int | Decimal, decimals: int) -> Decimal:
    return Decimal(raw_amount) / (Decimal(10) ** Decimal(decimals))


def _read_v3_pool_state(
    *,
    web3: Web3,
    pool_address: str,
    input_token_address: str,
    output_token_address: str,
    wallet_address: str,
    allowance_spender_address: str,
    input_token_usd_price: Decimal,
) -> dict[str, Decimal | int | str]:
    pool = _v3_pool_contract(web3, pool_address)
    token0 = web3.to_checksum_address(pool.functions.token0().call())
    token1 = web3.to_checksum_address(pool.functions.token1().call())

    input_token = web3.to_checksum_address(input_token_address)
    output_token = web3.to_checksum_address(output_token_address)
    token_set = {token0, token1}
    if input_token not in token_set or output_token not in token_set:
        raise RuntimeError(
            "configured input/output token addresses do not match the Uniswap V3 pool token pair"
        )

    slot0 = pool.functions.slot0().call()
    sqrt_price_x96 = int(slot0[0])
    liquidity = int(pool.functions.liquidity().call())
    if sqrt_price_x96 <= 0 or liquidity <= 0:
        raise RuntimeError("pool returned non-positive slot0/liquidity state")

    token0_contract = _erc20_contract(web3, token0)
    token1_contract = _erc20_contract(web3, token1)
    decimals0 = int(token0_contract.functions.decimals().call())
    decimals1 = int(token1_contract.functions.decimals().call())

    reserve0_raw = (Decimal(liquidity) * Q96) / Decimal(sqrt_price_x96)
    reserve1_raw = (Decimal(liquidity) * Decimal(sqrt_price_x96)) / Q96
    reserve0 = _to_human_amount(reserve0_raw, decimals0)
    reserve1 = _to_human_amount(reserve1_raw, decimals1)

    if input_token == token0:
        input_reserve = reserve0
        output_reserve = reserve1
        input_decimals = decimals0
    else:
        input_reserve = reserve1
        output_reserve = reserve0
        input_decimals = decimals1

    input_contract = _erc20_contract(web3, input_token)
    wallet_address_checksum = web3.to_checksum_address(wallet_address)
    allowance_spender_checksum = web3.to_checksum_address(allowance_spender_address)
    wallet_balance = _to_human_amount(
        int(input_contract.functions.balanceOf(wallet_address_checksum).call()),
        input_decimals,
    )
    wallet_allowance = _to_human_amount(
        int(
            input_contract.functions.allowance(
                wallet_address_checksum,
                allowance_spender_checksum,
            ).call()
        ),
        input_decimals,
    )

    if output_reserve <= 0:
        raise RuntimeError("pool returned a non-positive output reserve")

    output_token_price = input_token_usd_price * (input_reserve / output_reserve)
    input_token_usd = input_reserve * input_token_usd_price
    output_token_usd = output_reserve * output_token_price

    return {
        "token0": token0,
        "token1": token1,
        "input_token": input_token,
        "output_token": output_token,
        "input_token_reserve": input_reserve,
        "output_token_reserve": output_reserve,
        "wallet_balance": wallet_balance,
        "wallet_allowance": wallet_allowance,
        "depth_usd_2pct": min(input_token_usd, output_token_usd) * Decimal("0.02"),
        "total_tvl_usd": input_token_usd + output_token_usd,
    }


class _LiveMarketFetcher:
    def __init__(self, web3: Web3) -> None:
        self._web3 = web3

    async def fetch_market_trend(self, pair: str) -> MarketTrend:
        block_number = int(self._web3.eth.block_number)
        confidence = Decimal("0.50") + Decimal(block_number % 50) / Decimal("100")
        return MarketTrend(
            direction=TrendDirection.UNKNOWN,
            confidence_score=min(confidence, Decimal("0.99")),
            timeframe_minutes=60,
        )

    async def fetch_capital_flow(self, pair: str) -> CapitalFlow:
        gas_price_gwei = Decimal(int(self._web3.eth.gas_price)) / Decimal(10**9)
        block_number = Decimal(int(self._web3.eth.block_number))
        return CapitalFlow(
            net_inflow_usd=block_number,
            volume_24h_usd=block_number * Decimal("100"),
            whale_inflow_usd=gas_price_gwei,
            retail_inflow_usd=block_number + gas_price_gwei,
        )


class _LiveLiquidityFetcher:
    def __init__(self, web3: Web3, config: GateConfig) -> None:
        self._web3 = web3
        self._config = config

    async def fetch_liquidity_depth(self, pair: str, dex: str) -> LiquidityDepth:
        pool_state = _read_v3_pool_state(
            web3=self._web3,
            pool_address=self._config.pool_address,
            input_token_address=self._config.input_token_address,
            output_token_address=self._config.output_token_address,
            wallet_address=self._config.wallet_address,
            allowance_spender_address=self._config.allowance_spender_address,
            input_token_usd_price=self._config.input_token_usd_price,
        )
        return LiquidityDepth(
            pair=pair,
            dex=dex,
            depth_usd_2pct=pool_state["depth_usd_2pct"],
            total_tvl_usd=pool_state["total_tvl_usd"],
        )


class _LiveOnchainFetcher:
    def __init__(self, web3: Web3) -> None:
        self._web3 = web3

    async def fetch_onchain_flow(self) -> OnchainFlow:
        block = self._web3.eth.get_block("latest")
        gas_price_gwei = Decimal(int(self._web3.eth.gas_price)) / Decimal(10**9)
        transaction_count = len(block.get("transactions", []))
        return OnchainFlow(
            active_address_delta_24h=transaction_count,
            transaction_count_24h=transaction_count,
            gas_price_gwei=gas_price_gwei,
        )


class _LiveRiskFetcher:
    def __init__(self, web3: Web3) -> None:
        self._web3 = web3

    async def fetch_risk_state(self, pair: str) -> RiskState:
        gas_price_gwei = Decimal(int(self._web3.eth.gas_price)) / Decimal(10**9)
        return RiskState(
            volatility_annualized=gas_price_gwei / Decimal("100"),
            var_95_usd=gas_price_gwei * Decimal("10"),
            correlation_to_market=Decimal("0.50"),
        )


class _LivePositionFetcher:
    def __init__(self, web3: Web3, config: GateConfig) -> None:
        self._web3 = web3
        self._config = config

    async def fetch_position_state(self, pair: str) -> PositionState:
        pool_state = _read_v3_pool_state(
            web3=self._web3,
            pool_address=self._config.pool_address,
            input_token_address=self._config.input_token_address,
            output_token_address=self._config.output_token_address,
            wallet_address=self._config.wallet_address,
            allowance_spender_address=self._config.allowance_spender_address,
            input_token_usd_price=self._config.input_token_usd_price,
        )
        return PositionState(
            current_position_usd=pool_state["wallet_balance"] * self._config.input_token_usd_price,
            unrealized_pnl_usd=Decimal("0"),
        )


class _LiveExecutionFetcher:
    def __init__(self, web3: Web3) -> None:
        self._web3 = web3

    async def fetch_execution_state(self) -> ExecutionState:
        block_number = int(self._web3.eth.block_number)
        return ExecutionState(
            daily_trades_executed=block_number % 7,
            daily_volume_usd=Decimal(block_number) * Decimal("10"),
        )


def _build_context_builder(web3: Web3, config: GateConfig) -> DecisionContextBuilder:
    return DecisionContextBuilder(
        market_fetcher=_LiveMarketFetcher(web3),
        liquidity_fetcher=_LiveLiquidityFetcher(web3, config),
        onchain_fetcher=_LiveOnchainFetcher(web3),
        risk_fetcher=_LiveRiskFetcher(web3),
        position_fetcher=_LivePositionFetcher(web3, config),
        execution_fetcher=_LiveExecutionFetcher(web3),
    )


def _build_strategy_intent() -> StrategyIntent:
    suffix = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    return StrategyIntent(
        strategy_intent_id=f"si-phase1-gate-{suffix}",
        template_id="phase1-gate-template",
        template_version=1,
    )


def _build_trade_intent(strategy_intent_id: str, config: GateConfig) -> TradeIntent:
    suffix = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    return TradeIntent(
        trade_intent_id=f"ti-phase1-gate-{suffix}",
        strategy_intent_id=strategy_intent_id,
        pair="ETH/USDC",
        dex="uniswap_v3",
        position_usd=config.position_usd,
        max_slippage_bps=config.max_slippage_bps,
        stop_loss_bps=100,
        take_profit_bps=250,
        entry_conditions=["price_below:3000"],
        ttl_seconds=3600,
    )


def _build_rpc_snapshot(
    *,
    web3: Web3,
    config: GateConfig,
    pool_state: dict[str, Decimal | int | str],
) -> RPCStateSnapshot:
    latest_block = web3.eth.get_block("latest")
    base_fee_wei = int(latest_block.get("baseFeePerGas") or 0)

    return RPCStateSnapshot(
        block_number=int(latest_block["number"]),
        block_timestamp=int(latest_block["timestamp"]),
        input_token_usd_price=config.input_token_usd_price,
        input_token_reserve=pool_state["input_token_reserve"],
        output_token_reserve=pool_state["output_token_reserve"],
        wallet_input_balance=pool_state["wallet_balance"],
        wallet_input_allowance=pool_state["wallet_allowance"],
        base_fee_gwei=max(0, int(Decimal(base_fee_wei) / Decimal(10**9))),
        max_priority_fee_gwei=config.max_priority_fee_gwei,
        max_gas_price_gwei=config.max_gas_price_gwei,
        estimated_gas_used=config.estimated_gas_used,
        native_token_usd_price=config.native_token_usd_price,
        expected_profit_usd=config.expected_profit_usd,
        ttl_buffer_seconds=config.ttl_buffer_seconds,
    )


def _run(coro):
    return asyncio.run(coro)


def test_phase1_real_rpc_gate_supports_uniswap_v3_live_reads() -> None:
    web3_cls = _require_web3()
    config = _load_gate_config()
    web3 = web3_cls(web3_cls.HTTPProvider(config.rpc_url))
    if not web3.is_connected():
        raise RuntimeError(f"rpc not connected: {config.rpc_url}")

    pool_state = _read_v3_pool_state(
        web3=web3,
        pool_address=config.pool_address,
        input_token_address=config.input_token_address,
        output_token_address=config.output_token_address,
        wallet_address=config.wallet_address,
        allowance_spender_address=config.allowance_spender_address,
        input_token_usd_price=config.input_token_usd_price,
    )
    assert pool_state["input_token"] == config.input_token_address
    assert pool_state["output_token"] == config.output_token_address

    strategy_intent = _build_strategy_intent()
    trade_intent = _build_trade_intent(strategy_intent.strategy_intent_id, config)
    strategy_constraints = StrategyConstraints(
        pair=trade_intent.pair,
        dex=trade_intent.dex,
        max_position_usd=Decimal("5000"),
        max_slippage_bps=trade_intent.max_slippage_bps,
        stop_loss_bps=trade_intent.stop_loss_bps,
        take_profit_bps=trade_intent.take_profit_bps,
        ttl_seconds=trade_intent.ttl_seconds,
        daily_trade_limit=2,
    )

    context = _run(
        _build_context_builder(web3, config).build(
            strategy_constraints=strategy_constraints,
            context_id="phase1-real-rpc-gate",
        )
    )
    assert context.context_id == "phase1-real-rpc-gate"
    assert context.strategy_constraints.dex == "uniswap_v3"
    assert context.sources == {
        "market_trend": "market_fetcher",
        "capital_flow": "market_fetcher",
        "liquidity_depth": "liquidity_fetcher",
        "onchain_flow": "onchain_fetcher",
        "risk_state": "risk_fetcher",
        "position_state": "position_fetcher",
        "execution_state": "execution_fetcher",
    }
    assert context.liquidity_depth.total_tvl_usd > 0
    assert context.liquidity_depth.depth_usd_2pct > 0
    assert context.onchain_flow.gas_price_gwei > 0
    assert context.position_state.current_position_usd >= 0

    snapshot = _build_rpc_snapshot(web3=web3, config=config, pool_state=pool_state)
    result = run_pre_registration_check(
        strategy_intent=strategy_intent,
        trade_intent=trade_intent,
        rpc_state_snapshot=snapshot,
    )

    required_input_amount = trade_intent.position_usd / snapshot.input_token_usd_price
    if result.observations is not None:
        assert result.observations.required_input_amount == required_input_amount
    if snapshot.wallet_input_balance < required_input_amount:
        assert result.is_allowed is False
        assert result.abort_reason is not None
        assert result.abort_reason.code == "InsufficientBalanceError"
        assert "wallet_input_balance" in result.abort_reason.message
    elif snapshot.wallet_input_allowance < required_input_amount:
        assert result.is_allowed is False
        assert result.abort_reason is not None
        assert result.abort_reason.code == "InsufficientAllowanceError"
        assert "wallet_input_allowance" in result.abort_reason.message
    else:
        assert result.is_allowed is True
        assert result.abort_reason is None

    assert snapshot.input_token_reserve == pool_state["input_token_reserve"]
    assert snapshot.output_token_reserve == pool_state["output_token_reserve"]
    assert snapshot.wallet_input_balance == pool_state["wallet_balance"]
    assert snapshot.wallet_input_allowance == pool_state["wallet_allowance"]
