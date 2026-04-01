"""
Execution Layer 异常体系。

缺规范时显式抛错，不做静默 fallback。
"""
from __future__ import annotations

from typing import Any


class ExecutionLayerError(Exception):
    """Execution Layer 基础异常。"""

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class RuntimeTriggerError(ExecutionLayerError):
    """Reactive trigger 与执行计划不一致。"""


class ExecutionPlanError(ExecutionLayerError):
    """已编译执行计划缺少 execution layer 所需字段。"""


class RuntimeGateError(ExecutionLayerError):
    """运行时门禁未通过，不允许发起链上调用。"""


class ReceiptConsistencyError(ExecutionLayerError):
    """链上执行返回的回执不满足 ExecutionRecord 建模要求。"""


class ExecutionAdapterError(ExecutionLayerError):
    """链上执行适配器接口不完整或不可调用。"""
