"""Pretty-print 1 episode từ file detailed_*.jsonl.

Sử dụng:
    python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl
    python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl --step 42
    python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl --grep "Restore"
    python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl --summary

Mục đích:
- Đọc lại từng step để hiểu LLM đã suy luận thế nào
- Trích đoạn cho báo cáo luận văn (vd "Setup C step 142: LLM gọi Restore, RoE deny vì host chưa admin")
- Debug khi nghi LLM hiểu sai
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list:
    """Load JSONL file → list of records."""
    records = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  ⚠ line {i+1} parse fail: {e}", file=sys.stderr)
    return records


def truncate(s, n=200):
    if s is None:
        return ""
    s = str(s)
    if len(s) <= n:
        return s
    return s[:n] + f"... [+{len(s)-n} chars]"


def print_event(rec, full=False):
    """Pretty-print 1 event."""
    ts = rec["ts"][:19]  # cắt giây
    step = rec["step"]
    ev = rec["event"]
    data = rec.get("data") or {}

    if ev == "episode_start":
        print(f"\n=== EPISODE START ===")
        for k, v in data.items():
            print(f"  {k}: {v}")
        return

    if ev == "episode_end":
        print(f"\n=== EPISODE END ===")
        print(f"  cumulative_reward: {data.get('cumulative_reward'):.2f}")
        print(f"  total_wall_time:   {data.get('total_wall_time_s'):.1f}s")
        print(f"  n_steps:           {data.get('n_steps')}")
        return

    prefix = f"[step {step:>3} {ts}] {ev}"

    if ev == "step_start":
        print(f"\n{prefix}")
        if full:
            print(f"  raw_obs: {truncate(json.dumps(data.get('raw_observation'), ensure_ascii=False), 1000)}")
    elif ev == "state_extracted":
        st = data.get("state", {})
        print(f"  └ state: phase={st.get('mission_phase')}, "
              f"threats={len(st.get('threats', []))}, "
              f"comms={len(st.get('comms', []))}")
        if full:
            print(f"    {json.dumps(st, ensure_ascii=False, indent=2)}")
    elif ev == "llm_query":
        mode = data.get("mode")
        user = data.get("user_message", "")
        print(f"  └ llm_query [{mode}]:")
        if full:
            print(f"    SYSTEM PROMPT:\n{truncate(data.get('system_prompt'), 2000)}\n")
            print(f"    USER MESSAGE:\n{user}")
        else:
            print(f"    user msg (first 200): {truncate(user, 200)}")
    elif ev == "llm_response_chunk":
        text = data.get("text", "")
        print(f"  └ llm_says: {truncate(text, 300)}")
    elif ev == "tool_call":
        print(f"  └ TOOL_CALL {data.get('name')}({data.get('args')})")
    elif ev == "tool_result":
        payload = data.get("payload")
        print(f"  └ TOOL_RESULT {data.get('name')} → {truncate(json.dumps(payload, ensure_ascii=False), 200)}")
    elif ev == "roe_verdict":
        allowed = data.get("allowed")
        symbol = "✓" if allowed else "✗"
        print(f"  └ RoE {symbol} {data.get('action_type')}({data.get('params')}): {data.get('reason') or 'allowed'}")
        if not allowed and data.get("suggested"):
            print(f"    suggested: {data.get('suggested')}")
    elif ev == "action_proposed":
        print(f"  └ PROPOSED {data.get('action_type')}({data.get('params')})  reason: {truncate(data.get('reason'), 100)}")
    elif ev == "action_materialized":
        print(f"  └ FINAL: {data.get('final_str')}")
    elif ev == "step_end":
        print(f"  └ step_end wall={data.get('wall_time_s'):.2f}s "
              f"proposed={data.get('n_proposed')} rejected={data.get('n_rejected')}")
    elif ev == "paper_parse_result":
        print(f"  └ paper_parse: {data.get('action_type')}({data.get('params')})")
    elif ev == "paper_parse_failed":
        print(f"  └ paper_parse FAILED — response: {truncate(data.get('response_preview'), 200)}")
    elif ev == "error":
        print(f"  └ ⚠ ERROR @ {data.get('where')}: {data.get('message')}")
        if full:
            print(f"    {data.get('traceback')}")
    else:
        print(f"  └ {ev}: {truncate(json.dumps(data, ensure_ascii=False), 200)}")


def summary(records: list):
    """Bảng tổng hợp ngắn cho 1 episode."""
    event_counts = Counter(r["event"] for r in records)
    print("=== TỔNG HỢP EVENT ===")
    for ev, n in sorted(event_counts.items(), key=lambda x: -x[1]):
        print(f"  {ev:30s} {n}")
    print()

    # Đếm tool call cụ thể
    tool_calls = Counter(r["data"]["name"] for r in records
                         if r["event"] == "tool_call" and r.get("data"))
    if tool_calls:
        print("=== TOOL CALLS ===")
        for tool, n in tool_calls.most_common():
            print(f"  {tool:30s} {n}")
        print()

    # Đếm RoE verdict
    roe_verdicts = [r for r in records if r["event"] == "roe_verdict"]
    n_allowed = sum(1 for r in roe_verdicts if r["data"].get("allowed"))
    n_denied = len(roe_verdicts) - n_allowed
    print(f"=== RoE ===")
    print(f"  allowed: {n_allowed}")
    print(f"  denied:  {n_denied}")
    if n_denied:
        print(f"\n  Top deny reasons:")
        deny_reasons = Counter(r["data"]["reason"] for r in roe_verdicts
                               if not r["data"].get("allowed"))
        for reason, n in deny_reasons.most_common(5):
            print(f"    [{n}x] {reason}")
    print()

    # Final action distribution
    actions = Counter()
    for r in records:
        if r["event"] == "action_materialized":
            final = r["data"].get("final_str", "")
            # Lấy phần trước (
            kind = final.split("(")[0]
            actions[kind] += 1
    print("=== HÀNH ĐỘNG CUỐI ===")
    for act, n in actions.most_common():
        print(f"  {act:30s} {n}")


def main():
    parser = argparse.ArgumentParser(description="Pretty-print 1 episode JSONL")
    parser.add_argument("path", type=str, help="Đường dẫn detailed_*.jsonl")
    parser.add_argument("--step", type=int, help="Chỉ in step cụ thể")
    parser.add_argument("--grep", type=str, help="Lọc event chứa keyword (case-insensitive)")
    parser.add_argument("--summary", action="store_true", help="In bảng tổng hợp event/step")
    parser.add_argument("--full", action="store_true", help="In full system prompt + user message + obs (rất dài)")
    parser.add_argument("--from-step", type=int, default=0, help="In từ step này")
    parser.add_argument("--to-step", type=int, default=10**9, help="In đến step này")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: file không tồn tại: {path}", file=sys.stderr)
        sys.exit(1)

    records = load_jsonl(path)
    print(f"Đã load {len(records)} event từ {path}\n")

    if args.summary:
        summary(records)
        return

    for r in records:
        step = r.get("step", 0)
        if args.step is not None and step != args.step:
            continue
        if step < args.from_step or step > args.to_step:
            continue
        if args.grep:
            blob = json.dumps(r, ensure_ascii=False).lower()
            if args.grep.lower() not in blob:
                continue
        print_event(r, full=args.full)


if __name__ == "__main__":
    main()
