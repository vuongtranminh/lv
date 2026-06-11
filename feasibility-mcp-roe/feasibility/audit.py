"""CSV audit log — every step's full decision flow.

This is the primary data source for Phase 2 analysis:
- Compute invalid-action rate = #(final_action == 'Sleep (no action proposed)') / N
- Compute RoE deny rate       = #(roe_rejections != '') / N
- Manual annotation source    = llm_reasoning column
"""

import csv
from datetime import datetime
from pathlib import Path


class AuditLog:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fp = open(self.path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._fp)
        self._writer.writerow([
            "timestamp", "step", "agent",
            "phase", "threats_count", "comms_count",
            "llm_reasoning", "proposed_action",
            "roe_rejections", "final_action",
        ])

    def log(self, step, agent, state, llm_reasoning, proposed, rejected, final):
        self._writer.writerow([
            datetime.utcnow().isoformat(),
            step, agent,
            (state or {}).get("mission_phase"),
            len((state or {}).get("threats", [])),
            len((state or {}).get("comms", [])),
            (llm_reasoning or "")[:500],
            str(proposed),
            "; ".join(f"{a}({h}): {r[:80]}" for a, h, r in (rejected or [])),
            str(final),
        ])
        self._fp.flush()

    def close(self):
        self._fp.close()
