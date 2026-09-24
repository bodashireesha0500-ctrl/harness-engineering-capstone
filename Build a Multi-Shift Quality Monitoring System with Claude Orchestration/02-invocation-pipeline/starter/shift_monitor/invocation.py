"""Three invocation shapes.

thin     — prompt only.
rich     — hot state + new defects.
resumed  — prior partial findings + new defects since the last manifest step.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from .state import HotState

InvocationShape = Literal["thin", "rich", "resumed"]


@dataclass(frozen=True)
class Invocation:
    shape: InvocationShape
    prompt: str


def thin(prompt: str) -> Invocation:
    return Invocation(shape="thin", prompt=prompt)


def rich(
    role: str,
    hot_state: HotState,
    new_defects: Sequence[Mapping[str, Any]],
) -> Invocation:
    prompt = f"""You are the on-call {role} for Northridge Plant 3.

## Current hot state
{hot_state.current_shift_summary}

Active alerts:
{hot_state.active_alerts}

Threshold statuses:
{hot_state.threshold_statuses}

## New defects since last shift
"""

    if new_defects:
        for defect in new_defects:
            prompt += (
                f"- {defect.get('id', '')} / "
                f"{defect.get('ts', '')} / "
                f"{defect.get('shift', '')} / "
                f"{defect.get('component', '')} / "
                f"{defect.get('severity', '')} / "
                f"{defect.get('description', '')}\n"
            )
    else:
        prompt += "- (none)\n"

    prompt += """
Provide:
- Summary
- Findings
- Recommended actions
- An Updated hot state proposal as a JSON block.
"""

    return Invocation(shape="rich", prompt=prompt)


def resumed(
    session_id: str,
    summary: str,
    latest_message: str,
    prior_steps: Sequence[Mapping[str, Any]],
    new_defects: Sequence[Mapping[str, Any]],
) -> Invocation:
    prompt = "## Prior partial findings\n"

    if prior_steps:
        for step in prior_steps:
            name = step.get("name", "")
            payload = step.get("payload", "")
            prompt += f"- {name}: {payload}\n"
    else:
        prompt += "- (none)\n"

    prompt += f"""
## Prior summary
{summary}

## New defects since last partial step
"""

    if new_defects:
        for defect in new_defects:
            prompt += (
                f"- {defect.get('id', '')} / "
                f"{defect.get('ts', '')} / "
                f"{defect.get('component', '')} / "
                f"{defect.get('severity', '')} / "
                f"{defect.get('description', '')}\n"
            )
    else:
        prompt += "- (none)\n"

    prompt += f"""
## Latest instruction
{latest_message}
"""

    return Invocation(shape="resumed", prompt=prompt)