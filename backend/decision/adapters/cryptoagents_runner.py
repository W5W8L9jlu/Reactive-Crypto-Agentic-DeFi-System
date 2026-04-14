from __future__ import annotations

import importlib
import inspect
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from backend.data.context_builder.models import DecisionContext

from .cryptoagents_adapter import CryptoAgentsOutputParseError
from .cryptoagents_projector import (
    CryptoAgentsProjectorPort,
    DefaultCryptoAgentsProjector,
)


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
        "projected_daily_trade_count",
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

_VERIFIED_RELAY_BASE_URLS = frozenset(
    {
        "https://api.ofox.ai",
        "https://api.ofox.ai/v1",
        "https://codex.ai02.cn",
        "https://codex.ai02.cn/v1",
    }
)

_DEFAULT_RELAY_EMBEDDING_MODEL = "openai/text-embedding-3-small"


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
        projector: CryptoAgentsProjectorPort | None = None,
    ) -> None:
        self._graph_factory = graph_factory or _load_default_graph
        self._as_of_date_provider = as_of_date_provider or (lambda: datetime.now(tz=timezone.utc).date())
        self._runtime_retry_attempts = runtime_retry_attempts or _runtime_retry_attempts_from_env()
        self._retry_backoff_seconds = (
            retry_backoff_seconds if retry_backoff_seconds is not None else _retry_backoff_seconds_from_env()
        )
        self._sleep_fn = sleep_fn or time.sleep
        self._projector = projector or DefaultCryptoAgentsProjector()

    def run(self, context: DecisionContext) -> dict[str, Any]:
        symbol = _pair_to_symbol(context.strategy_constraints.pair)
        trade_date = self._as_of_date_provider()
        if not isinstance(trade_date, date):
            raise CryptoAgentsStructuredOutputMissingError("as_of_date_provider must return datetime.date")

        graph = self._graph_factory()
        serialized_context = _serialize_decision_context(context)
        last_runtime_error: Exception | None = None
        for attempt in range(1, self._runtime_retry_attempts + 1):
            try:
                if _graph_accepts_decision_context(graph):
                    propagated = graph.propagate(
                        symbol,
                        trade_date.isoformat(),
                        decision_context=serialized_context,
                    )
                else:
                    propagated = graph.propagate(symbol, trade_date.isoformat())
                if isinstance(propagated, tuple) and len(propagated) == 2:
                    final_state, signal = propagated
                else:
                    final_state, signal = propagated, None
                structured = _extract_structured_output(final_state=final_state, signal=signal)
                if structured is None:
                    if not isinstance(final_state, dict):
                        raise CryptoAgentsStructuredOutputMissingError(
                            "CryptoAgents graph output must provide a JSON-like final_state for projection."
                        )
                    try:
                        structured = self._projector.project(
                            decision_context=context,
                            final_state=final_state,
                            signal=signal,
                        )
                    except Exception as exc:
                        raise CryptoAgentsStructuredOutputMissingError(
                            "CryptoAgents projector failed to build structured decision output."
                        ) from exc
                return _validate_required_structured_keys(structured)
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
    _apply_embedding_runtime_overrides()
    return trading_graph_cls(
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config=config,
    )


def _extract_structured_output(*, final_state: Any, signal: Any) -> dict[str, Any] | None:
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

    return None


def _validate_required_structured_keys(structured: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(_REQUIRED_STRUCTURED_KEYS - set(structured.keys()))
    if missing:
        raise CryptoAgentsStructuredOutputMissingError(
            "CryptoAgents graph output must include required fields: " + ", ".join(missing)
        )
    return structured


def _pair_to_symbol(pair: str) -> str:
    if "/" not in pair:
        raise CryptoAgentsStructuredOutputMissingError("decision_context.strategy_constraints.pair must be like BASE/QUOTE")
    base = pair.split("/", maxsplit=1)[0].strip().upper()
    if not base:
        raise CryptoAgentsStructuredOutputMissingError("cannot derive base symbol from pair")
    return base


def _serialize_decision_context(context: DecisionContext) -> dict[str, Any]:
    payload = context.model_dump(mode="json")
    payload.setdefault("generated_at", datetime.now(tz=timezone.utc).isoformat())
    return payload


def _graph_accepts_decision_context(graph: Any) -> bool:
    propagate = getattr(graph, "propagate", None)
    if propagate is None:
        return False
    for parameter in inspect.signature(propagate).parameters.values():
        if parameter.name == "decision_context":
            return True
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            return True
    return False


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


def _apply_embedding_runtime_overrides() -> None:
    embedding_model = _resolve_embedding_model_override()
    if embedding_model is None:
        return
    try:
        memory_module = importlib.import_module("cryptoagents.agents.utils.memory")
    except Exception as exc:
        raise CryptoAgentsRunnerDependencyError(
            "CryptoAgents memory module import failed while applying embedding model override."
        ) from exc
    memory_cls = getattr(memory_module, "FinancialSituationMemory", None)
    if memory_cls is None:
        raise CryptoAgentsRunnerDependencyError(
            "FinancialSituationMemory is missing in cryptoagents.agents.utils.memory."
        )

    def _get_embedding(self: Any, text: str) -> Any:
        response = self.client.embeddings.create(model=embedding_model, input=text)
        return response.data[0].embedding

    memory_cls.get_embedding = _get_embedding


def _resolve_embedding_model_override() -> str | None:
    base_url = _normalize_openai_base_url()
    configured = os.environ.get("CRYPTOAGENTS_EMBEDDING_MODEL")
    if configured is None or configured.strip() == "":
        if not _is_verified_relay_base_url(base_url):
            return None
        model = _DEFAULT_RELAY_EMBEDDING_MODEL
    else:
        model = configured.strip()
    if _is_verified_relay_base_url(base_url) and "/" not in model:
        raise CryptoAgentsRunnerDependencyError(
            "CRYPTOAGENTS_EMBEDDING_MODEL must be provider-prefixed when OPENAI_BASE_URL uses a verified relay."
        )
    return model


def _normalize_openai_base_url() -> str | None:
    raw = os.environ.get("OPENAI_BASE_URL")
    if raw is None:
        return None
    normalized = raw.strip().rstrip("/")
    if normalized == "":
        return None
    return normalized


def _is_verified_relay_base_url(base_url: str | None) -> bool:
    if base_url is None:
        return False
    return base_url in _VERIFIED_RELAY_BASE_URLS


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
