"""Extract 5 metrics M1-M5 từ audit logs + joint reward files.

M1 — Episode joint reward (mean ± std qua các episode/red variant)
M2 — Invalid action rate: tỷ lệ action LLM proposed nhưng bị reject hoặc
     không materialize hợp lệ → cho thấy độ trung thành schema.
M3 — RoE deny rate: tỷ lệ proposed bị RoE từ chối (chỉ áp dụng Setup C).
M4 — Comms misread rate: tỷ lệ comm decode sai (cần ground truth — Setup A
     đo gián tiếp qua log raw vector; B/C không có misread vì decoder pre-parse).
M5 — Step latency: trung bình thời gian / step (giây).

Sử dụng:
    python benchmark/extract_metrics.py
    python benchmark/extract_metrics.py --setup C
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

RESULTS_DIR = Path(__file__).parent / "results"


def load_episode_meta(filepath: Path) -> dict:
    """Load joint reward file."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def parse_audit_csv(filepath: Path) -> list:
    """Parse audit log CSV (mỗi row = 1 step)."""
    if not filepath.exists():
        return []
    with open(filepath, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_metrics_for_episode(meta: dict, audit_rows: list) -> dict:
    """Compute M1-M5 cho 1 episode."""
    setup = meta["setup"]
    n_steps = len(audit_rows) if audit_rows else len(meta.get("step_rewards", []))

    # M1: cumulative joint reward
    m1 = meta["cumulative_joint_reward"]

    # M2/M3: parse audit rows
    n_invalid = 0
    n_denied = 0
    n_proposed = 0
    for row in audit_rows:
        final = row.get("final_action", "")
        proposed = row.get("proposed_action", "")
        rejected = row.get("roe_rejections", "")

        if proposed and proposed not in ("None", ""):
            n_proposed += 1
        # final = "Sleep (no action proposed)" → invalid
        if "no action proposed" in final.lower() or "parse fail" in final.lower():
            n_invalid += 1
        # rejected có nội dung → RoE denied
        if rejected and rejected.strip() not in ("", "None", "[]"):
            n_denied += 1

    m2 = (n_invalid / n_steps) if n_steps > 0 else 0.0
    m3 = (n_denied / n_proposed) if n_proposed > 0 else 0.0

    # M4: comms misread — proxy bằng số lần LLM hiểu sai vector. Setup A
    # (paper baseline) đếm qua keyword trong llm_reasoning; B/C dùng decoder
    # pre-parse nên gần 0 by design.
    n_misread = 0
    for row in audit_rows:
        reasoning = (row.get("llm_reasoning") or "").lower()
        # Heuristic: phát hiện rephrasing sai (LLM nói "bit 5 = 1" trong khi
        # comms decoded thực tế khác). Đếm gián tiếp.
        if setup == "A":
            # Tăng counter khi LLM viết về bit positions mà không có decode chính xác
            if "bit" in reasoning and "compromise" not in reasoning:
                n_misread += 1
    m4 = (n_misread / n_steps) if n_steps > 0 else 0.0

    # M5: step latency
    wall = meta.get("wall_time_seconds", 0)
    m5 = (wall / n_steps) if n_steps > 0 else 0.0

    return {
        "setup": setup,
        "red_variant": meta["red_variant"],
        "episode_idx": meta["episode_idx"],
        "M1_joint_reward": m1,
        "M2_invalid_action_rate": m2,
        "M3_roe_deny_rate": m3,
        "M4_comms_misread_rate": m4,
        "M5_step_latency_s": m5,
        "n_steps": n_steps,
        "n_proposed": n_proposed,
        "n_invalid": n_invalid,
        "n_denied": n_denied,
    }


def aggregate(per_episode_metrics: list) -> dict:
    """Aggregate qua episodes: theo (setup, red_variant) → mean/std."""
    grouped = defaultdict(list)
    for m in per_episode_metrics:
        key = (m["setup"], m["red_variant"])
        grouped[key].append(m)

    summary = []
    for (setup, red), runs in sorted(grouped.items()):
        n = len(runs)
        if n == 0:
            continue

        def agg(field):
            vals = [r[field] for r in runs]
            mu = mean(vals) if vals else 0.0
            sd = stdev(vals) if len(vals) >= 2 else 0.0
            return mu, sd

        m1_mu, m1_sd = agg("M1_joint_reward")
        m2_mu, m2_sd = agg("M2_invalid_action_rate")
        m3_mu, m3_sd = agg("M3_roe_deny_rate")
        m4_mu, m4_sd = agg("M4_comms_misread_rate")
        m5_mu, m5_sd = agg("M5_step_latency_s")

        summary.append({
            "setup": setup,
            "red_variant": red,
            "n_episodes": n,
            "M1_mean": m1_mu, "M1_std": m1_sd,
            "M2_mean": m2_mu, "M2_std": m2_sd,
            "M3_mean": m3_mu, "M3_std": m3_sd,
            "M4_mean": m4_mu, "M4_std": m4_sd,
            "M5_mean": m5_mu, "M5_std": m5_sd,
        })
    return summary


def write_csv(summary: list, path: Path):
    """Ghi summary ra CSV."""
    if not summary:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        for row in summary:
            writer.writerow(row)


def print_table(summary: list):
    """In bảng tóm tắt ra stdout."""
    if not summary:
        print("Không có dữ liệu.")
        return
    fmt = "{:<8} {:<14} {:>3} | {:>10} ± {:<6} | {:>5} ± {:<5} | {:>5} ± {:<5} | {:>5} ± {:<5} | {:>5} ± {:<5}"
    print(fmt.format(
        "Setup", "Red", "N",
        "M1(rew)", "std",
        "M2",  "std",
        "M3",  "std",
        "M4",  "std",
        "M5(s)", "std",
    ))
    print("-" * 130)
    for row in summary:
        print(fmt.format(
            row["setup"], row["red_variant"], row["n_episodes"],
            f"{row['M1_mean']:.2f}", f"{row['M1_std']:.2f}",
            f"{row['M2_mean']:.3f}", f"{row['M2_std']:.3f}",
            f"{row['M3_mean']:.3f}", f"{row['M3_std']:.3f}",
            f"{row['M4_mean']:.3f}", f"{row['M4_std']:.3f}",
            f"{row['M5_mean']:.2f}", f"{row['M5_std']:.2f}",
        ))


def main():
    parser = argparse.ArgumentParser(description="Extract M1-M5 từ benchmark logs")
    parser.add_argument("--setup", choices=["A", "B", "C"], help="Filter theo setup")
    parser.add_argument("--out", type=str, default=str(RESULTS_DIR / "summary.csv"),
                        help="Output CSV path")
    args = parser.parse_args()

    reward_files = sorted(RESULTS_DIR.glob("joint_reward_*.json"))
    if not reward_files:
        print(f"Không tìm thấy joint_reward_*.json trong {RESULTS_DIR}")
        return

    per_episode = []
    for jp in reward_files:
        meta = load_episode_meta(jp)
        if args.setup and meta["setup"] != args.setup:
            continue
        audit_path = Path(meta["audit_log"])
        rows = parse_audit_csv(audit_path)
        m = compute_metrics_for_episode(meta, rows)
        per_episode.append(m)

    print(f"Đã xử lý {len(per_episode)} episode.\n")
    summary = aggregate(per_episode)
    print_table(summary)

    out_path = Path(args.out)
    write_csv(summary, out_path)
    print(f"\n→ summary saved to {out_path}")

    # Cũng lưu per-episode raw
    raw_path = RESULTS_DIR / "per_episode_metrics.csv"
    if per_episode:
        with open(raw_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(per_episode[0].keys()))
            writer.writeheader()
            for row in per_episode:
                writer.writerow(row)
        print(f"→ per-episode saved to {raw_path}")


if __name__ == "__main__":
    main()
