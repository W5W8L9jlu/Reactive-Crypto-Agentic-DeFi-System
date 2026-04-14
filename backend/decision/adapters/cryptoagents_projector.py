from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from backend.data.context_builder.models import DecisionContext


class CryptoAgentsProjectorPort(Protocol):
    def project(
        self,
        *,
        decision_context: DecisionContext,
        final_state: dict[str, Any],
        signal: Any,
    ) -> dict[str, Any]: ...


class DefaultCryptoAgentsProjector:
    """Project free-text upstream state into local structured PortfolioManagerOutput shape."""

    def __init__(self, *, prompt_path: Path | None = None) -> None:
        self._prompt_path = prompt_path or (
            Path(__file__).resolve().parents[1]
            / "prompts"
            / "cryptoagents_structured_output.md"
        )

    def project(
        self,
        *,
        decision_context: DecisionContext,
        final_state: dict[str, Any],
        signal: Any,
    ) -> dict[str, Any]:
        # Keep prompt asset as single source for projection contract wording.
        _ = self._load_prompt_contract()
        constraints = decision_context.strategy_constraints
        thesis = _compose_thesis(final_state=final_state, signal=signal)
        if thesis is None:
            raise ValueError("missing narrative decision text for projection")
        trace = _build_agent_trace_steps(final_state=final_state, thesis=thesis)
        return {
            "pair": constraints.pair,
            "dex": constraints.dex,
            "position_usd": str(constraints.max_position_usd),
            "max_slippage_bps": constraints.max_slippage_bps,
            "stop_loss_bps": constraints.stop_loss_bps,
            "take_profit_bps": constraints.take_profit_bps,
            "entry_conditions": ("price_below:projected_entry",),
            "ttl_seconds": constraints.ttl_seconds,
            "projected_daily_trade_count": max(0, min(1, constraints.daily_trade_limit)),
            "investment_thesis": thesis,
            "confidence_score": _extract_confidence(final_state=final_state),
            "agent_trace_steps": trace,
        }

    def _load_prompt_contract(self) -> str:
        if not self._prompt_path.exists():
            raise ValueError(f"missing projector prompt: {self._prompt_path}")
        content = self._prompt_path.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError(f"empty projector prompt: {self._prompt_path}")
        return content


def _compose_thesis(*, final_state: dict[str, Any], signal: Any) -> str | None:
    text_candidates: tuple[Any, ...] = (
        final_state.get("final_trade_decision"),
        final_state.get("portfolio_decision"),
        final_state.get("market_report"),
        signal,
    )
    for candidate in text_candidates:
        if not isinstance(candidate, str):
            continue
        text = candidate.strip()
        if not text:
            continue
        if text.lower() in {"buy", "sell", "hold"}:
            continue
        return text
    return None


def _extract_confidence(*, final_state: dict[str, Any]) -> str:
    value = final_state.get("confidence_score")
    if isinstance(value, (int, float, str)):
        text = str(value).strip()
        if text:
            return text
    return "0.5"


def _build_agent_trace_steps(*, final_state: dict[str, Any], thesis: str) -> list[dict[str, str]]:
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    traces: list[dict[str, str]] = []
    mapping = (
        ("market_analyst", final_state.get("market_report")),
        ("news_analyst", final_state.get("news_report")),
        ("fundamentals_analyst", final_state.get("fundamentals_report")),
    )
    for agent, raw_summary in mapping:
        if isinstance(raw_summary, str) and raw_summary.strip():
            traces.append(
                {
                    "agent": agent,
                    "summary": raw_summary.strip()[:200],
                    "timestamp": now_iso,
                }
            )
    traces.append(
        {
            "agent": "portfolio_manager",
            "summary": thesis[:200],
            "timestamp": now_iso,
        }
    )
    return traces


__all__ = [
    "CryptoAgentsProjectorPort",
    "DefaultCryptoAgentsProjector",
]
