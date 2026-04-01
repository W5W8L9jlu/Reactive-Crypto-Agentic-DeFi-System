"""
Execution Compiler 异常体系。

所有异常必须携带足够的上下文，便于上层统一处理。
失败快速抛异常，不做局部吞异常。
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any


class ExecutionCompilerError(Exception):
    """Execution Compiler 基础异常。"""
    
    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class CompilationInputError(ExecutionCompilerError):
    """输入验证失败（输入数据不符合预期）。"""
    pass


class ChainStateError(ExecutionCompilerError):
    """链状态不可用或已过期。"""
    pass


class ConstraintViolationError(ExecutionCompilerError):
    """约束计算结果违反 invariant。"""
    pass


class TokenPrecisionError(ExecutionCompilerError):
    """Token 精度处理失败。"""
    pass


class CompilationConfigError(ExecutionCompilerError):
    """编译配置错误。"""
    pass
