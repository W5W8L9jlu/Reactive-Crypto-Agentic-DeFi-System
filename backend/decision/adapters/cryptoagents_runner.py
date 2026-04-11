from __future__ import annotations

import importlib
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from backend.data.context_builder.models import DecisionContext

from .cryptoagents_adapter import CryptoAgentsOutputParseError


_REQUIRED_STRUCTURED_KEYS = frozenset(
    {
        "pair",
        "dex",
        "position_usd",
        "max_slippage_bps",
        "stop_loss_bps",
        "take_profit_bps",
        "entry_conditions",
        "ttl_seconds",
        "investment_thesis",
        "confidence_score",
        "agent_trace_steps",
    }
)

_RETRYABLE_RUNTIME_EXCEPTION_NAMES = frozenset(
    {
        "APIConnectionError",
        "APITimeoutError",
        "ConnectError",
        "ConnectTimeout",
        "ConnectionResetError",
        "InternalServerError",
        "RateLimitError",
        "ReadTimeout",
        "RemoteProtocolError",
        "TimeoutException",
        "WriteTimeout",
    }
)


class CryptoAgentsRunnerDependencyError(CryptoAgentsOutputParseError):
    """Raised when the production CryptoAgents graph dependency is unavailable."""


class CryptoAgentsStructuredOutputMissingError(CryptoAgentsOutputParseError):
    """Raised when graph output does not provide the required structured decision object."""


class CryptoAgentsGraphPort(Protocol):
    def propagate(self, company_name: str, trade_date: str) -> tuple[Any, Any]: ...


class ProductionCryptoAgentsRunner:
    """Production CryptoAgents runner implementation that calls the external graph."""

    def __init__(
        self,
        *,
        graph_factory: Any | None = None,
        as_of_date_provider: Any | None = None,
        runtime_retry_attempts: int | None = None,
        retry_backoff_seconds: float | None = None,
        sleep_fn: Any | None = None,
    ) -> None:
        self._graph_factory = graph_factory or _load_default_graph
        self._as_of_date_provider = as_of_date_provider or (lambda: datetime.now(tz=timezone.utc).date())
        self._runtime_retry_attempts = runtime_retry_attempts or _runtime_retry_attempts_from_env()
        self._retry_backoff_seconds = (
            retry_backoff_seconds if retry_backoff_seconds is not None else _retry_backoff_seconds_from_env()
        )
        self._sleep_fn = sleep_fn or time.sleep

    def run(self, context: DecisionContext) -> dict[str, Any]:
        symbol = _pair_to_symbol(context.strategy_constraints.pair)
        trade_date = self._as_of_date_provider()
        if not isinstance(trade_date, date):
            raise CryptoAgentsStructuredOutputMissingError("as_of_date_provider must return datetime.date")

        graph = self._graph_factory()
        last_runtime_error: Exception | None = None
        for attempt in range(1, self._runtime_retry_attempts + 1):
            try:
                propagated = graph.propagate(symbol, trade_date.isoformat())
                if isinstance(propagated, tuple) and len(propagated) == 2:
                    final_state, signal = propagated
                else:
                    final_state, signal = propagated, None
                return _extract_structured_output(final_state=final_state, signal=signal)
            except Exception as exc:  # pragma: no cover - branch validated by name-based tests
                if not _is_retryable_runtime_error(exc):
                    raise
                last_runtime_error = exc
                if attempt < self._runtime_retry_attempts and self._retry_backoff_seconds > 0:
                    self._sleep_fn(self._retry_backoff_seconds * attempt)
        raise CryptoAgentsRunnerDependencyError(
            "CryptoAgents graph runtime failed after retries. Check OPENAI_BASE_URL / proxy / network."
        ) from last_runtime_error


def _load_default_graph() -> CryptoAgentsGraphPort:
    _inject_cryptoagents_ref_path()
    try:
        module = importlib.import_module("cryptoagents.graph.trading_graph")
        config_module = importlib.import_module("cryptoagents.config")
    except Exception as exc:
        raise CryptoAgentsRunnerDependencyError(
            "CryptoAgents graph import failed. Install runtime deps and ensure external_refs/CryptoAgents is present."
        ) from exc

    trading_graph_cls = getattr(module, "TradingAgentsGraph", None)
    if trading_graph_cls is None:
        raise CryptoAgentsRunnerDependencyError("TradingAgentsGraph is missing in cryptoagents.graph.trading_graph")

    config = dict(getattr(config_module, "CRYPTO_CONFIG", {}))
    if "project_dir" not in config:
        config["project_dir"] = str(_repo_root())
    deep_model = os.environ.get("CRYPTOAGENTS_DEEP_THINK_LLM")
    quick_model = os.environ.get("CRYPTOAGENTS_QUICK_THINK_LLM")
    if deep_model:
        config["deep_think_llm"] = deep_model
    if quick_model:
        config["quick_think_llm"] = quick_model
    _apply_chat_openai_runtime_overrides(module)
    return trading_graph_cls(
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config=config,
    )


