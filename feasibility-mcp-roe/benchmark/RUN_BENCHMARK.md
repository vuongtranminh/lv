# Cách chạy benchmark đầy đủ (chia chunk dần dần)

## Mô hình thời gian

- 60 episode = 3 setup × 4 red × 5 ep
- ~30 phút / episode → tổng ~30 giờ
- Mọi episode đã xong sẽ được **skip tự động** khi chạy lại (resume mặc định)

## 1. Cài CybORG CAGE 4 (bắt buộc — một lần)

```bash
cd /Users/apple/Workspace/personal/side-projects/demo/llms-are-acd-main
./install_unified.sh                 # 15–30 phút
source cage-env/bin/activate
cd ../feasibility-mcp-roe
pip install anyio claude-agent-sdk pandas matplotlib scikit-learn
```

## 2. Smoke test (1 episode, ~15 phút)

```bash
python benchmark/run_benchmark.py --setup C --red FiniteState --episodes 1
```

Sinh: `results/audit_C_FiniteState_ep0.csv` + `results/joint_reward_C_FiniteState_ep0.json`

→ Nếu OK, pipeline chạy ngon, sang bước 3.

## 3. Xem tiến độ bất cứ lúc nào

```bash
python benchmark/run_benchmark.py --status
```

Output ví dụ:
```
Setup  Red            | ep0 ep1 ep2 ep3 ep4 | done
A      FiniteState    | ✓   ✓   ✓   ·   ·  | 3/5
B      FiniteState    | ✓   ✓   ·   ·   ·  | 2/5
...
Tổng: 6/60 episode hoàn thành
Tiến độ: 10.0%  •  ETA còn lại: ~27.0 giờ
Episode kế tiếp: setup=A, red=FiniteState, ep=3
  → python benchmark/run_benchmark.py --setup A --red FiniteState --episodes 5
```

## 4. Ba cách chia chunk

### Cách A — chạy theo **(setup, red)**, mỗi lần 5 episode (~2.5 giờ)

12 phiên × 2.5 giờ = 30 giờ. Phù hợp chạy mỗi tối / mỗi buổi.

```bash
# Phiên 1
python benchmark/run_benchmark.py --setup A --red FiniteState --episodes 5
# Phiên 2
python benchmark/run_benchmark.py --setup A --red AggressiveFSM --episodes 5
# ...
# Phiên 12
python benchmark/run_benchmark.py --setup C --red ImpactFSM --episodes 5
```

Mỗi phiên crash giữa chừng cũng OK — chạy lại lệnh, các episode đã xong sẽ bị skip.

### Cách B — chạy theo `--chunk N/12` (chia tự động)

```bash
# Chia 60 ep còn lại thành 12 phần, chạy phần 1
python benchmark/run_benchmark.py --chunk 1/12

# Lần khác chạy phần 2
python benchmark/run_benchmark.py --chunk 2/12

# v.v...
```

Khác Cách A: `--chunk` tính từ **danh sách todo còn lại sau khi resume**, không nhất thiết khớp `(setup, red)` cụ thể. Lợi điểm: chia đều, không cần nhớ đã làm tới đâu.

### Cách C — chạy ngầm hết 30 giờ

```bash
nohup python benchmark/run_benchmark.py --all > benchmark_full.log 2>&1 &
tail -f benchmark_full.log
```

Resume vẫn áp dụng — nếu chạy lại sau crash, các ep đã xong sẽ skip.

## 4.5. Xem log chi tiết từng episode

Mỗi episode sinh **3 file** vào `results/`:

| File | Mô tả | Dùng cho |
|---|---|---|
| `audit_<tag>.csv` | Tóm tắt per-step (1 row/step) | extract_metrics — tính M1-M5 |
| `joint_reward_<tag>.json` | Tổng kết episode (reward, wall time, step rewards) | summary + tiến độ |
| `detailed_<tag>.jsonl` | **Mọi event** chi tiết — full prompt, full Claude response, mỗi tool call, mỗi RoE verdict | đọc lại / debug / trích đoạn báo cáo |

### Xem log chi tiết

```bash
# Tổng hợp 1 episode — bảng event count, tool call, RoE verdict
python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl --summary

# In từng step (compact)
python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl

# Chỉ in 1 step cụ thể
python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl --step 142

# In full system prompt + user message + raw observation (rất dài)
python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl --step 142 --full

# Tìm step nào có RoE deny Restore
python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl --grep "denied"

# Range step (vd debug từ step 100-110)
python benchmark/inspect_episode.py results/detailed_C_FiniteState_ep0.jsonl --from-step 100 --to-step 110
```

### Cấu trúc 1 dòng JSONL

