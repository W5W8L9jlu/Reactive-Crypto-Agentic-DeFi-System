from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, model_validator


class RegisterPayload(BaseModel):
    """
    InvestmentIntent 注册 payload，直接对应合约的 registerInvestmentIntent 参数。
    
    注意：AI 层不生成 calldata，此 payload 为结构化数据，由调用层编码。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    # 身份与资产
    intent_id: str  # bytes32 的 hex 表示
    owner: str  # address
    input_token: str  # address
    output_token: str  # address
    planned_entry_size: int  # uint256, 原始 token 数量（已考虑精度）

    # 入场绝对约束（注册时固化）
    entry_amount_out_minimum: int  # uint256, entryMinOut
    entry_valid_until: int  # uint256, Unix timestamp
    max_gas_price_gwei: int  # uint256, 以 Gwei 为单位的 max gas price

    # 出场约束（以 BPS 表示的相对 slippage，触发时应用）
    stop_loss_slippage_bps: int  # uint256, 相对于入场实际 output 的 slippage
    take_profit_slippage_bps: int  # uint256, 相对于入场实际 output 的 slippage

    # 出场 floor 约束（绝对值，由合约计算）
    exit_min_out_floor: int  # uint256, 合约计算的最低出场 output


class ExecutionHardConstraints(BaseModel):
    """
    执行硬约束，与 validation 层的 ExecutionHardConstraints 对齐。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_slippage_bps: int = Field(ge=0)
    ttl_seconds: PositiveInt
    stop_loss_bps: int = Field(ge=0)
    take_profit_bps: int = Field(ge=0)


class ExecutionPlan(BaseModel):
    """
    注册时编译产物，包含 register payload 与链上硬约束参数。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    trade_intent_id: str
    register_payload: RegisterPayload
    hard_constraints: ExecutionHardConstraints

    # 编译元数据
    compiled_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    compiler_version: str = Field(default="1.0.0")


class ChainStateSnapshot(BaseModel):
    """
    注册时链上状态快照。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    # Gas 状态
    base_fee_gwei: int = Field(ge=0)  # 当前 base fee in Gwei
    max_priority_fee_gwei: int = Field(ge=0)  # 建议 priority fee in Gwei

    # 区块状态
    block_number: PositiveInt
    block_timestamp: int  # Unix timestamp

    # Token 价格/储备（用于计算 minOut）
    input_token_decimals: int = Field(ge=0, le=18)
    output_token_decimals: int = Field(ge=0, le=18)
    input_output_price: Decimal  # 1 input token = X output tokens


class CompilerConfig(BaseModel):
    """
    ExecutionCompiler 配置参数。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    # Gas 配置
    gas_buffer_multiplier: Decimal = Field(default=Decimal("1.2"), gt=1)  # base fee 缓冲倍数
    max_gas_price_cap_gwei: int = Field(default=500, ge=0)  # hard cap

    # TTL 配置（在 trade intent ttl 基础上减去 buffer）
    ttl_buffer_seconds: int = Field(default=60, ge=0)

    # minOut 计算配置
    slippage_tolerance_buffer_bps: int = Field(default=10, ge=0)  # 在 max_slippage 上加 buffer


class CompilationContext(BaseModel):
    """
    编译上下文，聚合所有编译所需输入。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy_intent: "StrategyIntent"
    trade_intent: "TradeIntent"
    chain_state: ChainStateSnapshot
    config: CompilerConfig = Field(default_factory=CompilerConfig)