def _extract_structured_output(*, final_state: Any, signal: Any) -> dict[str, Any]:
    candidates: list[Any] = []
    if isinstance(final_state, dict):
        candidates.append(final_state.get("structured_decision"))
        candidates.append(final_state.get("portfolio_manager_output"))
        candidates.append(final_state.get("structured_output"))
        candidates.append(final_state)
    candidates.append(signal)

    for candidate in candidates:
        if isinstance(candidate, dict) and _REQUIRED_STRUCTURED_KEYS.issubset(candidate.keys()):
            return dict(candidate)

    raise CryptoAgentsStructuredOutputMissingError(
        "CryptoAgents graph output must include a structured decision dict with conditional intent fields."
    )


def _pair_to_symbol(pair: str) -> str:
    if "/" not in pair:
        raise CryptoAgentsStructuredOutputMissingError("decision_context.strategy_constraints.pair must be like BASE/QUOTE")
    base = pair.split("/", maxsplit=1)[0].strip().upper()
    if not base:
        raise CryptoAgentsStructuredOutputMissingError("cannot derive base symbol from pair")
    return base


def _inject_cryptoagents_ref_path() -> None:
    raw_path = os.environ.get("CRYPTOAGENTS_REF_PATH")
    ref_root = Path(raw_path) if raw_path else (_repo_root() / "external_refs" / "CryptoAgents")
    if not ref_root.exists():
        raise CryptoAgentsRunnerDependencyError(
            "CryptoAgents reference repo is missing. Expected path: external_refs/CryptoAgents"
        )
    ref_path = str(ref_root.resolve())
    if ref_path not in sys.path:
        sys.path.insert(0, ref_path)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _is_retryable_runtime_error(exc: Exception) -> bool:
    current: BaseException | None = exc
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if current.__class__.__name__ in _RETRYABLE_RUNTIME_EXCEPTION_NAMES:
            return True
        current = current.__cause__ or current.__context__
    return False


def _runtime_retry_attempts_from_env() -> int:
    raw = os.environ.get("CRYPTOAGENTS_RUNTIME_RETRY_ATTEMPTS", "2").strip()
    try:
        attempts = int(raw)
    except ValueError as exc:
        raise CryptoAgentsRunnerDependencyError(
            "CRYPTOAGENTS_RUNTIME_RETRY_ATTEMPTS must be a positive integer."
        ) from exc
    if attempts <= 0:
        raise CryptoAgentsRunnerDependencyError(
            "CRYPTOAGENTS_RUNTIME_RETRY_ATTEMPTS must be a positive integer."
        )
    return attempts


def _retry_backoff_seconds_from_env() -> float:
    raw = os.environ.get("CRYPTOAGENTS_RUNTIME_RETRY_BACKOFF_SECONDS", "2.0").strip()
    try:
        backoff_seconds = float(raw)
    except ValueError as exc:
        raise CryptoAgentsRunnerDependencyError(
            "CRYPTOAGENTS_RUNTIME_RETRY_BACKOFF_SECONDS must be a non-negative number."
        ) from exc
    if backoff_seconds < 0:
        raise CryptoAgentsRunnerDependencyError(
            "CRYPTOAGENTS_RUNTIME_RETRY_BACKOFF_SECONDS must be a non-negative number."
        )
    return backoff_seconds


def _apply_chat_openai_runtime_overrides(module: Any) -> None:
    llm_timeout_seconds = _optional_positive_float_env("CRYPTOAGENTS_LLM_TIMEOUT_SECONDS")
    llm_max_retries = _optional_non_negative_int_env("CRYPTOAGENTS_LLM_MAX_RETRIES")
    if llm_timeout_seconds is None and llm_max_retries is None:
        return
    original_chat_openai = getattr(module, "ChatOpenAI", None)
    if original_chat_openai is None:
        return

    def _chat_openai_factory(*args: Any, **kwargs: Any) -> Any:
        if llm_timeout_seconds is not None:
            kwargs.setdefault("timeout", llm_timeout_seconds)
        if llm_max_retries is not None:
            kwargs.setdefault("max_retries", llm_max_retries)
        return original_chat_openai(*args, **kwargs)

    module.ChatOpenAI = _chat_openai_factory


def _optional_positive_float_env(env_name: str) -> float | None:
    raw = os.environ.get(env_name)
    if raw is None or raw.strip() == "":
        return None
    try:
        value = float(raw.strip())
    except ValueError as exc:
        raise CryptoAgentsRunnerDependencyError(
            f"{env_name} must be a positive number when provided."
        ) from exc
    if value <= 0:
        raise CryptoAgentsRunnerDependencyError(
            f"{env_name} must be a positive number when provided."
        )
    return value


def _optional_non_negative_int_env(env_name: str) -> int | None:
    raw = os.environ.get(env_name)
    if raw is None or raw.strip() == "":
        return None
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise CryptoAgentsRunnerDependencyError(
            f"{env_name} must be a non-negative integer when provided."
        ) from exc
    if value < 0:
        raise CryptoAgentsRunnerDependencyError(
            f"{env_name} must be a non-negative integer when provided."
        )
    return value


__all__ = [
    "CryptoAgentsGraphPort",
    "CryptoAgentsRunnerDependencyError",
    "CryptoAgentsStructuredOutputMissingError",
    "ProductionCryptoAgentsRunner",
]