```json
{"ts": "2026-06-27T08:15:32.123", "step": 42, "agent": "blue_agent_4",
 "event": "roe_verdict",
 "data": {"action_type": "Restore", "params": {"hostname": "host_b"},
          "allowed": false, "reason": "...", "suggested": "..."}}
```

Các event_type ghi:
- `episode_start`, `episode_end` — meta + tổng kết
- `step_start` — raw CybORG observation
- `state_extracted` — sau pre-parse JSON
- `llm_query` — **full system prompt + full user message**
- `llm_response_chunk` — mỗi text block Claude trả về (không truncate)
- `tool_call` — tên + args
- `tool_result` — full payload
- `roe_verdict` — allowed/denied + reason + suggested
- `action_proposed`, `action_materialized` — chuyển từ JSON sang CybORG Action
- `step_end` — wall time, count proposed/rejected
- `paper_parse_result` / `paper_parse_failed` — chỉ Setup A
- `error` — bất kỳ exception nào xảy ra trong query LLM

### Parse JSONL bằng pandas

```python
import pandas as pd
df = pd.read_json("results/detailed_C_FiniteState_ep0.jsonl", lines=True)
# Lọc RoE deny
deny = df[df["event"] == "roe_verdict"]
deny = deny[deny["data"].apply(lambda d: not d["allowed"])]
print(deny.groupby(deny["data"].apply(lambda d: d["action_type"])).size())
```

## 5. Khi đã xong → extract metric

```bash
python benchmark/extract_metrics.py
```

Sinh:
- `results/summary.csv` — bảng mean ± std (setup × red, mỗi cell 5 ep)
- `results/per_episode_metrics.csv` — raw per-episode

Khi `--status` báo 60/60 episode hoàn thành là extract sẽ ra đủ số.

## 6. Có thể chạy extract giữa chừng

Khi mới có 6/60 episode, `extract_metrics.py` vẫn chạy được — bảng `summary.csv` sẽ có ô `N=1` hoặc `N<5`. Hữu ích để xem xu hướng trước khi xong hết.

```bash
# Sau mỗi phiên, extract để xem xu hướng tạm
python benchmark/run_benchmark.py --setup A --red FiniteState --episodes 5
python benchmark/extract_metrics.py
```

## 7. Lệnh tiện ích

| Mục đích | Lệnh |
|---|---|
| Xem tiến độ | `python benchmark/run_benchmark.py --status` |
| Chạy 1 episode cụ thể | `python benchmark/run_benchmark.py --setup C --red FiniteState --episodes 1` |
| Chạy 1 cặp setup+red (5 ep) | `python benchmark/run_benchmark.py --setup A --red AggressiveFSM --episodes 5` |
| Chạy phần thứ N/12 | `python benchmark/run_benchmark.py --chunk 3/12` |
| Chạy hết phần còn lại | `python benchmark/run_benchmark.py --all` |
| Chạy lại từ đầu (xoá kết quả) | `python benchmark/run_benchmark.py --all --force` |
| Tổng hợp metric | `python benchmark/extract_metrics.py` |

## 8. Gợi ý lịch chạy

Nếu bận, chia làm **2 tuần**:
- **Tuần 1**: chạy hết Setup A (4 phiên × 2.5h) + Setup B (4 phiên × 2.5h) = 20h
- **Tuần 2**: chạy hết Setup C (4 phiên × 2.5h) = 10h + extract metric + fill báo cáo

Nếu cấp tốc trong **3 ngày**:
- Ngày 1: Setup A đầy đủ (~10h, có thể chạy nền ban đêm)
- Ngày 2: Setup B đầy đủ (~10h)
- Ngày 3: Setup C đầy đủ (~10h) + extract + fill

## Troubleshooting

| Triệu chứng | Nguyên nhân | Fix |
|---|---|---|
| `ImportError: CybORG` | Chưa active `cage-env` | `source llms-are-acd-main/cage-env/bin/activate` |
| `--status` không in gì | Path `benchmark/results/` không tồn tại | `mkdir -p benchmark/results` |
| Episode chạy lại dù đã xong | File `joint_reward_*.json` thiếu hoặc corrupted | Dùng `--force` để overwrite, hoặc xoá file đó trước |
| Smoke test fail step 0 | Action wrapping mismatch | Kiểm tra `_materialize()` trong `claude_policy.py` |
| Reward luôn = 0 | Sum reward logic sai | Xem `sum_reward_dict()` trong `run_benchmark.py` |
| Audit CSV không có cột `proposed_action` | Schema mismatch | Xem `audit.py` header |
| Claude API timeout / rate-limit | Premium seat limit | Đợi vài phút, chạy lại — resume sẽ skip ep đã xong |
