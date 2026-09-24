"""Incremental crash-recovery manifest backed by JSON lines + fsync."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

InvocationShape = Literal["thin", "rich", "resumed"]


class Step(BaseModel):
    model_config = ConfigDict(frozen=True)

    step_id: str
    name: str
    ts: datetime
    invocation_shape: InvocationShape
    payload: dict[str, Any]


class ManifestState(BaseModel):
    complete: bool
    steps: list[Step]


class Manifest:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append_step(self, step: Step) -> None:
        # Make sure the parent directory exists.
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize the step as one UTF-8 JSON line.
        data = (step.model_dump_json() + "\n").encode("utf-8")

        # Binary append mode is required for reliable fsync semantics.
        with open(self.path, "ab") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

    @classmethod
    def load(cls, path: Path) -> ManifestState:
        # Missing manifest means an empty, incomplete state.
        if not path.exists():
            return ManifestState(complete=False, steps=[])

        steps: list[Step] = []

        # Read each non-empty JSONL line and validate it as a Step.
        with open(path, "r") as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                steps.append(Step.model_validate_json(line))

        # Only the final "complete" step marks the manifest complete.
        complete = bool(steps) and steps[-1].name == "complete"

        return ManifestState(complete=complete, steps=steps)