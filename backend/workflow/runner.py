from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_MANIFEST_PATH = REPO_ROOT / "docs" / "manifests" / "task_context_manifest.json"
WORKFLOW_MANIFEST_PATH = REPO_ROOT / "docs" / "manifests" / "workflow_manifest.json"

_DECOMPOSITION_STOPWORDS = {
    "a",
    "an",
    "and",
    "before",
    "build",
    "by",
    "for",
    "from",
    "full",
    "improve",
    "in",
    "into",
    "is",
    "it",
    "module",
    "modules",
    "need",
    "of",
    "on",
    "or",
    "project",
    "should",
    "the",
    "this",
    "that",
    "to",
    "up",
    "use",
    "with",
    "workflow",
    "across",
    "coding",
}


def _ensure_utf8_stdio() -> None:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_task_manifest() -> dict:
    return _load_json(TASK_MANIFEST_PATH)


def load_workflow_manifest() -> dict:
    return _load_json(WORKFLOW_MANIFEST_PATH)


def get_module_spec(module_id: str) -> dict:
    manifest = load_task_manifest()
    for module in manifest["modules"]:
        if module["id"] == module_id:
            return module
    raise KeyError(module_id)


def get_workflow_spec(module_id: str) -> dict:
    workflow = load_workflow_manifest()
    try:
        roles = dict(workflow["module_roles"][module_id])
        roles.setdefault("senior_developer", "Senior Developer")
        return roles
    except KeyError as exc:
        raise KeyError(module_id) from exc


def _iter_module_tokens(module: dict) -> set[str]:
    tokens: set[str] = set()
    tokens.add(module["id"].lower())
    for chunk in re.split(r"[^a-zA-Z0-9]+", module["title"].lower()):
        if len(chunk) >= 3:
            tokens.add(chunk)
    for chunk in module["id"].lower().split("_"):
        if len(chunk) >= 3:
            tokens.add(chunk)
    return tokens


def _module_roots(module: dict) -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved.exists() and resolved not in seen:
            seen.add(resolved)
            roots.append(resolved)

    add(REPO_ROOT / module["workdir"])
    for raw in module["files"]:
        path = REPO_ROOT / raw
        if path.exists() and path.is_dir():
            add(path)
        if path.parts and path.parts[0] == "backend" and len(path.parts) > 1:
            add(REPO_ROOT / path.parts[0] / path.parts[1])
    return roots


def discover_test_targets(module: dict) -> list[Path]:
    tokens = _iter_module_tokens(module)
    targets: list[Path] = []
    seen: set[Path] = set()

    for root in _module_roots(module):
        for pattern in ("test*.py", "*test*.py"):
            for candidate in root.rglob(pattern):
                if not candidate.is_file():
                    continue
                candidate_lower = candidate.as_posix().lower()
                if not any(token in candidate_lower for token in tokens):
                    continue
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    targets.append(resolved)

    return targets


def validate_manifest() -> list[str]:
    issues: list[str] = []
    task_manifest = load_task_manifest()
    workflow_manifest = load_workflow_manifest()
    task_module_ids = {module["id"] for module in task_manifest["modules"]}
    workflow_module_ids = set(workflow_manifest["module_roles"])

    missing_in_workflow = sorted(task_module_ids - workflow_module_ids)
    extra_in_workflow = sorted(workflow_module_ids - task_module_ids)
    if missing_in_workflow:
        issues.append(
            "Modules missing from workflow manifest: " + ", ".join(missing_in_workflow)
        )
    if extra_in_workflow:
        issues.append(
            "Unknown workflow modules: " + ", ".join(extra_in_workflow)
        )

    for module in task_manifest["modules"]:
        for key in ("workdir", "knowledge", "contract", "prompt"):
            path = REPO_ROOT / module[key]
            if not path.exists():
                issues.append(f"Missing {key} for {module['id']}: {module[key]}")
        for dependency in module.get("depends", []):
            path = REPO_ROOT / dependency
            if not path.exists():
                issues.append(f"Missing dependency for {module['id']}: {dependency}")
        for raw in module.get("files", []):
            path = REPO_ROOT / raw
            if not path.exists():
                issues.append(f"Missing canonical file for {module['id']}: {raw}")

    return issues


def _find_phase_for_module(module_id: str) -> str:
    workflow_manifest = load_workflow_manifest()
    for phase in workflow_manifest["phases"]:
        if module_id in phase["modules"]:
            return phase["name"]
    return "Unassigned"


def _read_contract_text(module: dict) -> str:
    return (REPO_ROOT / module["contract"]).read_text(encoding="utf-8")


def _extract_contract_section_items(contract_text: str, heading: str) -> list[str]:
    items: list[str] = []
    capture = False
    for raw_line in contract_text.splitlines():
        line = raw_line.strip()
        if line == f"## {heading}":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.startswith(("- ", "* ")):
            item = line[2:].strip()
            if item:
                items.append(item)
    return items


