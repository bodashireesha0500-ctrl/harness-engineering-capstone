"""Resume-vs-fresh decision logic for crash recovery.

The 30-minute threshold is ~1/16 of an 8-hour shift cycle: a resume inside this
window is still operating on the same shift's working set; anything older is
treated as a stale partial that should be re-started from scratch with whatever
findings the manifest already captured injected as a summary.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from .manifest import ManifestState

# TODO: Name the staleness threshold as a module-level constant
# STALE_RESUME_THRESHOLD_MINUTES = 30. The number is not arbitrary — it's about
# one-sixteenth of an 8-hour shift; resumes within this window are still on the
# same shift's working set. Document the rationale in a comment.
STALE_RESUME_THRESHOLD_MINUTES = 30  # TODO: confirm and document

Decision = Literal["resume", "fresh"]


def decide(state: ManifestState, now: datetime) -> str:
    # A completed manifest should not be resumed.
    if state.complete:
        return "fresh"

    # No recorded steps means there is nothing to resume.
    if not state.steps:
        return "fresh"

    # Compare now with the timestamp of the latest recorded step.
    last_ts = state.steps[-1].ts
    age = now - last_ts

    # Resume if the partial run is within the stale threshold.
    # At exactly 30 minutes, resume wins.
    if age <= timedelta(minutes=STALE_RESUME_THRESHOLD_MINUTES):
        return "resume"

    return "fresh"