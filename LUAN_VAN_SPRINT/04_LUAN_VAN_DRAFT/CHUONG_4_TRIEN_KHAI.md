# CHƯƠNG 4 — TRIỂN KHAI VÀ THỰC NGHIỆM

## 4.1 Môi trường thực nghiệm

### 4.1.1 Hệ điều hành và phần cứng

- **Hệ điều hành**: macOS (Darwin 24.2.0) / Linux Ubuntu 22.04 LTS — đều hỗ trợ.
- **Phần cứng tối thiểu**: 8 GB RAM, CPU 4 nhân, không bắt buộc GPU vì LLM gọi qua API.
- **Kết nối mạng**: cần internet để gọi Claude API.

### 4.1.2 Hệ thống mô phỏng CybORG CAGE 4

Đề tài sử dụng **CybORG CAGE 4** — phiên bản được trích từ kho lưu trữ thử thách `cage-challenge-4` và đóng gói trong repo của bài báo *Large Language Models are Autonomous Cyber Defenders* [2] (folder `llms-are-acd-main/`).

Cài đặt qua script tự động:

```bash
cd llms-are-acd-main
chmod +x install_unified.sh
./install_unified.sh
source cage-env/bin/activate
```

Script tự động: clone CybORG repo, tạo virtual environment, cài CybORG package + dependencies.

### 4.1.3 Mô hình Ngôn ngữ Lớn — Claude Haiku 4.5

Đề tài chọn **Claude Haiku 4.5** (model ID: `claude-haiku-4-5`) làm LLM chính. Lý do:

- **Tier giá tương đương GPT-4o-mini** (sử dụng trong bài báo [2]) → đảm bảo so sánh công bằng.
- **Native MCP support** — `claude-agent-sdk` (Python) cung cấp MCP server in-process và tool runner sẵn.
- **Auth qua Claude Code login** — không cần quản lý API key riêng (dùng Team Premium seat).
- **Hỗ trợ prompt caching aggressive** — quan trọng cho việc tối ưu latency và token consumption qua nhiều step.

### 4.1.4 Stack kỹ thuật

| Thành phần | Phiên bản | Vai trò |
|---|---|---|
| Python | 3.11 | Runtime chính |
| `claude-agent-sdk` | ≥ 0.2.0 | LLM SDK + MCP support |
| `anyio` | ≥ 4.0 | Async runtime |
| `ray[rllib]` | (theo cage-env) | Policy interface cho CybORG |
| `pyyaml` | (chuẩn) | Đọc config |

## 4.2 Triển khai Prototype (Giai đoạn 0 — Nghiên cứu khả thi)

### 4.2.1 Cấu trúc thư mục

Toàn bộ code triển khai nằm trong thư mục `feasibility-mcp-roe/` (sibling của `llms-are-acd-main/`, không sửa đổi mã nguồn gốc):

```
feasibility-mcp-roe/
├── feasibility/                    # Code chính
│   ├── prompt.md                   # System prompt tiếng Việt
│   ├── tools.py                    # 6 MCP tool
│   ├── state_extractor.py          # Decoder pre-parse
│   ├── context.py                  # StepContext singleton
│   ├── claude_policy.py            # ray.rllib.Policy subclass
│   ├── audit.py                    # CSV logger
│   └── roe/
│       ├── rules.py                # 3 quy tắc RoE (Giai đoạn 0)
│       ├── rules_v2.py             # 8 quy tắc RoE (Phase 2 mở rộng)
│       └── policy_engine.py        # validate() + record_action()
├── tests/
│   └── test_offline.py             # 11 unit test pure logic
├── run_smoke.py                    # Scenario 1
├── scenario_2_roe_deny.py          # Scenario 2 (2 parts)
├── scenario_3_token_compare.py     # Scenario 3
├── run_all_scenarios.py            # Orchestrator
└── logs/                           # Output các lần chạy
```

Tổng dung lượng code (Giai đoạn 0): **~1.230 dòng Python**.

### 4.2.2 Triển khai các thành phần chính

#### Decoder Pre-parse

`feasibility/state_extractor.py` triển khai 3 hàm chính:
- `decode_commvector()` — decode 1 vectơ 8-bit thành JSON
- `extract_threats()` — quét observation dict, trích host-level threats + IOC
- `extract_state()` — hàm cửa vào tổng hợp

#### MCP Tools

`feasibility/tools.py` đăng ký 6 tool vào in-process MCP server:
- 2 observation tool (read-only)
- 4 action proposal tool (qua `_propose()` helper gọi RoE)

Tất cả tool dùng decorator `@tool` của `claude-agent-sdk`. Description và schema tiếng Việt để Claude reasoning tiếng Việt.

#### RoE Rule Engine