def _unique_strings(values: Iterable[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def _normalize_task_items(values: list[str] | None) -> list[str]:
    items: list[str] = []
    for value in values or []:
        for chunk in re.split(r"\r?\n", value):
            chunk = chunk.strip()
            if not chunk:
                continue
            if chunk.startswith("[ ] "):
                chunk = chunk[4:].strip()
            elif chunk.startswith(("- ", "* ")):
                chunk = chunk[2:].strip()
            items.append(chunk)
    return items


def _module_read_first_paths(module: dict) -> list[str]:
    paths = [
        "docs/knowledge/01_core/01_system_invariants.md",
        "docs/knowledge/01_core/02_domain_models.md",
    ]
    paths.extend(module.get("depends", []))
    paths.extend([module["knowledge"], module["contract"], module["prompt"]])
    return _unique_strings(paths)


def _module_only_edit_paths(module: dict) -> list[str]:
    return _unique_strings(module["files"])


def _workflow_role_lines(roles: dict) -> list[str]:
    lines = [
        f"- Developer: `{roles['developer']}`",
        f"- Senior Developer: `{roles['senior_developer']}`" if roles.get("senior_developer") else "",
        f"- Test Executor: `{roles['tester']}`",
        f"- Result Analyzer: `{roles['analyzer']}`",
    ]
    if roles.get("reviewer"):
        lines.append(f"- Code Reviewer: `{roles['reviewer']}`")
    if roles.get("git_master"):
        lines.append(f"- Git Workflow Master: `{roles['git_master']}`")
    lines.append(f"- Gate: `{roles['gate']}`")
    return [line for line in lines if line]


def _workflow_gate_lines(roles: dict) -> list[str]:
    lines: list[str] = []
    if roles.get("senior_developer"):
        lines.extend(
            [
                "## Senior Developer Gate",
                "",
                "- Trigger: implementation needs cross-file coordination, engineering detail recovery, or unblock support.",
                "- Input: task card, diff, related files, and test feedback.",
                "- Output: implementation suggestions, patch direction, and risk points.",
                "",
            ]
        )
    if roles.get("reviewer"):
        lines.extend(
            [
                "## Code Reviewer Gate",
                "",
                "- Trigger: code changes are implemented and tests have passed.",
                "- Input: the diff, test summary, and preserved invariants.",
                "- Output: review verdict, issues, and final approval/blocker notes.",
                "",
            ]
        )
    if roles.get("git_master"):
        lines.extend(
            [
                "## Git Workflow Master Gate",
                "",
                "- Trigger: work is ready to close or publish.",
                "- Input: branch state, commit range, PR scope, and outstanding review notes.",
                "- Output: branch/commit/PR hygiene verdict and closure instructions.",
                "",
            ]
        )
    return lines


def _module_suggested_checks(module: dict) -> list[str]:
    tests = discover_test_targets(module)
    if not tests:
        return ["No module-local test target discovered."]
    return [
        f"python -m pytest {path.relative_to(REPO_ROOT).as_posix()} -q"
        for path in tests
    ]


def _tokenize_text(text: str) -> list[str]:
    tokens: list[str] = []
    normalized = text.replace("_", " ")
    for raw in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+|[\u4e00-\u9fff]+", normalized):
        if re.fullmatch(r"[A-Za-z]+(?:'[A-Za-z]+)?", raw):
            parts = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|\d+", raw)
            if parts:
                tokens.extend(part.casefold() for part in parts if part.casefold() not in _DECOMPOSITION_STOPWORDS)
            else:
                token = raw.casefold()
                if token not in _DECOMPOSITION_STOPWORDS:
                    tokens.append(token)
            continue
        if raw.casefold() not in _DECOMPOSITION_STOPWORDS:
            tokens.append(raw)
    return tokens


def _read_module_contract_sections(module: dict) -> dict[str, list[str]]:
    contract_text = _read_contract_text(module)
    return {
        "scope": _extract_contract_section_items(contract_text, "Scope"),
        "definition_of_done": _extract_contract_section_items(contract_text, "Definition of Done"),
        "minimum_verification": _extract_contract_section_items(contract_text, "Minimum Verification"),
        "non_goals": _extract_contract_section_items(contract_text, "Non-goals"),
        "hard_invariants": _extract_contract_section_items(contract_text, "Hard Invariants"),
        "handoff_contract": _extract_contract_section_items(contract_text, "Handoff Contract"),
    }


def _module_decomposition_signals(module: dict, goal_text: str) -> tuple[int, list[str]]:
    sections = _read_module_contract_sections(module)
    module_blob = " ".join(
        [
            module["id"],
            module["title"],
            module.get("group", ""),
            *sections["scope"],
            *sections["definition_of_done"],
            *sections["minimum_verification"],
            *sections["non_goals"],
            *sections["hard_invariants"],
            *sections["handoff_contract"],
        ]
    )
    module_tokens = set(_tokenize_text(module_blob))
    goal_tokens = set(_tokenize_text(goal_text))
    overlap = sorted(goal_tokens & module_tokens)

    score = len(overlap)
    goal_lower = goal_text.casefold()
    module_id_lower = module["id"].casefold()
    module_title_lower = module["title"].casefold()

    if module_id_lower.replace("_", " ") in goal_lower or module_id_lower in goal_lower:
        score += 3
    if module_title_lower in goal_lower:
        score += 3
    if module.get("group") and module["group"].casefold() in goal_lower:
        score += 1

    signals: list[str] = []
    if overlap:
        signals.append("token overlap: " + ", ".join(overlap[:4]))
    if module_id_lower.replace("_", " ") in goal_lower or module_id_lower in goal_lower:
        signals.append("goal references module id")
    if module_title_lower in goal_lower:
        signals.append("goal references module title")
    if module.get("group") and module["group"].casefold() in goal_lower:
        signals.append("goal references module group")
    if not signals:
        signals.append("no strong token match; keep in candidate pool by phase order")

    return score, signals


def _module_decomposition_summary(goal: str, context: list[str] | None = None) -> dict:
    context = context or []
    goal_text = " ".join([goal, *context]).strip()
    phase_order = {
        phase["name"]: index for index, phase in enumerate(load_workflow_manifest()["phases"])
    }
    scored_modules: list[dict] = []

    for module in load_task_manifest()["modules"]:
        score, signals = _module_decomposition_signals(module, goal_text)
        scored_modules.append(
            {
                "module_id": module["id"],
                "title": module["title"],
                "phase": _find_phase_for_module(module["id"]),
                "score": score,
                "signals": signals,
                "workflow_roles": get_workflow_spec(module["id"]),
            }
        )

    scored_modules.sort(key=lambda item: (-item["score"], phase_order.get(item["phase"], 999), item["module_id"]))
    top_modules = scored_modules[:5]
    top_score = top_modules[0]["score"] if top_modules else 0
    second_score = top_modules[1]["score"] if len(top_modules) > 1 else 0

    if top_modules and top_score >= 4 and top_score >= second_score + 2:
        recommended_mode = "single-module"
        recommended_module = top_modules[0]["module_id"]
    else:
        recommended_mode = "project-decomposition"
        recommended_module = None

    phase_plan: list[dict] = []
    seen_phases: set[str] = set()
    for phase in load_workflow_manifest()["phases"]:
        modules_in_phase = [item["module_id"] for item in top_modules if item["phase"] == phase["name"]]
        if modules_in_phase:
            seen_phases.add(phase["name"])
            phase_plan.append({"phase": phase["name"], "modules": modules_in_phase})
    for item in top_modules:
        if item["phase"] not in seen_phases:
            phase_plan.append({"phase": item["phase"], "modules": [item["module_id"]]})
            seen_phases.add(item["phase"])

    return {
        "goal": goal,
        "context": context,
        "goal_text": goal_text,
        "recommended_mode": recommended_mode,
        "recommended_module": recommended_module,
        "top_modules": top_modules,
        "phase_plan": phase_plan,
    }


def _project_decomposition_product_manager(proposal: dict) -> dict:
    notes = [
        f"Project goal: {proposal['goal']}",
        "Keep scope aligned to module contracts and existing workflow phases.",
        "No module-level draft before decomposition approval.",
    ]
    if proposal["context"]:
        notes.append("Context constraints: " + " / ".join(proposal["context"]))
    return {"role": "Product Manager", "notes": notes}


def _project_decomposition_workflow_architect(proposal: dict) -> dict:
    return {
        "role": "Workflow Architect",
        "recommended_mode": proposal["recommended_mode"],
        "recommended_module": proposal["recommended_module"],
        "phase_plan": proposal["phase_plan"],
    }


def _project_decomposition_software_architect(proposal: dict) -> dict:
    top_modules = proposal["top_modules"]
    concerns = [
        "Validate boundaries against contract scope, handoff, and non-goal clauses.",
        "Prefer a single module only when one candidate clearly dominates.",
    ]
    if top_modules:
        concerns.append(f"Top candidate: {top_modules[0]['module_id']} ({top_modules[0]['phase']})")
    return {
        "role": "Software Architect",
        "concerns": concerns,
        "top_modules": top_modules[:5],
    }


def _project_decomposition_senior_project_manager(proposal: dict) -> dict:
    backlog = []
    for phase in proposal["phase_plan"]:
        backlog.append(
            {
                "phase": phase["phase"],
                "modules": phase["modules"],
                "order_hint": "Start from the first module in phase order.",
            }
        )
    return {"role": "Senior Project Manager", "backlog": backlog}


def _project_decomposition_technical_writer(proposal: dict, role_outputs: dict[str, dict]) -> str:
    top_modules = proposal["top_modules"]
    lines = [
        "# Project Decomposition",
        "",
        f"- `状态：` {proposal.get('status', 'Proposed')}",
        "",
        "## Technical Writer Synthesis",
        "",
    ]
    if proposal["recommended_mode"] == "single-module":
        lines.append(f"- Direct module workflow for `{proposal['recommended_module']}`")
    else:
        lines.append("- Project decomposition required before module-level draft")
    lines.extend(
        [
            "",
            "## Product Manager",
            "",
            *[f"- {item}" for item in role_outputs["product_manager"]["notes"]],
            "",
            "## Workflow Architect",
            "",
            f"- Recommended mode: `{role_outputs['workflow_architect']['recommended_mode']}`",
        ]
    )
    if role_outputs["workflow_architect"]["recommended_module"]:
        lines.append(f"- Recommended module: `{role_outputs['workflow_architect']['recommended_module']}`")
    lines.extend(
        [
            "",
            "## Software Architect",
            "",
            *[f"- {item}" for item in role_outputs["software_architect"]["concerns"]],
            "",
            "## Senior Project Manager",
            "",
        ]
    )
    for item in role_outputs["senior_project_manager"]["backlog"]:
        lines.append(f"- `{item['phase']}`: {', '.join(item['modules'])}")
    lines.extend(
        [
            "",
            "## Review Gate",
            "",
            "- This proposal must be approved before module-level `draft`.",
            "",
            "## Top Candidates",
            "",
        ]
    )
    if top_modules:
        for item in top_modules:
            lines.extend(
                [
                    f"- `{item['module_id']}` ({item['title']})",
                    f"  - Phase: `{item['phase']}`",
                    f"  - Score: `{item['score']}`",
                    "  - Roles: "
                    + ", ".join(
                        [
                            f"developer `{item['workflow_roles']['developer']}`",
                            f"tester `{item['workflow_roles']['tester']}`",
                            f"analyzer `{item['workflow_roles']['analyzer']}`",
                            *(
                                [f"reviewer `{item['workflow_roles']['reviewer']}`"]
                                if item["workflow_roles"].get("reviewer")
                                else []
                            ),
                            *(
                                [f"git_master `{item['workflow_roles']['git_master']}`"]
                                if item["workflow_roles"].get("git_master")
                                else []
                            ),
                            f"gate `{item['workflow_roles']['gate']}`",
                        ]
                    ),
                    f"  - Signals: {', '.join(item['signals'])}",
                ]
            )
    else:
        lines.append("- No candidate modules found.")
    lines.extend(
        [
            "",
            "## Phase Plan",
            "",
        ]
    )
    if proposal["phase_plan"]:
        for phase in proposal["phase_plan"]:
            lines.append(f"- `{phase['phase']}`: {', '.join(phase['modules'])}")
    else:
        lines.append("- No phase plan available.")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
        ]
    )
    if proposal["recommended_mode"] == "single-module":
        lines.append(f"- Use `draft {proposal['recommended_module']}` next.")
    else:
        lines.append("- Approve the split, then run `spawn-decomposition` to generate role packets.")
    return "\n".join(lines)


