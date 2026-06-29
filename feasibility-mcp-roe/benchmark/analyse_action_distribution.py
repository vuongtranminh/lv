"""Phân tích phân phối action từ log JSON Lines của benchmark.

Sprint 3 — Nhánh B (theo góp ý của thầy: "thêm bảng phân phối action, tỷ lệ
Sleep, số host được can thiệp"). Đọc detailed_*.jsonl + joint_reward_*.json,
sinh bảng Markdown + CSV trả lời câu hỏi: "Setup C có thắng nhờ ngủ không?"

Usage:
    python analyse_action_distribution.py [results_dir]

    results_dir default = thư mục `results/` cạnh script.

Output:
    - results/action_distribution.csv (per-run summary)
    - stdout: bảng Markdown để paste vào báo cáo
"""

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

# action_materialized.data.cyborg_action có dạng:
#   "Sleep"
#   "Analyse public_access_zone_subnet_server_host_0"
#   "Restore office_network_subnet_user_host_4"
ACTION_RE = re.compile(r"^(\w+)(?:\s+(.+))?$")

# Phân loại action theo nhóm — match với bảng thầy yêu cầu.
TRACKED_ACTIONS = ["Sleep", "Analyse", "Remove", "Restore", "DeployDecoy",
                   "BlockTrafficZone", "Monitor"]

# Filename parser: detailed_<setup>_<red>_ep<n>[_<tag>].jsonl
FNAME_RE = re.compile(r"^detailed_([^_]+)_([^_]+)_ep(\d+)(?:_([^.]+))?\.jsonl$")


def parse_log(path: Path) -> dict:
    """Đếm action từ một log JSONL. Trả về dict thống kê."""
    counts = Counter()
    distinct_hosts = set()
    n_steps = 0

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event") != "action_materialized":
                continue
            n_steps += 1
            cyborg = rec.get("data", {}).get("cyborg_action", "")
            m = ACTION_RE.match(cyborg)
            if not m:
                continue
            action_type, target = m.group(1), m.group(2)
            counts[action_type] += 1
            # Đếm host distinct được can thiệp (loại trừ Sleep + Block)
            if action_type in {"Analyse", "Remove", "Restore", "DeployDecoy"} and target:
                distinct_hosts.add(target.strip())

    return {
        "counts": counts,
        "distinct_hosts": len(distinct_hosts),
        "n_steps": n_steps,
    }


def parse_filename(name: str):
    """Decompose detailed_<setup>_<red>_ep<n>[_<tag>].jsonl → (setup, red, ep, tag)."""
    m = FNAME_RE.match(name)
    if not m:
        return None
    setup, red, ep, tag = m.group(1), m.group(2), int(m.group(3)), m.group(4)
    return setup, red, ep, tag


def load_reward(results_dir: Path, setup: str, red: str, ep: int, tag: str | None) -> float | None:
    """Tìm joint_reward_<setup>_<red>_ep<n>[_tag].json tương ứng."""
    if tag:
        fname = f"joint_reward_{setup}_{red}_ep{ep}_{tag}.json"
    else:
        fname = f"joint_reward_{setup}_{red}_ep{ep}.json"
    path = results_dir / fname
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return float(data.get("cumulative_joint_reward", 0.0))
    except Exception:
        return None


def setup_label(setup: str, tag: str | None) -> str:
    """A/B/C → human label; tag distinguishes C-v1 (sprint1) vs C-v2 (post-fix)."""
    if setup == "C":
        if tag == "sprint1":
            return "C-v1 (Sprint1 pre-fix)"
        return "C-v2 (Sprint2 post-fix)"
    return setup


def build_table(rows: list[dict]) -> tuple[str, list[list]]:
    """Sinh Markdown table + CSV rows."""
    header = (
        "| Setup | Red | Ep | Sleep | Analyse | Remove | Restore | DeployDecoy | "
        "Block | % Sleep | # host can thiệp | Reward |"
    )
    sep = "|" + "|".join(["---"] * 12) + "|"
    lines = [header, sep]
    csv_rows = [["Setup", "Red", "Ep", "Sleep", "Analyse", "Remove", "Restore",
                 "DeployDecoy", "Block", "% Sleep", "# host can thiệp", "Reward"]]
    for r in rows:
        c = r["counts"]
        n = max(r["n_steps"], 1)
        pct_sleep = 100.0 * c.get("Sleep", 0) / n
        row = [
            r["label"], r["red"], r["ep"],
            c.get("Sleep", 0),
            c.get("Analyse", 0),
            c.get("Remove", 0),
            c.get("Restore", 0),
            c.get("DeployDecoy", 0),
            c.get("BlockTrafficZone", 0),
            f"{pct_sleep:.1f}%",
            r["distinct_hosts"],
            f"{r['reward']:.0f}" if r["reward"] is not None else "N/A",
        ]
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
        csv_rows.append(row)
    return "\n".join(lines), csv_rows


def main():
    script_dir = Path(__file__).parent
    results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else (script_dir / "results")
    if not results_dir.exists():
        print(f"ERROR: không tìm thấy thư mục {results_dir}", file=sys.stderr)
        sys.exit(1)

    log_files = sorted(results_dir.glob("detailed_*.jsonl"))
    if not log_files:
        print(f"ERROR: không có log nào trong {results_dir}", file=sys.stderr)
        sys.exit(1)

    rows = []
    for path in log_files:
        parsed = parse_filename(path.name)
        if parsed is None:
            continue
        setup, red, ep, tag = parsed
        stats = parse_log(path)
        reward = load_reward(results_dir, setup, red, ep, tag)
        rows.append({
            "label": setup_label(setup, tag),
            "setup": setup,
            "red": red,
            "ep": ep,
            "tag": tag,
            "counts": stats["counts"],
            "distinct_hosts": stats["distinct_hosts"],
            "n_steps": stats["n_steps"],
            "reward": reward,
        })

    # Sort: A, B, C-v1, C-v2, C-active, ... by Setup then ep then tag
    setup_order = {"A": 0, "B": 1, "C": 2}
    tag_order = {None: 1, "sprint1": 0, "active": 2}
    rows.sort(key=lambda r: (
        setup_order.get(r["setup"], 99),
        tag_order.get(r["tag"], 5),
        r["red"], r["ep"],
    ))

    markdown_table, csv_rows = build_table(rows)

    # Output CSV
    csv_path = results_dir / "action_distribution.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerows(csv_rows)

    # Output Markdown to stdout
    print("# Phân phối action — Sprint 3 Nhánh B")
    print()
    print(f"Nguồn: {len(rows)} log trong `{results_dir.relative_to(script_dir.parent)}/`")
    print()
    print(markdown_table)
    print()
    print(f"_CSV đã lưu: `{csv_path.relative_to(script_dir.parent)}`_")
    print()
    print("## Diễn giải")
    print()
    print("- **% Sleep** = tỷ lệ step agent chọn Sleep / tổng step (500)")
    print("- **# host can thiệp** = số host distinct mà agent Analyse/Remove/Restore/DeployDecoy")
    print("- Nếu một Setup có % Sleep cao + # host can thiệp thấp → agent **không phòng thủ chủ động**")
    print("- Reward cao + # host can thiệp thấp → **thắng nhờ né phạt, không phải nhờ defense**")


if __name__ == "__main__":
    main()