`feasibility/roe/rules.py` chứa 3 rule + `EpisodeCounters` class. `feasibility/roe/policy_engine.py` cung cấp 2 hàm:
- `validate(action_type, params, state)` → `Verdict`
- `record_action(action_type, params)` — cập nhật counter

#### Claude Policy

`feasibility/claude_policy.py` định nghĩa `ClaudeDefenderPolicy(Policy)` — subclass của `ray.rllib.policy.policy.Policy`:

```python
class ClaudeDefenderPolicy(Policy):
    def __init__(self, observation_space, action_space, config=None):
        ...

    def compute_single_action(self, obs=None, prev_action=None, **kwargs):
        # 1. Reset StepContext
        # 2. Pre-parse observation
        # 3. Bridge sync → async, gọi Claude với MCP tools
        # 4. Lấy proposed_action từ StepContext
        # 5. Materialize thành CybORG Action
        # 6. Audit log
        return action, [], {}
```

### 4.2.3 Tích hợp với CybORG

Việc tích hợp đầy đủ với CybORG (wire 4 blue agent RL còn lại + chạy full 500-step episode) thuộc về **Phase 2** (mục 4.4 dưới). Trong Giai đoạn 0, prototype chỉ chạy `compute_single_action` độc lập với observation hand-crafted để verify pipeline.

## 4.3 Ba kịch bản kiểm thử khả thi (Giai đoạn 0)

Để xác nhận tính khả thi của kiến trúc ở quy mô nhỏ, đề tài thiết kế ba kịch bản kiểm thử (test scenario), mỗi kịch bản tấn công vào một trong ba luận điểm chính.

### 4.3.1 Kịch bản 1 — Happy Path (Kiến trúc hoạt động đầu cuối)

**Mục đích**: Verify toàn bộ pipeline hoạt động end-to-end, từ observation thô đến CybORG action.

**Thiết kế**:
- Đầu vào: observation giả với `host_a` có file `escalate.sh` (IOC admin), agent_2 báo admin compromise busy, agent_3 báo user-level.
- Đầu ra mong đợi: Claude gọi 2 observation tool, đề xuất `Restore host_a`, RoE allow.

**Kết quả**: Pass.
- 4 tool call (ToolSearch → get_threat_summary → get_comms_decoded → propose_restore)
- Final action: `Restore host_a`
- Wall time: 19,36 giây

**Trích reasoning Claude từ log**:
> *"Host_a có admin-level compromise với IOC `escalate.sh` (privilege escalation) và 1 suspicious process. [...] Tôi có đủ bằng chứng để thực hiện restore theo RoE."*

→ **Chứng minh**: Claude không bao giờ chạm bit thô `[0,0,0,0,0,1,1,1]` — chỉ đọc `{"compromise_level": "admin"}` đã được decode. Hạn chế 1 được giải quyết bằng kiến trúc.

📁 Log: `logs/scenario_1_happy_path_20260611_133751.txt`

### 4.3.2 Kịch bản 2 — RoE Deny + LLM Self-Correct

Kịch bản này chia thành hai phần để cô lập biến số.

#### Phần A — RoE deny tất định (không qua LLM)

**Mục đích**: Verify RoE engine hoạt động deterministic, không phụ thuộc LLM.

**Thiết kế**:
- Đầu vào: state có `host_a` với `compromise_level = "user"` (chỉ file `cmd.sh`, chưa phải admin).
- Lệnh: gọi trực tiếp `_propose("Restore", {"hostname": "host_a"}, "aggressive response")` trong Python.

**Kết quả**: Pass.
- RoE trả về:
  ```json
  {
    "status": "denied",
    "reason": "Restore yêu cầu xác nhận admin-level compromise; host 'host_a' hiện đang ở mức 'user'.",
    "suggested": "propose_analyse(hostname='host_a', reason='thu thập thêm bằng chứng')"
  }
  ```
- `proposed_action = None`, `rejected_attempts` có 1 entry.
- Wall time: <0,01 giây (deterministic Python, không gọi LLM).

→ **Chứng minh**: RoE là rào chắn cứng, không phụ thuộc LLM. Hạn chế 2 (phần ràng buộc) được giải quyết.

#### Phần B — LLM tự sửa sai khi nhận denial

**Mục đích**: Verify LLM đọc được denial và chuyển sang action khác (vòng lặp self-correction).

**Thiết kế**:
- Pre-fill `EpisodeCounters.blocks_per_zone = {"restricted_zone_b": 1}` (mô phỏng đã block một lần).
- Inject vào situation message: *"Lần trước bạn thử block restricted_zone_b nhưng bị RoE từ chối vì hit rate limit. Hãy chọn action khác."*
- Đồng thời cho thấy agent_2 báo admin compromise.

**Kết quả**: Pass.
- Final action: `DeployDecoy(gateway)` — action hoàn toàn khác.
- Wall time: 29,27 giây.

