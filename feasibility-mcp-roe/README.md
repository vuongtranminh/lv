# Feasibility Study: MCP + RoE on TH3 Codebase

Nghiên cứu khả thi (feasibility) cho đề tài luận văn: dùng **MCP Tool Use**
+ **Rules of Engagement (RoE)** để fix 3 hạn chế LLM agent trong bài TH3
(*Large Language Models are Autonomous Cyber Defenders*).

3 hạn chế của TH3 cần fix:
1. **Ảo giác**: LLM đọc nhầm vectơ truyền thông 8-bit của đồng đội
2. **Lệ thuộc prompt**: định nghĩa action trong prompt sai một chữ → LLM hành xử khác hẳn
3. **Không có hàm thưởng**: LLM không biết "thắng" là gì, chỉ làm theo trực giác

Đây là **side project**, **KHÔNG sửa đổi** `llms-are-acd-main/`.

📄 **Báo cáo gửi thầy**: [BAO_CAO_BUOC_1.md](BAO_CAO_BUOC_1.md)

---

## Scope (phạm vi)

- **1 blue agent** (mặc định `blue_agent_4`) điều khiển bởi Claude + MCP tools + RoE
- 4 blue agent còn lại: giữ RL KEEP baseline của paper TH3 (Phase 2)
- **3 RoE rules**: restore-needs-admin, block-rate-limit, decoy-rate-limit
- **2 observation tools**: `get_threat_summary`, `get_comms_decoded`
- **4 action-proposal tools**: analyse, restore, deploy_decoy, block_traffic

---

## Cấu trúc thư mục

```
feasibility-mcp-roe/
├── feasibility/                     # Code chính
│   ├── prompt.md                    # System prompt tiếng Việt
│   ├── tools.py                     # 6 MCP tool (@tool decorator)
│   ├── state_extractor.py           # Decode CybORG obs (8-bit → JSON)
│   ├── context.py                   # StepContext singleton
│   ├── claude_policy.py             # ray.rllib.Policy subclass
│   ├── audit.py                     # CSV log mỗi step
│   └── roe/
│       ├── rules.py                 # 3 quy tắc + EpisodeCounters
│       └── policy_engine.py         # validate() + record_action()
├── tests/
│   └── test_offline.py              # 11 unit test pure logic (no LLM)
├── run_smoke.py                     # Scenario 1 — happy path
├── scenario_2_roe_deny.py           # Scenario 2 — RoE deny + self-correct
├── scenario_3_token_compare.py     # Scenario 3 — Mode A vs Mode B
├── run_all_scenarios.py             # Orchestrator chạy hết, lưu logs/
├── run_experiment.py                # Full CybORG (Phase 2, có NotImplementedError)
├── logs/                            # Output mỗi lần chạy (timestamped)
├── BAO_CAO_BUOC_1.md                # Báo cáo bước 1 gửi thầy
├── requirements.txt
├── .env.example
└── README.md                        # File này
```

---

## Setup

Dùng `claude-agent-sdk` — auth qua Claude Code login, **không cần API key**.

### 1. Cài Python package

```bash
pip3 install -r requirements.txt
```

### 2. Login Claude Code (chỉ 1 lần)

`claude-agent-sdk` đi kèm sẵn Claude Code CLI. Login bằng tài khoản Claude Team Premium:

```bash
/opt/homebrew/lib/python3.11/site-packages/claude_agent_sdk/_bundled/claude /login
```

Hoặc cài Claude Code global để có lệnh `claude` ở bất kỳ đâu:

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude /login
```

### 3. (Tùy chọn) Cấu hình env vars

```bash
cp .env.example .env
# Sửa .env nếu muốn đổi model hoặc audit log path
source .env
```

Mặc định:
- `CLAUDE_MODEL=claude-haiku-4-5` (tương đương GPT-4o-mini của paper)
- `AUDIT_LOG_PATH=./audit_blue_agent_4.csv`

### 4. Verify auth work

```bash
python3 -c "
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions
async def main():
    opts = ClaudeAgentOptions(model='claude-haiku-4-5', max_turns=1)
    async for msg in query(prompt='nói ok', options=opts):
        print(type(msg).__name__)