def _build_project_decomposition_role_outputs(proposal: dict) -> dict[str, dict]:
    return {
        "product_manager": _project_decomposition_product_manager(proposal),
        "workflow_architect": _project_decomposition_workflow_architect(proposal),
        "software_architect": _project_decomposition_software_architect(proposal),
        "senior_project_manager": _project_decomposition_senior_project_manager(proposal),
    }


_DECOMPOSITION_SPAWN_ROLE_SPECS = [
    {
        "key": "product_manager",
        "role": "Product Manager",
        "depends_on": [],
        "task_lines": [
            "Check whether the decomposition still reflects the user goal and core invariants.",
            "Call out missing acceptance criteria, scope gaps, and ambiguous non-goals.",
            "Do not expand the scope beyond the approved proposal.",
        ],
        "output_lines": [
            "Return a short Markdown review with `Goal Fit`, `Acceptance Gaps`, `Non-goal Gaps`, and `Risk Adjustments`.",
        ],
    },
    {
        "key": "workflow_architect",
        "role": "Workflow Architect",
        "depends_on": [],
        "task_lines": [
            "Validate the phase order, dependency order, and handoff path in the approved split.",
            "Highlight any phase that should be split further or merged back into a single module.",
            "Keep the answer focused on orchestration and boundary flow.",
        ],
        "output_lines": [
            "Return the recommended phase order, dependency notes, and any sequencing risks.",
        ],
    },
    {
        "key": "software_architect",
        "role": "Software Architect",
        "depends_on": [],
        "task_lines": [
            "Review module boundaries, dependency edges, and interface risks in the approved split.",
            "Flag any module that crosses contract boundaries or creates hidden coupling.",
            "Prefer precise boundary comments over broad redesign advice.",
        ],
        "output_lines": [
            "Return a concise boundary review with confirmed cuts and risk flags.",
        ],
    },
    {
        "key": "senior_project_manager",
        "role": "Senior Project Manager",
        "depends_on": [],
        "task_lines": [
            "Turn the approved phase plan into an executable backlog with an order hint.",
            "Identify the first module to attack and the checkpoints that must complete first.",
            "Do not recast architecture decisions; keep the work package level only.",
        ],
        "output_lines": [
            "Return a backlog grouped by phase with the next execution step called out explicitly.",
        ],
    },
    {
        "key": "technical_writer",
        "role": "Technical Writer",
        "depends_on": [
            "Product Manager",
            "Workflow Architect",
            "Software Architect",
            "Senior Project Manager",
        ],
        "task_lines": [
            "Wait for the four review outputs before final synthesis.",
            "Merge the approved split with the review notes into the final decomposition proposal.",
            "Preserve the existing hard invariants and the approved phase plan.",
        ],
        "output_lines": [
            "Return final Markdown with sections for synthesis, each role, review gate, top candidates, phase plan, and next step.",
        ],
    },
]


def _decomposition_spawn_prompt(proposal: dict, spec: dict) -> str:
    lines = [
        f"You are the `{spec['role']}` in the Project Decomposition workflow.",
        "Use the approved decomposition proposal as the source of truth.",
        f"Project goal: {proposal['goal']}",
        f"Recommended mode: `{proposal['recommended_mode']}`",
    ]
    if proposal["context"]:
        lines.append("Context constraints: " + " / ".join(proposal["context"]))
    lines.extend(
        [
            "",
            "Task:",
            *[f"- {item}" for item in spec["task_lines"]],
            "",
            "Return format:",
            *[f"- {item}" for item in spec["output_lines"]],
        ]
    )
    if spec["depends_on"]:
        lines.extend(
            [
                "",
                "Dependencies:",
                *[f"- Wait for `{role}` output before final synthesis." for role in spec["depends_on"]],
            ]
        )
    return "\n".join(lines)