**Trích reasoning Claude từ log**:
> *"Hành động trước đó: Block restricted_zone_b bị từ chối vì RoE rate limit (đã block 1 lần). [...] Tôi không thể block restricted_zone_b nữa. [...] Tôi sẽ deploy_decoy trên một host quan trọng trong public_access_zone."*

→ **Chứng minh**: cơ chế LLM ↔ RoE feedback loop hoạt động đúng — Claude đọc denial bằng tiếng Việt, không lặp lại action bị chặn, chuyển sang action thay thế. Hạn chế 3 có evidence sơ bộ.

📁 Log: `logs/scenario_2_roe_deny_20260611_133811.txt`

### 4.3.3 Kịch bản 3 — Đo lường giảm prompt

**Mục đích**: So sánh dung lượng prompt giữa kiến trúc baseline (kiểu bài báo [2]) và kiến trúc đề xuất.

**Thiết kế**:
- Cùng 1 observation giả (1 host, 4 comm vector).
- **Mode A** (kiểu baseline): nhồi toàn bộ context + raw bit vào prompt, single shot, không tool.
- **Mode B** (kiến trúc đề xuất): prompt ngắn + MCP tools, LLM tự query.

**Kết quả**:

| Chỉ số | Mode A | Mode B | Δ |
|---|---:|---:|---:|
| System prompt (chars) | 2.800 | 2.454 | −12,4% |
| User message (chars) | 554 | 160 | −71,1% |
| Total controlled prompt (chars) | 3.354 | 2.614 | **−22,1%** |
| SDK input_tokens | 10 | 31 | +210% |
| SDK cache_creation | 0 | 8.521 | n/a |
| SDK cache_read | 19.481 | 75.845 | +289% |
| Output tokens | 1.080 | 2.565 | +138% |
| Wall time | 14,16s | 29,03s | +105% |
| Tool calls | 1 (single shot) | 4 | — |

**Diễn giải**:
- ✓ **Phần prompt em viết** giảm 22,1% (system + user).
- ✗ **Tổng token SDK xử lý** tăng 333% do multi-turn + Claude Code CLI overhead.

→ **Chứng minh**: ở phần em chủ động viết, MCP gọn hơn. Phần SDK wrapper nằm ngoài tầm kiểm soát.

⚠ **Lưu ý**: kịch bản này chỉ chạy trên 1 observation giả nhỏ (1 host). Chưa test với observation thực của CybORG (5+ host, nhiều process). Kết quả token có thể khác hẳn khi observation lớn — cần đo ở Phase 2 với multi-step.

📁 Log: `logs/scenario_3_token_compare_20260611_133841.txt`

## 4.4 Mười một Unit Test (kiểm thử deterministic)

Ngoài ba kịch bản LLM, đề tài có **11 unit test pure Python** (không gọi LLM) để verify deterministic core:

| Nhóm | Số test | Nội dung |
|---|---:|---|
| Decoder 8-bit → JSON | 4 | no_compromise, admin+busy, skip_self, IOC_extraction |
| Rule restore_needs_admin | 3 | denied_when_user, allowed_when_admin, denied_when_host_not_in_threats |
| Rule block_rate_limit | 2 | first_allowed, second_denied |
| Rule decoy_rate_limit | 1 | max_two_per_host |
| Default fallback | 1 | unknown_action_allowed |

**Kết quả**: **11/11 pass** trong <1 giây.

```
✓ test_decode_commvector_no_compromise
✓ test_decode_commvector_admin_compromise_busy
✓ test_decode_skips_self
✓ test_extract_state_with_admin_ioc
✓ test_restore_denied_when_no_admin
✓ test_restore_allowed_when_admin
✓ test_restore_denied_when_host_not_in_threats
✓ test_block_first_allowed_second_denied
✓ test_block_different_zones_independent
✓ test_decoy_max_two_per_host
✓ test_unknown_action_allowed_by_default

11/11 passed
```

📁 Log: `logs/offline_tests_20260611_133751.txt`

## 4.5 Tổng kết Giai đoạn 0

### 4.5.1 Đánh giá so với 3 hạn chế

| Hạn chế trong [2] | Giải pháp đề xuất | Trạng thái xác nhận (Giai đoạn 0) |
|---|---|---|
| Ảo giác đọc vectơ 8-bit | Pre-decode bit → JSON, expose qua MCP tool | ✓ Giải quyết bằng kiến trúc |
| Lệ thuộc prompt cho định nghĩa action | RoE rule tất định + MCP schema cứng | ✓ Verified ở quy mô nhỏ |
| Thiếu reward direction | RoE feedback (allow/deny + reason) | ⚠ Bằng chứng sơ bộ, cần Phase 2 |

### 4.5.2 Phát hiện ngoài kỳ vọng

