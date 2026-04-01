from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterator

from pydantic import BaseModel, ConfigDict, RootModel

try:
    from .errors import ExportDomainError
except ImportError:  # pragma: no cover - support direct script-style imports in local tests.
    from errors import ExportDomainError


class DecisionArtifact(RootModel[dict[str, Any]]):
    """Typed wrapper for DecisionArtifact payload."""


class ExecutionRecord(RootModel[dict[str, Any]]):
    """Typed wrapper for ExecutionRecord payload."""


class MachineTruth(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_artifact: dict[str, Any]
    execution_record: dict[str, Any]


@dataclass(frozen=True)
class ExportOutputs:
    machine_truth_json: str
    audit_markdown: str
    investment_memo: str


def export_outputs(
    *,
    decision_artifact: DecisionArtifact,
    execution_record: ExecutionRecord,
    memo_brief: str | None = None,
) -> ExportOutputs:
    if not decision_artifact.root and not execution_record.root:
        raise ExportDomainError(
            "TODO: docs/knowledge/08_delivery/01_export_outputs.md 未定义空产物导出规则。"
        )

    machine_truth_model = MachineTruth(
        decision_artifact=decision_artifact.root,
        execution_record=execution_record.root,
    )
    machine_truth_doc = machine_truth_model.model_dump(mode="python")

    try:
        machine_truth_json = json.dumps(
            machine_truth_doc,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except TypeError as exc:
        raise ExportDomainError(f"Machine Truth JSON 序列化失败: {exc}") from exc

    excerpt_items = list(_iter_json_leaves(machine_truth_doc, pointer=""))
    audit_markdown = _render_audit_markdown(excerpt_items)
    investment_memo = _render_investment_memo(
        machine_truth_json=machine_truth_json,
        excerpt_count=len(excerpt_items),
        memo_brief=memo_brief,
    )

    return ExportOutputs(
        machine_truth_json=machine_truth_json,
        audit_markdown=audit_markdown,
        investment_memo=investment_memo,
    )


def _iter_json_leaves(value: Any, pointer: str) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        if not value:
            yield pointer or "/", {}
            return
        for key in sorted(value):
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from _iter_json_leaves(value[key], f"{pointer}/{escaped}")
        return

    if isinstance(value, list):
        if not value:
            yield pointer or "/", []
            return
        for idx, item in enumerate(value):
            yield from _iter_json_leaves(item, f"{pointer}/{idx}")
        return

    yield pointer or "/", value


def _render_audit_markdown(excerpt_items: list[tuple[str, Any]]) -> str:
    lines = [
        "# Audit Markdown Excerpt",
        "",
        "> 来源：Machine Truth JSON。此处仅做字段摘抄，不改写结论。",
        "",
        "```machine-truth-excerpt",
    ]
    for pointer, value in excerpt_items:
        lines.append(f"{pointer}\t{json.dumps(value, ensure_ascii=False, sort_keys=True)}")
    lines.extend(["```", ""])
    return "\n".join(lines)


def _render_investment_memo(
    *,
    machine_truth_json: str,
    excerpt_count: int,
    memo_brief: str | None,
) -> str:
    memo_note = memo_brief.strip() if memo_brief and memo_brief.strip() else "TODO: 补充投研摘要。"
    checksum = hashlib.sha256(machine_truth_json.encode("utf-8")).hexdigest()
    lines = [
        "# Investment Memo",
        "",
        "## Boundary",
        "- 本报告用于投研沟通，不作为执行真相。",
        "- 执行以 Machine Truth JSON 为唯一来源。",
        "",
        "## Traceability Metadata",
        f"- machine_truth_sha256: {checksum}",
        f"- audit_excerpt_items: {excerpt_count}",
        "",
        "## Analyst Notes",
        memo_note,
        "",
        "TODO: docs/knowledge/08_delivery/01_export_outputs.md 未定义 Memo 正式模板。",
    ]
    return "\n".join(lines)


__all__ = [
    "DecisionArtifact",
    "ExecutionRecord",
    "ExportDomainError",
    "ExportOutputs",
    "MachineTruth",
    "export_outputs",
]