def _decomposition_spawn_agent_packet(proposal: dict, spec: dict) -> dict:
    role_output = proposal["role_outputs"][spec["key"]]
    prompt = _decomposition_spawn_prompt(proposal, spec)
    return {
        "role": spec["role"],
        "role_key": spec["key"],
        "depends_on": spec["depends_on"],
        "spawn_agent": {
            "message": prompt,
            "items": [
                {"type": "text", "text": prompt},
                {
                    "type": "text",
                    "text": "Approved decomposition proposal:\n```markdown\n"
                    + proposal["markdown"]
                    + "\n```",
                },
                {
                    "type": "text",
                    "text": "Deterministic draft for this role:\n```json\n"
                    + json.dumps(role_output, indent=2, ensure_ascii=False)
                    + "\n```",
                },
            ],
        },
    }


def build_decomposition_spawn_payload(proposal: dict) -> dict:
    if proposal.get("status") != "Approved":
        raise ValueError("Project decomposition must be Approved before spawn packets are generated.")
    if "role_outputs" not in proposal:
        raise ValueError("Approved project decomposition is missing role_outputs.")

    packets = [_decomposition_spawn_agent_packet(proposal, spec) for spec in _DECOMPOSITION_SPAWN_ROLE_SPECS]
    return {
        "workflow": "Project Decomposition",
        "status": "ReadyForSpawn",
        "spawn_order": [spec["role"] for spec in _DECOMPOSITION_SPAWN_ROLE_SPECS],
        "spawn_groups": [
            {
                "name": "review-pack",
                "mode": "parallel",
                "agents": packets[:-1],
            },
            {
                "name": "final-synthesis",
                "mode": "after-review",
                "agents": [packets[-1]],
            },
        ],
        "source_proposal": proposal,
        "summary": proposal["summary"],
    }


def build_project_decomposition(goal: str, *, context: list[str] | None = None) -> dict:
    proposal = _module_decomposition_summary(goal, context)
    role_outputs = _build_project_decomposition_role_outputs(proposal)
    technical_writer_synthesis = _project_decomposition_technical_writer(proposal, role_outputs)
    role_outputs["technical_writer"] = {
        "role": "Technical Writer",
        "synthesis": technical_writer_synthesis,
    }
    return {
        **proposal,
        "status": "Proposed",
        "role_outputs": role_outputs,
        "summary": {
            "goal": proposal["goal"],
            "recommended_mode": proposal["recommended_mode"],
            "recommended_module": proposal["recommended_module"],
            "top_candidate_ids": [item["module_id"] for item in proposal["top_modules"]],
            "phase_names": [item["phase"] for item in proposal["phase_plan"]],
        },
        "markdown": technical_writer_synthesis,
    }


def build_approved_project_decomposition_from_proposal(proposal: dict) -> dict:
    status = proposal.get("status")
    if status not in {"Proposed", "Approved"}:
        raise ValueError("Project decomposition must be Proposed before approval.")
    approved = dict(proposal)
    approved["status"] = "Approved"
    return approved


def _module_draft_fields(module_id: str, instructions: list[str] | None = None) -> dict:
    module = get_module_spec(module_id)
    contract_text = _read_contract_text(module)
    instructions = instructions or []

    scope_items = _extract_contract_section_items(contract_text, "Scope")
    done_items = _extract_contract_section_items(contract_text, "Definition of Done")
    verification_items = _extract_contract_section_items(contract_text, "Minimum Verification")
    non_goal_items = _extract_contract_section_items(contract_text, "Non-goals")
    hard_invariants = _extract_contract_section_items(contract_text, "Hard Invariants")
    handoff_items = _extract_contract_section_items(contract_text, "Handoff Contract")

    goal = (
        f"Implement the module scope for {module['title']}"
        if not scope_items
        else f"Implement module scope: {'; '.join(scope_items)}"
    )
    if instructions:
        goal = f"{goal} | Human instruction: {' / '.join(instructions)}"

    acceptance = _unique_strings(done_items + verification_items)
    if not acceptance:
        acceptance = ["TODO: derive acceptance from contract Definition of Done and Minimum Verification."]

    non_goals = _unique_strings(non_goal_items)
    if not non_goals:
        non_goals = ["TODO: derive non-goals from contract Non-goals section."]

    risks = _unique_strings(hard_invariants + handoff_items)
    if instructions:
        risks.append("Human instruction may further constrain scope; re-review after edits.")
    if not risks:
        risks = ["TODO: derive risks from hard invariants and handoff contract."]

    return {
        "module_id": module_id,
        "title": module["title"],
        "goal": goal,
        "acceptance": acceptance,
        "non_goals": non_goals,
        "risks": risks,
        "instructions": instructions,
        "sources": {
            "scope": scope_items,
            "definition_of_done": done_items,
            "minimum_verification": verification_items,
            "non_goals": non_goal_items,
            "hard_invariants": hard_invariants,
            "handoff_contract": handoff_items,
        },
    }


def _module_draft_summary(draft: dict) -> dict:
    return {
        "module_id": draft["module_id"],
        "title": draft["title"],
        "goal": draft["goal"],
        "acceptance_highlights": draft["acceptance"][:3],
        "non_goals_highlights": draft["non_goals"][:3],
        "risks_highlights": draft["risks"][:3],
    }


def _build_draft_markdown(module_id: str, *, instructions: list[str] | None = None) -> str:
    module = get_module_spec(module_id)
    package = _module_package_data(module_id)
    draft = _module_draft_fields(module_id, instructions)

    lines = [
        "# Draft Task Card",
        "",
        "## Header",
        "",
        f"- `模块：` {module['title']} (`{module_id}`)",
        f"- `负责人 agent：` {package['workflow_roles']['developer']}",
        "- `状态：` Draft",
        "- `来源：` 用户目标 / contract / prompt / knowledge",
    ]
    if draft["instructions"]:
        lines.extend(
            [
                "",
                "## 0. Human Instruction",
                "",
                *[f"- {item}" for item in draft["instructions"]],
            ]
        )
    lines.extend(
        [
            "",
            "## 1. 目标",
            "",
            f"- {draft['goal']}",
            "",
            "## 2. 验收标准",
            "",
            *[f"- [ ] {item}" for item in draft["acceptance"]],
            "",
            "## 3. 非目标",
            "",
            *[f"- {item}" for item in draft["non_goals"]],
            "",
            "## 4. 风险",
            "",
            *[f"- {item}" for item in draft["risks"]],
            "",
            "## 5. 依据",
            "",
            "- `docs/knowledge/01_core/01_system_invariants.md`",
            "- `docs/knowledge/01_core/02_domain_models.md`",
            f"- `{module['knowledge']}`",
            f"- `{module['contract']}`",
            f"- `{module['prompt']}`",
        ]
    )
    return "\n".join(lines)