anyio.run(main)
"
```

Thấy `SystemMessage` → `AssistantMessage` → `ResultMessage` = OK.
Nếu thấy `Not logged in` → quay lại bước 2.

---

## Cách chạy

### Chạy tất cả 4 test (kèm lưu logs)

```bash
python3 run_all_scenarios.py
```

→ Mất ~1.5-2 phút. Output lưu vào `logs/` với timestamp. Terminal chỉ in summary.

### Chạy từng cái (xem trực tiếp ra terminal)

| Lệnh | Test gì | Thời gian | Tốn token? |
|---|---|---|---|
| `python3 tests/test_offline.py` | 11 unit test pure logic | <1s | Không |
| `python3 run_smoke.py` | Scenario 1 — happy path | ~22s | Có (~$0.01) |
| `python3 scenario_2_roe_deny.py` | Scenario 2 — RoE deny + self-correct | ~30s | Có |
| `python3 scenario_3_token_compare.py` | Scenario 3 — Token comparison | ~45s | Có |

### Đọc log

```bash
# Liệt kê log mới nhất
ls -lt logs/

# Xem 1 file
less logs/scenario_2_roe_deny_*.txt

# Hoặc mở bằng app text editor
open logs/scenario_1_happy_path_*.txt
```

---

## Verbose logging

Tools log chi tiết I/O + RoE verdict khi `VERBOSE = True`.

```python
# Trong scenario script (đã set sẵn):
from feasibility import tools as feas_tools
feas_tools.VERBOSE = True
```

Output có:
- `🔧 CLAUDE GỌI TOOL: ...`
- `📤 [tool_name] kết quả trả về cho Claude: ...`
- `⚖️ RoE thẩm định: ✓ ALLOWED / ✗ DENIED`
- `💭 CLAUDE NÓI: ...`

Tắt verbose nếu cần (vd scenario_3 đã tắt vì in cả 2 mode A/B quá dài):

```python
feas_tools.VERBOSE = False
```

---

## Troubleshooting

| Lỗi | Cách fix |
|---|---|
| `ModuleNotFoundError: claude_agent_sdk` | Chạy lại `pip3 install -r requirements.txt` |
| `Not logged in · Please run /login` | Login lại Claude Code (bước 2 setup) |
| `Authentication failed` | Token hết hạn → login lại |
| Scenario chạy quá lâu (>3 phút) | Ctrl+C, kiểm tra mạng, chạy lại |

---

## Phase 2 (chưa làm — chờ thầy duyệt báo cáo bước 1)

Mục tiêu: chạy full 500-step episode trên CybORG CAGE 4.

Cần làm:
1. Wire `claude_policy.py` vào CybORG submission (4 RL KEEP agent + 1 Claude agent)
2. Mở rộng RoE > 3 rule
3. Benchmark: setup A (paper baseline) / B (MCP only) / C (MCP+RoE) × 5 episode × 1+ red variant

Metrics cần đo ở Phase 2:

| Metric | Source |
|---|---|
| Reward | CybORG built-in |
| Invalid action rate | Audit log: rows với `final_action == Sleep` |
| RoE deny rate | Audit log: count `roe_rejections` non-empty |
| Step latency p50/p95 | Wall-time giữa obs và action |
| Comms misread rate | Manual annotate 50 random audit row |
| Marginal token cost | Đo sau khi cache warm |

Pass criterion (go/no-go) đề xuất:
- Invalid action rate (MCP+RoE) **< 0.5×** baseline
- RoE deny rate **∈ [5%, 40%]**
- Reward (MCP+RoE) **≥ baseline − 30%**
- Step latency **< 5×** baseline LLM

**3/4 → go** vào nghiên cứu sâu hơn. Ngược lại → viết failure modes, dừng.

---

## Links

- 📄 [BAO_CAO_BUOC_1.md](BAO_CAO_BUOC_1.md) — Báo cáo bước 1 gửi thầy
- 📁 [llms-are-acd-main/](../llms-are-acd-main/) — Repo paper TH3 gốc (sibling)
- 📁 [logs/](logs/) — Output của các lần chạy scenario