Trong một lần thử Kịch bản 2, một "directive" sai được cố tình đưa vào prompt ("block ngay không cần investigate"). Claude **từ chối tuân thủ** directive này, yêu cầu investigate trước khi block. → Prompt + tool design **tự nó cũng là một lớp phòng vệ** bên cạnh RoE.

### 4.5.3 Hạn chế chưa được kiểm chứng ở Giai đoạn 0

Những điều cần kiểm chứng tiếp ở Phase 2:

1. Chưa test trên observation thực tế của CybORG CAGE 4 (test mới dùng 1 host giả).
2. Chưa chạy full episode 500 step.
3. Chưa đo chi phí biên (marginal cost) sau khi prompt cache đạt trạng thái ổn định.
4. RoE denial trong Kịch bản 2 Phần B được inject thủ công vào prompt thay vì fire tại runtime — chưa test full loop.
5. Chưa benchmark với 4 biến thể red agent.
6. Tập RoE rule mới có 3 — cần mở rộng lên 8-10.

## 4.6 Thiết kế thực nghiệm Phase 2 — Full Benchmark

### 4.6.1 Mở rộng tập RoE rule (Phase 2A)

Mở rộng từ 3 lên **8 rule** đầy đủ. Chi tiết tập rule mới được trình bày trong Phụ lục A.

### 4.6.2 Tích hợp full CybORG (Phase 2B)

Wire `ClaudeDefenderPolicy` vào CybORG submission đầy đủ:
- 1 blue agent dùng kiến trúc đề xuất (MCP + RoE).
- 4 blue agent dùng baseline RL KEEP có sẵn trong repo `llms-are-acd-main/`.
- Verify pipeline chạy được 500 step không crash.

### 4.6.3 Thiết kế thí nghiệm so sánh A/B/C

| Setup | Mô tả | Mục đích |
|---|---|---|
| **A** (baseline) | LLM theo bài báo [2], không MCP không RoE | Đường cơ sở |
| **B** (MCP only) | LLM + MCP (có decoder + tool allow-list), không RoE rule | Cô lập đóng góp của MCP |
| **C** (MCP + RoE) | Kiến trúc đề xuất đầy đủ | Đo lường kiến trúc tổng |

### 4.6.4 Thiết kế thí nghiệm theo red variant

Sử dụng 4 biến thể red agent có sẵn trong bài báo [2]:

| Red variant | Đặc trưng |
|---|---|
| FiniteState (default) | Hành vi cố định, có lịch trình |
| AggressiveFSM | Dùng service discovery hung hãn, quét nhanh |
| StealthyFSM | Dùng service discovery lén lút |
| ImpactFSM | Ưu tiên gây tác động lên dịch vụ trọng yếu |

### 4.6.5 Quy mô thí nghiệm

| Yếu tố | Giá trị |
|---|---:|
| Số setup | 3 (A, B, C) |
| Số red variant | 4 |
| Số episode mỗi cấu hình | 5 |
| Step mỗi episode | 500 |
| **Tổng số episode** | **60** |

**Wall time ước tính**: ~30 giờ chạy mô phỏng (chia nhiều phiên).

### 4.6.6 Năm chỉ số đo lường

| ID | Chỉ số | Cách đo |
|---|---|---|
| M1 | Reward | CybORG built-in joint reward |
| M2 | Invalid Action Rate | (số step `final_action == Sleep`) / tổng step |
| M3 | RoE Deny Rate | (số step có `rejected_attempts != []`) / tổng step |
| M4 | Comms Misread Rate | Gán nhãn thủ công 50 audit row mỗi setup |
| M5 | Step Latency (p50, p95) | Wall clock time |

### 4.6.7 Tiêu chí đạt (Pass Criterion)

| Chỉ số | Tiêu chí | Diễn giải |
|---|---|---|
| M2 | Setup C < 0,5 × Setup A | RoE giảm invalid action ≥ 50% |
| M3 | 5% ≤ Setup C ≤ 40% | RoE fire hợp lý |
| M1 | Setup C ≥ Setup A − 30% | Reward không giảm quá ngưỡng |
| M5 | Setup C < 5 × Setup A | Latency chấp nhận được |
| M4 | Setup C < 5% | Decoder loại bỏ ảo giác comms |

**Quy ước đánh giá**:
- 5/5 đạt → đề tài thành công xuất sắc.
- 3-4/5 đạt → đề tài thành công.
- < 3/5 đạt → chuyển sang phân tích failure modes.

### 4.6.8 Quy trình chạy benchmark

```bash
# Chạy 60 episode đầy đủ
python3 benchmark/run_benchmark.py --all

# Phân tích log
python3 benchmark/analyze_metrics.py benchmark/results/
python3 benchmark/analyze_clustering.py benchmark/results/

# Xuất bảng + biểu đồ
python3 benchmark/generate_report.py benchmark/results/
```

Kết quả chi tiết được trình bày trong **Chương 5**.