def build_task_draft(module_id: str, *, instructions: list[str] | None = None) -> dict:
    package = _module_package_data(module_id)
    draft = _module_draft_fields(module_id, instructions)
    summary = _module_draft_summary(draft)
    markdown = _build_draft_markdown(module_id, instructions=instructions)
    return {
        **package,
        "status": "Draft",
        "summary": summary,
        "draft": draft,
        "markdown": markdown,
    }


def _render_draft_review(draft: dict) -> str:
    summary = draft["summary"]
    acceptance_lines = [f"- {item}" for item in summary["acceptance_highlights"]]
    non_goal_lines = [f"- {item}" for item in summary["non_goals_highlights"]]
    risk_lines = [f"- {item}" for item in summary["risks_highlights"]]
    lines = [
        "# Draft Summary",
        "",
        f"- `模块：` {summary['title']} (`{summary['module_id']}`)",
        f"- `阶段：` {draft['phase']}",
        f"- `目标：` {summary['goal']}",
        "",
        "## 重点验收",
        "",
        *(acceptance_lines or ["- 无"]),
        "",
        "## 重点非目标",
        "",
        *(non_goal_lines or ["- 无"]),
        "",
        "## 重点风险",
        "",
        *(risk_lines or ["- 无"]),
        "",
        "# Full Draft",
        "",
        draft["markdown"],
    ]
    return "\n".join(lines)


def _module_package_data(module_id: str) -> dict:
    module = get_module_spec(module_id)
    roles = get_workflow_spec(module_id)
    phase = _find_phase_for_module(module_id)
    read_first = _module_read_first_paths(module)
    only_edit = _module_only_edit_paths(module)
    suggested_checks = _module_suggested_checks(module)
    return {
        "module_id": module_id,
        "title": module["title"],
        "phase": phase,
        "workflow_roles": roles,
        "read_first": read_first,
        "only_edit": only_edit,
        "suggested_checks": suggested_checks,
    }


def _build_task_card_markdown(
    module_id: str,
    *,
    goal: str,
    acceptance: list[str] | None = None,
    non_goals: list[str] | None = None,
    risks: list[str] | None = None,
) -> str:
    module = get_module_spec(module_id)
    roles = get_workflow_spec(module_id)
    package = _module_package_data(module_id)
    acceptance = acceptance or []
    non_goals = non_goals or []
    risks = risks or []

    lines = [
        "# Task Card",
        "",
        "## Header",
        "",
        f"- `模块：` {module['title']} (`{module_id}`)",
        f"- `负责人 agent：` {roles['developer']}",
        "- `状态：` Todo",
        "- `来源：` 用户目标 / contract / prompt / knowledge",
        "",
        "## 1. 目标",
        "",
        f"- {goal}",
        "",
        "## 2. 验收标准",
        "",
    ]
    if acceptance:
        lines.extend(f"- [ ] {item}" for item in acceptance)
    else:
        lines.append("- [ ] TODO")
    lines.extend(
        [
            "",
            "## 3. 非目标",
            "",
        ]
    )
    if non_goals:
        lines.extend(f"- {item}" for item in non_goals)
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## 4. 风险",
            "",
        ]
    )
    if risks:
        lines.extend(f"- {item}" for item in risks)
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## 5. 文件范围",
            "",
            "- `Create:`",
            "- `Modify:`",
            *[f"  - `{path}`" for path in package["only_edit"]],
            "- `Test:`",
            *[f"  - `{check}`" for check in package["suggested_checks"]],
            "",
            "## 6. 约束",
            "",
            "- 必须保持模块知识库和 contract 约束。",
            "- 只触碰文件范围内的路径。",
            "- 输出和路径引用必须保持 POSIX 风格。",
            "",
            "## 7. 测试计划",
            "",
            *[f"- {check}" for check in package["suggested_checks"]],
            "",
            "## 8. 交付物",
            "",
            "- 代码变更",
            "- 测试结果",
            "- 未完成事项或剩余风险",
        ]
    )
    return "\n".join(lines)


def build_task_card(module_id: str, *, goal: str, acceptance: list[str] | None = None, non_goals: list[str] | None = None, risks: list[str] | None = None) -> str:
    return _build_task_card_markdown(
        module_id,
        goal=goal,
        acceptance=acceptance,
        non_goals=non_goals,
        risks=risks,
    )


def _build_prompt_body(module_id: str) -> str:
    module = get_module_spec(module_id)
    roles = get_workflow_spec(module_id)
    phase = _find_phase_for_module(module_id)
    read_first = _module_read_first_paths(module)
    only_edit = _module_only_edit_paths(module)
    suggested_checks = _module_suggested_checks(module)

    lines = [
        f"You are a Codex subagent working on module `{module['title']}` (`{module_id}`).",
        f"Phase: `{phase}`.",
        "",
        "Workflow roles:",
        *_workflow_role_lines(roles),
        "",
        *(_workflow_gate_lines(roles)),
        "",
        "Read first:",
        *[f"- `{path}`" for path in read_first],
        "",
        "Only edit:",
        *[f"- `{path}`" for path in only_edit],
        "",
        "Instructions:",
        "- Use `docs/manifests/workflow_manifest.json` and `docs/manifests/task_context_manifest.json` as the source of truth.",
        "- Keep the change small and reviewable.",
        "- If the implementation gets blocked on cross-file engineering detail, escalate to Senior Developer.",
        "- After implementation and tests, route the diff through the Code Reviewer before final handoff.",
        "- Before branch or PR closure, follow the Git Workflow Master for Git hygiene.",
        "- Preserve POSIX-style paths in any output or references.",
        "- Do not modify files outside the only-edit list.",
        "- If the requested behavior is not defined by the module docs or manifests, stop and report the ambiguity instead of inventing it.",
        "",
        "Suggested checks:",
        *[f"- `{check}`" for check in suggested_checks],
        "",
        "Deliverables:",
        "- Summarize changed files, preserved invariants, validations run, and remaining risks.",
    ]
    return "\n".join(lines)


def build_task_package(module_id: str) -> str:
    module = get_module_spec(module_id)
    package = _module_package_data(module_id)
    prompt_body = _build_prompt_body(module_id)

    lines = [
        f"# Task Package: {module['title']}",
        "",
        f"**Module:** `{package['module_id']}`",
        f"**Title:** `{package['title']}`",
        f"**Phase:** `{package['phase']}`",
        "",
        "## Workflow Roles",
        *_workflow_role_lines(package["workflow_roles"]),
        "",
        *(_workflow_gate_lines(package["workflow_roles"])),
        "",
        "## Read First",
        *[f"- `{path}`" for path in package["read_first"]],
        "",
        "## Only Edit",
        *[f"- `{path}`" for path in package["only_edit"]],
        "",
        "## Suggested Checks",
        *[f"- `{check}`" for check in package["suggested_checks"]],
        "",
        "## Prompt Body",
        "```text",
        prompt_body,
        "```",
    ]
    return "\n".join(lines)


