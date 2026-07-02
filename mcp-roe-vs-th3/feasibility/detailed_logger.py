"""Detailed logger — ghi mọi event xảy ra trong 1 episode.

Định dạng: JSONL (1 event = 1 line JSON), append-only. Có thể parse lại bằng
`jq`, `pandas.read_json(lines=True)`, hoặc script tùy ý.

Mỗi event có schema:
    {
      "ts": "2026-06-27T08:15:32.123456",
      "step": 42,
      "agent": "blue_agent_4",
      "event": "<event_type>",
      "data": { ... payload phụ thuộc event_type ... }
    }

Các event_type được ghi:

  step_start          — bắt đầu step, kèm raw observation (full)
  state_extracted     — sau extract_state, kèm structured state (full)
  llm_query           — gửi prompt cho Claude (full system + user message)
  llm_response_chunk  — mỗi text block Claude trả về
  tool_call           — Claude gọi tool (name + args)
  tool_result         — tool trả kết quả (full payload)
  roe_verdict         — RoE thẩm định propose_* (allowed/denied + reason)
  action_proposed     — proposed_action được set trong StepContext
  action_materialized — final CybORG Action object
  step_end            — kết thúc step (joint_reward, wall_time, token_counts)
  episode_start       — đầu episode (setup, mode_flags, red_variant, seed)
  episode_end         — cuối episode (cumulative_reward, total_wall_time)
  error               — lỗi xảy ra (traceback)

Mọi field được serialize an toàn — object không-JSON-able (CybORG Action, numpy
array, etc.) sẽ stringify bằng repr().
"""

import json
import os
import traceback
from datetime import datetime
from pathlib import Path


def _safe_serialize(obj):
    """Convert object thành JSON-safe representation."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, set):
        return [_safe_serialize(x) for x in obj]
    if hasattr(obj, "__dict__"):
        return {"_class": type(obj).__name__, "_repr": repr(obj)[:500]}
    try:
        return repr(obj)[:500]
    except Exception:
        return "<unrepresentable>"


class DetailedLogger:
    """Per-episode detailed JSONL logger."""

    def __init__(self, path: str, agent_name: str = "?", episode_meta: dict = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.agent_name = agent_name
        self.step = 0
        self.episode_meta = episode_meta or {}
        # APPEND mode — KHÔNG ghi đè khi resume. Phân biệt run mới vs resume
        # bằng cách kiểm tra file đã có nội dung chưa.
        file_exists = self.path.exists() and self.path.stat().st_size > 0
        self._fp = open(self.path, "a", encoding="utf-8", buffering=1)  # line-buffered
        if not file_exists:
            # File mới — ghi episode_start
            self.event("episode_start", data=self.episode_meta)
        else:
            # Resume — ghi episode_resume thay vì episode_start để không trùng
            self.event("episode_resume", data=self.episode_meta)

    def set_step(self, step: int):
        self.step = step

    def event(self, event_type: str, data=None, agent: str = None):
        """Ghi 1 event."""
        record = {
            "ts": datetime.utcnow().isoformat(),
            "step": self.step,
            "agent": agent or self.agent_name,
            "event": event_type,
            "data": _safe_serialize(data) if data is not None else None,
        }
        try:
            self._fp.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            # Last resort — ghi error mà không crash episode
            self._fp.write(json.dumps({
                "ts": datetime.utcnow().isoformat(),
                "step": self.step,
                "agent": self.agent_name,
                "event": "logger_error",
                "data": {"error": str(e), "original_event": event_type},
            }) + "\n")

    # ─── Convenience methods ────────────────────────────────────────────────

    def step_start(self, raw_observation):
        self.event("step_start", data={"raw_observation": raw_observation})

    def state_extracted(self, state):
        self.event("state_extracted", data={"state": state})

    def llm_query(self, system_prompt: str, user_message: str, mode: str, opts_summary: dict = None):
        self.event("llm_query", data={
            "mode": mode,  # "mcp" hoặc "paper"
            "system_prompt": system_prompt,
            "user_message": user_message,
            "opts": opts_summary or {},
        })

    def llm_response_chunk(self, text: str):
        self.event("llm_response_chunk", data={"text": text})

    def tool_call(self, name: str, args: dict):
        self.event("tool_call", data={"name": name, "args": args})

    def tool_result(self, name: str, payload):
        self.event("tool_result", data={"name": name, "payload": payload})

    def roe_verdict(self, action_type: str, params: dict, allowed: bool, reason: str, suggested: str):
        self.event("roe_verdict", data={
            "action_type": action_type,
            "params": params,
            "allowed": allowed,
            "reason": reason,
            "suggested": suggested,
        })

    def action_proposed(self, action_type: str, params: dict, reason: str):
        self.event("action_proposed", data={
            "action_type": action_type,
            "params": params,
            "reason": reason,
        })

    def action_materialized(self, final_str: str, cyborg_action_repr: str):
        self.event("action_materialized", data={
            "final_str": final_str,
            "cyborg_action": cyborg_action_repr,
        })

    def step_end(self, joint_reward: float, wall_time_s: float, n_proposed: int = 0,
                 n_rejected: int = 0, n_tool_calls: int = 0):
        self.event("step_end", data={
            "joint_reward": joint_reward,
            "wall_time_s": wall_time_s,
            "n_proposed": n_proposed,
            "n_rejected": n_rejected,
            "n_tool_calls": n_tool_calls,
        })

    def error(self, where: str, exc: Exception):
        self.event("error", data={
            "where": where,
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        })

    def episode_end(self, cumulative_reward: float, total_wall_time_s: float, n_steps: int):
        self.event("episode_end", data={
            "cumulative_reward": cumulative_reward,
            "total_wall_time_s": total_wall_time_s,
            "n_steps": n_steps,
        })

    def close(self):
        try:
            self._fp.flush()
            self._fp.close()
        except Exception:
            pass


# ─── No-op fallback (khi không có logger được khởi tạo) ──────────────────────

class _NullLogger:
    """No-op logger — dùng khi không có DetailedLogger được set."""
    def __getattr__(self, name):
        def noop(*args, **kwargs):
            pass
        return noop


_NULL = _NullLogger()


def get_logger():
    """Trả về logger hiện tại (gán bởi ClaudeDefenderPolicy) hoặc no-op."""
    from .context import StepContext
    return StepContext.logger or _NULL
