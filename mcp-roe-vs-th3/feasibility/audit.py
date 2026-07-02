"""CSV audit log — tóm tắt per-step cho extract_metrics.

Log đầy đủ (full prompt, full response, từng tool call, RoE verdict, raw obs,
state extracted, timing) được ghi ở `detailed_*.jsonl` cùng episode.

CSV này dùng cho:
- Compute invalid-action rate = #(final_action == 'Sleep (no action proposed)') / N
- Compute RoE deny rate       = #(roe_rejections != '') / N
- Annotation source           = llm_reasoning column (tóm tắt)
"""

import csv
from datetime import datetime
from pathlib import Path


class AuditLog:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # APPEND mode — không ghi đè khi resume từ checkpoint.
        # Header chỉ ghi khi file mới chưa tồn tại.
        file_exists = self.path.exists() and self.path.stat().st_size > 0
        self._fp = open(self.path, "a", newline="", encoding="utf-8")
        self._writer = csv.writer(self._fp)
        if not file_exists:
            self._writer.writerow([
                "timestamp", "step", "agent",
                "phase", "threats_count", "comms_count",
                "llm_reasoning", "proposed_action",
                "roe_rejections", "final_action",
            ])

    def log(self, step, agent, state, llm_reasoning, proposed, rejected, final):
        # CSV chỉ giữ tóm tắt — log đầy đủ ở detailed_*.jsonl cùng episode
        self._writer.writerow([
            datetime.utcnow().isoformat(),
            step, agent,
            (state or {}).get("mission_phase"),
            len((state or {}).get("threats", [])),
            len((state or {}).get("comms", [])),
            (llm_reasoning or "")[:2000],
            str(proposed),
            "; ".join(f"{a}({h}): {r}" for a, h, r in (rejected or [])),
            str(final),
        ])
        self._fp.flush()

    def close(self):
        self._fp.close()