def build_spawn_payload(module_id: str) -> str:
    module = get_module_spec(module_id)
    package = _module_package_data(module_id)
    payload = {
        **package,
        "prompt": _build_prompt_body(module_id),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_spawn_task_payload(
    module_id: str,
    *,
    goal: str,
    acceptance: list[str] | None = None,
    non_goals: list[str] | None = None,
    risks: list[str] | None = None,
) -> str:
    package = _module_package_data(module_id)
    task_card = {
        "module_id": module_id,
        "goal": goal,
        "acceptance": acceptance or [],
        "non_goals": non_goals or [],
        "risks": risks or [],
        "markdown": build_task_card(
            module_id,
            goal=goal,
            acceptance=acceptance,
            non_goals=non_goals,
            risks=risks,
        ),
    }
    prompt_body = "\n".join(
        [
            f"You are a Codex subagent working on module `{package['title']}` (`{module_id}`).",
            f"Phase: `{package['phase']}`.",
            "",
            "Use this task card as the source of truth:",
            "```markdown",
            task_card["markdown"],
            "```",
            "",
            "Module package:",
            json.dumps(package, indent=2, ensure_ascii=False),
            "",
            "Instructions:",
            "- Complete the acceptance criteria.",
            "- Respect the non-goals and risks.",
            "- If the implementation gets blocked on cross-file engineering detail, escalate to Senior Developer.",
            "- After implementation and tests, route the diff through the Code Reviewer before final handoff.",
            "- Before branch or PR closure, follow the Git Workflow Master for Git hygiene.",
            "- Preserve POSIX-style paths in any output or references.",
            "- If the task is under-specified, stop and report the ambiguity instead of inventing behavior.",
        ]
    )
    payload = {
        **package,
        "module_package": package,
        "task_card": task_card,
        "prompt_body": prompt_body,
        "prompt": prompt_body,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_approved_spawn_payload_from_draft(draft: dict) -> str:
    if draft.get("status") != "Approved":
        raise ValueError("Draft must be marked Approved before spawn payload generation.")
    module_id = draft["module_id"]
    package = _module_package_data(module_id)
    task_card = {
        "module_id": module_id,
        "goal": draft["draft"]["goal"],
        "acceptance": draft["draft"]["acceptance"],
        "non_goals": draft["draft"]["non_goals"],
        "risks": draft["draft"]["risks"],
        "markdown": draft["markdown"],
        "status": "Approved",
    }
    prompt_body = "\n".join(
        [
            f"You are a Codex subagent working on module `{package['title']}` (`{module_id}`).",
            f"Phase: `{package['phase']}`.",
            "",
            "Use this task card as the source of truth:",
            "```markdown",
            task_card["markdown"],
            "```",
            "",
            "Module package:",
            json.dumps(package, indent=2, ensure_ascii=False),
            "",
            "Instructions:",
            "- Complete the acceptance criteria.",
            "- Respect the non-goals and risks.",
            "- If the implementation gets blocked on cross-file engineering detail, escalate to Senior Developer.",
            "- After implementation and tests, route the diff through the Code Reviewer before final handoff.",
            "- Before branch or PR closure, follow the Git Workflow Master for Git hygiene.",
            "- Preserve POSIX-style paths in any output or references.",
            "- If the task is under-specified, stop and report the ambiguity instead of inventing behavior.",
        ]
    )
    payload = {
        **package,
        "status": "Approved",
        "module_package": package,
        "task_card": task_card,
        "prompt_body": prompt_body,
        "prompt": prompt_body,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def write_json_file(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _default_approved_split_path(from_split: Path) -> Path:
    return from_split.with_name(f"{from_split.stem}.approved{from_split.suffix}")


def build_dispatch_brief(module_id: str) -> str:
    module = get_module_spec(module_id)
    roles = get_workflow_spec(module_id)
    phase = _find_phase_for_module(module_id)
    tests = discover_test_targets(module)
    read_first = [f"- `{path}`" for path in _module_read_first_paths(module)]

    lines = [
        f"# Dispatch Brief: {module['title']}",
        "",
        f"**Module:** `{module_id}`",
        f"**Phase:** `{phase}`",
        f"**Workdir:** `{module['workdir']}`",
        "",
        "## Roles",
        *_workflow_role_lines(roles),
        "",
        *(_workflow_gate_lines(roles)),
        "",
        "## Read First",
        *read_first,
        "",
        "## Only Edit",
        *[f"- `{path}`" for path in _module_only_edit_paths(module)],
        "",
        "## Suggested Checks",
    ]
    if tests:
        lines.extend(f"- `python -m pytest {path.relative_to(REPO_ROOT).as_posix()} -q`" for path in tests)
    else:
        lines.append("- No module-local test target discovered.")
    lines.extend(
        [
            "",
            "## Output Format",
            "- Use `docs/superpowers/TASK_CARD_TEMPLATE.md` for planning",
            "- Use `docs/superpowers/AGENT_REPORT_TEMPLATE.md` for reporting",
        ]
    )
    return "\n".join(lines)


def next_module(after: str | None = None) -> str:
    workflow_manifest = load_workflow_manifest()
    order = workflow_manifest["first_run_order"]
    if after is None:
        return order[0]
    index = order.index(after)
    if index + 1 >= len(order):
        raise ValueError(f"No module follows {after}")
    return order[index + 1]


def _run_command(command: list[str], *, cwd: Path) -> None:
    rendered = " ".join(shlex.quote(part) for part in command)
    print(f"\n$ {rendered}")
    subprocess.run(command, cwd=cwd, check=True)


def _run_module_checks(module_id: str, *, execute: bool, strict: bool) -> int:
    module = get_module_spec(module_id)
    issues = validate_manifest()
    module_targets = discover_test_targets(module)

    if issues:
        for issue in issues:
            print(f"manifest: {issue}")
        if strict:
            return 1

    if not module_targets:
        print(f"{module_id}: no test targets discovered")
        return 1 if strict else 0

    command = [sys.executable, "-m", "pytest", *[str(path.relative_to(REPO_ROOT)) for path in module_targets], "-q"]
    print(f"{module_id}: discovered {len(module_targets)} test target(s)")
    for target in module_targets:
        print(f"- {target.relative_to(REPO_ROOT).as_posix()}")
    print(f"Suggested command: {' '.join(shlex.quote(part) for part in command)}")

    if execute:
        _run_command(command, cwd=REPO_ROOT)
    return 0


def _add_task_card_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("module_id")
    parser.add_argument("--goal", required=True, help="Required user goal for the task card.")
    parser.add_argument(
        "--acceptance",
        action="append",
        default=[],
        help="Repeatable or newline-delimited acceptance criterion.",
    )
    parser.add_argument(
        "--non-goals",
        action="append",
        default=[],
        help="Repeatable or newline-delimited non-goal.",
    )
    parser.add_argument(
        "--risks",
        action="append",
        default=[],
        help="Repeatable or newline-delimited risk.",
    )


def _add_draft_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("module_id")
    parser.add_argument(
        "--instruction",
        action="append",
        default=[],
        help="Repeatable human instruction or constraint that should influence the draft.",
    )
    parser.add_argument(
        "--write",
        help="Optional path to write the draft JSON file for human review.",
    )


def _add_split_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--goal",
        required=True,
        help="Project-level goal or request to decompose.",
    )
    parser.add_argument(
        "--context",
        action="append",
        default=[],
        help="Optional extra context or constraints that should influence decomposition.",
    )
    parser.add_argument(
        "--write",
        help="Optional path to write the decomposition proposal JSON file.",
    )


def _add_review_split_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--from-split",
        required=True,
        help="Path to a decomposition proposal JSON file.",
    )
    parser.add_argument(
        "--write",
        help="Optional path to write the reviewed decomposition JSON file.",
    )


def _add_approve_split_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--from-split",
        required=True,
        help="Path to a decomposition proposal JSON file to approve.",
    )
    parser.add_argument(
        "--write",
        help="Optional path to write the approved decomposition JSON file. Defaults to <from-split>.approved.json.",
    )


def _add_spawn_decomposition_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--from-split",
        required=True,
        help="Path to an approved decomposition proposal JSON file.",
    )
    parser.add_argument(
        "--write",
        help="Optional path to write the spawn-ready decomposition JSON file.",
    )
    parser.add_argument(
        "--emit-dir",
        help="Optional directory to emit one file per spawned role plus a manifest.json bundle. Module execution bundles are also emitted under <emit-dir>/modules.",
    )


def _add_review_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--from-draft",
        required=True,
        help="Path to a reviewed draft JSON file marked Approved.",
    )
    parser.add_argument(
        "--write",
        help="Optional path to write the approved spawn payload JSON file.",
    )


def _print_plan() -> None:
    workflow_manifest = load_workflow_manifest()
    print("# Workflow Plan")
    for phase in workflow_manifest["phases"]:
        print(f"\n## {phase['name']}")
        for module_id in phase["modules"]:
            roles = workflow_manifest["module_roles"][module_id]
            print(
                f"- {module_id}: {roles['developer']} -> {roles.get('senior_developer', 'Senior Developer')} -> {roles['tester']} -> {roles['analyzer']}"
                + (
                    f" -> {roles['reviewer']}"
                    if roles.get("reviewer")
                    else ""
                )
                + (
                    f" -> {roles['git_master']}"
                    if roles.get("git_master")
                    else ""
                )
                + f" -> {roles['gate']}"
            )


def _role_slug(role: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", role.casefold()).strip("-")


def _proposal_module_ids(proposal: dict) -> list[str]:
    module_ids: list[str] = []
    seen: set[str] = set()
    for phase in proposal.get("phase_plan", []):
        for module_id in phase.get("modules", []):
            if module_id in seen:
                continue
            seen.add(module_id)
            module_ids.append(module_id)
    return module_ids


def _module_execution_bundle_data(module_id: str) -> dict:
    draft = build_task_draft(module_id)
    approved_draft = dict(draft)
    approved_draft["status"] = "Approved"
    spawn_payload = json.loads(build_approved_spawn_payload_from_draft(approved_draft))
    package = _module_package_data(module_id)
    return {
        "module_id": module_id,
        "title": package["title"],
        "phase": package["phase"],
        "workflow_roles": package["workflow_roles"],
        "read_first": package["read_first"],
        "only_edit": package["only_edit"],
        "suggested_checks": package["suggested_checks"],
        "draft": draft,
        "review_markdown": _render_draft_review(draft),
        "approved_draft": approved_draft,
        "spawn": spawn_payload,
    }


def _render_module_execution_bundle_readme(bundle_name: str, module_bundle: dict) -> str:
    lines = [
        f"# {bundle_name}",
        "",
        "This directory is a Codex-ready module execution bundle.",
        "",
        "## Read Order",
        "",
        "- `draft.json`",
        "- `review.md`",
        "- `approved.json`",
        "- `spawn.json`",
        "",
        "## How To Use",
        "",
        "- Read the draft first, then review, then approved, then spawn.",
        "- The approved draft is the single source of truth for the final spawn payload.",
        "- Use the `spawn.json` file when launching the Codex subagent.",
        "",
        "## Module",
        "",
        f"- `Module:` `{module_bundle['module_id']}`",
        f"- `Title:` `{module_bundle['title']}`",
        f"- `Phase:` `{module_bundle['phase']}`",
    ]
    return "\n".join(lines)


def _write_module_execution_bundle(output_dir: Path, module_id: str) -> None:
    bundle = _module_execution_bundle_data(module_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "workflow": "Module Execution",
        "status": "ReadyForSpawn",
        "module_id": bundle["module_id"],
        "title": bundle["title"],
        "phase": bundle["phase"],
        "read_first": bundle["read_first"],
        "only_edit": bundle["only_edit"],
        "suggested_checks": bundle["suggested_checks"],
        "files": {
            "draft": "draft.json",
            "review": "review.md",
            "approved": "approved.json",
            "spawn": "spawn.json",
        },
    }
    write_json_file(output_dir / "manifest.json", manifest)
    (output_dir / "README.md").write_text(
        _render_module_execution_bundle_readme(output_dir.name, bundle),
        encoding="utf-8",
    )
    write_json_file(output_dir / "draft.json", bundle["draft"])
    (output_dir / "review.md").write_text(bundle["review_markdown"], encoding="utf-8")
    write_json_file(output_dir / "approved.json", bundle["approved_draft"])
    write_json_file(output_dir / "spawn.json", bundle["spawn"])


def _write_decomposition_spawn_bundle(output_dir: Path, payload: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json_file(output_dir / "manifest.json", payload)
    (output_dir / "README.md").write_text(
        _render_decomposition_spawn_bundle_readme(output_dir.name, payload),
        encoding="utf-8",
    )
    for index, group in enumerate(payload["spawn_groups"], start=1):
        for agent in group["agents"]:
            role = agent["role"]
            role_slug = _role_slug(role)
            role_index = payload["spawn_order"].index(role) + 1
            role_payload = {
                "workflow": payload["workflow"],
                "status": payload["status"],
                "role": role,
                "group": group["name"],
                "group_mode": group["mode"],
                "spawn_order": role_index,
                "depends_on": agent["depends_on"],
                "spawn_agent": agent["spawn_agent"],
                "source_proposal": payload["source_proposal"],
            }
            write_json_file(output_dir / f"{role_index:02d}-{role_slug}.json", role_payload)


def _render_decomposition_spawn_bundle_readme(bundle_name: str, payload: dict) -> str:
    lines = [
        f"# {bundle_name}",
        "",
        "This directory is a Codex-ready project decomposition spawn bundle.",
        "",
        "## Read Order",
        "",
        "- `README.md`",
        "- `manifest.json`",
    ]
    for index, role in enumerate(payload["spawn_order"], start=1):
        lines.append(f"- `{index:02d}-{_role_slug(role)}.json`")
    lines.extend(
        [
            "",
            "## How To Use",
            "",
            "- Read `manifest.json` to inspect the approved split, spawn groups, and source proposal.",
            "- Read the role files in order.",
            "- For each role file, copy `spawn_agent.message` and `spawn_agent.items` into the Codex session that will launch the agent.",
            "- The `Technical Writer` file is the final synthesis step and depends on the review pack.",
            "- If module bundles are present under `modules/`, run each module through draft, review, approved, and spawn in order.",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Project-level agent workflow helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("plan", help="Print the workflow phases and module assignments.")

    package_parser = subparsers.add_parser(
        "package",
        help="Print a complete task package for a specific module.",
    )
    package_parser.add_argument("module_id")

    task_card_parser = subparsers.add_parser(
        "task-card",
        help="Print a Markdown task card for a module and explicit task inputs.",
    )
    _add_task_card_arguments(task_card_parser)

    draft_parser = subparsers.add_parser(
        "draft",
        help="Generate a draft task card from module contract sections.",
    )
    _add_draft_arguments(draft_parser)

    split_parser = subparsers.add_parser(
        "split",
        help="Generate a project decomposition proposal before module-level workflow.",
    )
    _add_split_arguments(split_parser)

    review_split_parser = subparsers.add_parser(
        "review-split",
        help="Review a decomposition proposal before module-level workflow.",
    )
    _add_review_split_arguments(review_split_parser)

    approve_split_parser = subparsers.add_parser(
        "approve-split",
        help="Approve a decomposition proposal before module-level workflow.",
    )
    _add_approve_split_arguments(approve_split_parser)

    spawn_decomposition_parser = subparsers.add_parser(
        "spawn-decomposition",
        help="Build spawn-ready agent packets from an approved decomposition proposal.",
    )
    _add_spawn_decomposition_arguments(spawn_decomposition_parser)

    brief_parser = subparsers.add_parser(
        "brief",
        help="Alias for task-card.",
    )
    _add_task_card_arguments(brief_parser)

    spawn_parser = subparsers.add_parser(
        "spawn-text",
        help="Print a manual Codex spawn_agent payload for a specific module.",
    )
    spawn_parser.add_argument("module_id")

    spawn_task_parser = subparsers.add_parser(
        "spawn-task",
        help="Print a spawn payload that includes module package and task card data.",
    )
    _add_task_card_arguments(spawn_task_parser)

    approve_parser = subparsers.add_parser(
        "approve",
        help="Approve a reviewed draft and emit the final spawn payload.",
    )
    _add_review_arguments(approve_parser)

    spawn_alias_parser = subparsers.add_parser(
        "spawn",
        help="Alias for spawn-text.",
    )
    spawn_alias_parser.add_argument("module_id")

    dispatch_parser = subparsers.add_parser(
        "dispatch",
        help="Build a dispatch brief for a specific module.",
    )
    dispatch_parser.add_argument("module_id")

    next_parser = subparsers.add_parser(
        "next",
        help="Print the next module in the first-run order.",
    )
    next_parser.add_argument("--after", help="Return the module after the given module id.")

    check_parser = subparsers.add_parser(
        "check",
        help="Validate a module workflow contract and optionally run its tests.",
    )
    check_parser.add_argument("module_id", nargs="?")
    check_parser.add_argument("--all", action="store_true", help="Check all modules.")
    check_parser.add_argument("--execute", action="store_true", help="Run the discovered tests.")
    check_parser.add_argument("--strict", action="store_true", help="Fail on missing tests or manifest issues.")

    audit_parser = subparsers.add_parser(
        "audit-manifest",
        help="Validate the workflow and task manifests without running tests.",
    )
    audit_parser.add_argument("--strict", action="store_true", help="Fail on any manifest issue.")

    args = parser.parse_args(argv)

    if args.command == "plan":
        _print_plan()
        return 0
    if args.command == "package":
        print(build_task_package(args.module_id))
        return 0
    if args.command in {"task-card", "brief"}:
        print(
            build_task_card(
                args.module_id,
                goal=args.goal,
                acceptance=_normalize_task_items(args.acceptance),
                non_goals=_normalize_task_items(args.non_goals),
                risks=_normalize_task_items(args.risks),
            )
        )
        return 0
    if args.command == "draft":
        draft = build_task_draft(args.module_id, instructions=_normalize_task_items(args.instruction))
        if args.write:
            write_json_file(Path(args.write), draft)
        print(_render_draft_review(draft))
        return 0
    if args.command == "split":
        proposal = build_project_decomposition(
            args.goal,
            context=_normalize_task_items(args.context),
        )
        if args.write:
            write_json_file(Path(args.write), proposal)
        print(proposal["markdown"])
        return 0
    if args.command == "review-split":
        proposal = _load_json(Path(args.from_split))
        if args.write:
            write_json_file(Path(args.write), proposal)
        print(proposal["markdown"])
        return 0
    if args.command == "approve-split":
        from_split = Path(args.from_split)
        proposal = _load_json(from_split)
        try:
            approved = build_approved_project_decomposition_from_proposal(proposal)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        write_json_file(Path(args.write) if args.write else _default_approved_split_path(from_split), approved)
        print(json.dumps(approved, indent=2, ensure_ascii=False))
        return 0
    if args.command == "spawn-decomposition":
        from_split = Path(args.from_split)
        proposal = _load_json(from_split)
        try:
            spawn_payload = build_decomposition_spawn_payload(proposal)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.write:
            write_json_file(Path(args.write), spawn_payload)
        if args.emit_dir:
            emit_dir = Path(args.emit_dir)
            _write_decomposition_spawn_bundle(emit_dir, spawn_payload)
            for index, module_id in enumerate(_proposal_module_ids(proposal), start=1):
                module_bundle_dir = emit_dir / "modules" / f"{index:02d}-{_role_slug(module_id)}"
                _write_module_execution_bundle(module_bundle_dir, module_id)
        print(json.dumps(spawn_payload, indent=2, ensure_ascii=False))
        return 0
    if args.command in {"spawn-text", "spawn"}:
        print(build_spawn_payload(args.module_id))
        return 0
    if args.command == "spawn-task":
        print(
            build_spawn_task_payload(
                args.module_id,
                goal=args.goal,
                acceptance=_normalize_task_items(args.acceptance),
                non_goals=_normalize_task_items(args.non_goals),
                risks=_normalize_task_items(args.risks),
            )
        )
        return 0
    if args.command == "approve":
        draft = _load_json(Path(args.from_draft))
        try:
            payload = json.loads(build_approved_spawn_payload_from_draft(draft))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.write:
            write_json_file(Path(args.write), payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if args.command == "dispatch":
        print(build_dispatch_brief(args.module_id))
        return 0
    if args.command == "next":
        print(next_module(args.after))
        return 0
    if args.command == "audit-manifest":
        issues = validate_manifest()
        if not issues:
            print("workflow_manifest: OK")
            return 0
        for issue in issues:
            print(f"workflow_manifest: {issue}")
        return 1 if args.strict else 0
    if args.command == "check":
        if args.all:
            exit_code = 0
            for module_id in load_workflow_manifest()["first_run_order"]:
                exit_code = max(exit_code, _run_module_checks(module_id, execute=args.execute, strict=args.strict))
            return exit_code
        if args.module_id is None:
            parser.error("check requires a module_id or --all")
        return _run_module_checks(args.module_id, execute=args.execute, strict=args.strict)

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
