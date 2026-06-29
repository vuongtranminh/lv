# BÁO CÁO BƯỚC 1 — TRIỂN KHAI QUY MÔ NHỎ

**Học viên**: Trần Minh Vương

**Ngày**: 2026-06-11

**Bài báo nền tảng**: LT1, TH3

**Repo**: `feasibility-mcp-roe/` (sibling của `llms-are-acd-main/`)

---

## Tổng quát: chứng minh gì?

Bài báo TH3 nói: **LLM có thể làm blue agent (người phòng thủ mạng), nhưng có 3 lỗi**:

1. **Ảo giác**: LLM đọc nhầm vectơ truyền thông 8-bit của đồng đội
2. **Lệ thuộc prompt**: định nghĩa hành động trong prompt sai một chữ → LLM hành xử khác hẳn
3. **Không có hàm thưởng**: LLM không biết "thắng" là gì, chỉ làm theo trực giác

**Đề xuất của em**: dùng **MCP (LLM gọi tool có cấu trúc)** + **RoE (rào chắn deterministic)** để fix 3 lỗi này.

**Việc đã làm**: dựng một bản thu nhỏ (feasibility) — **CHƯA chạy 500 step thật trên CybORG**, mà dựng **3 tình huống giả** + **11 unit test** để chứng minh kiến trúc work ở quy mô nhỏ. Mỗi tình huống tấn công vào 1 lỗi.

---

## 3 tình huống đã dựng (tấn công những gì)

### Tình huống 1 — Happy path (kiến trúc work cơ bản)

| | |
|---|---|
| **Tấn công gì** | Đưa cho Claude tình huống thực tế: `host_a` của em có file `escalate.sh` (dấu hiệu admin xâm phạm); đồng đội `blue_agent_2` cũng báo bị xâm phạm admin |
| **Mong muốn** | Claude (a) gọi tool để query state thay vì đọc raw bit, (b) suy luận đúng tình hình, (c) chọn action hợp lý |
| **Kết quả thực** | ✓ Claude gọi 2 tool obs → đọc JSON đã decode → đề xuất `Restore host_a` (đúng action vì admin xâm phạm xác nhận) |
| **Reasoning Claude in ra (từ log)** | *"Host_a có **admin-level compromise** với IOC `escalate.sh` (privilege escalation) và 1 suspicious process. [...] Tôi có đủ bằng chứng để thực hiện restore theo RoE."* |
| **Wall time** | 19.36s |
| **Tool calls** | 4 (ToolSearch → get_threat_summary → get_comms_decoded → propose_restore) |

**Chứng minh**: Claude không bao giờ chạm bit thô `[0,0,0,0,0,1,1,1]` — chỉ đọc `{"compromise_level": "admin"}` đã được code Python decode trước.

→ **Lỗi 1 (ảo giác) được giải quyết bằng kiến trúc**: decoder pre-parse 8-bit thành JSON, LLM không có cơ hội đọc sai bit vì không bao giờ thấy bit thô.

📁 Log: `logs/scenario_1_happy_path_20260611_133751.txt`

---

### Tình huống 2 — RoE chặn được + LLM tự sửa sai

Chia 2 phần để cô lập biến số.

#### Phần A: chứng minh RoE deny đúng (không cần LLM)

| | |
|---|---|
| **Tấn công gì** | Tự tay gọi `_propose("Restore", {hostname: "host_a"})` trong khi state chỉ có user-level compromise (file `cmd.sh`, chưa phải admin) |
| **Mong muốn** | RoE phải từ chối, kèm lý do rõ + gợi ý action khác |
| **Kết quả thực** | ✓ RoE trả về: `{"status": "denied", "reason": "Restore yêu cầu xác nhận admin-level compromise; host 'host_a' hiện đang ở mức 'user'.", "suggested": "propose_analyse..."}` |
| **State sau** | `proposed_action = None`, `rejected_attempts` có 1 entry |
| **Wall time** | <0.01s (deterministic Python, không gọi LLM) |

**Chứng minh**: RoE là **rào chắn cứng, không phụ thuộc LLM** — viết bằng Python deterministic, test đâu chạy đó. Có 7 unit test khác trong `tests/test_offline.py` cũng pass cùng nội dung này.

→ **Lỗi 2 (LLM lệ thuộc prompt) được giải quyết**: RoE chặn hành động sai bằng logic Python, không phụ thuộc LLM diễn giải prompt như thế nào.

#### Phần B: chứng minh LLM đọc deny rồi tự sửa sai

| | |
|---|---|
| **Tấn công gì** | Đưa Claude vào tình huống đã giả lập sẵn: prompt báo "lần trước bạn vừa thử block `restricted_zone_b` nhưng bị RoE từ chối vì hit rate limit. Hãy chọn action khác." Đồng thời cho thấy đồng đội báo admin compromise ở mạng khác |
| **Mong muốn** | Claude (a) đọc hiểu lý do bị từ chối, (b) KHÔNG retry block_traffic, (c) đề xuất action khác hợp lý |
| **Kết quả thực** | ✓ Claude đề xuất `DeployDecoy(gateway)` — action hoàn toàn khác |
| **Reasoning Claude in ra (từ log)** | *"Hành động trước đó: Block restricted_zone_b bị từ chối vì RoE rate limit (đã block 1 lần). [...] Tôi không thể block restricted_zone_b nữa. [...] Tôi sẽ deploy_decoy trên một host quan trọng trong public_access_zone."* |
| **Wall time** | 29.27s |

**Chứng minh**: cơ chế "LLM ↔ RoE" tương tác đúng — Claude đọc denial bằng tiếng Việt, không bị infinite loop, biết chuyển hướng sang action khác.

**⚠ Lưu ý quan trọng**: denial được **inject thủ công** vào prompt (em mô phỏng tình huống step trước đã bị deny). **CHƯA test** trường hợp denial fire trực tiếp từ tool runtime trong cùng 1 step — đó là test sâu hơn ở Phase 2.

→ **Lỗi 3 (không có hàm thưởng) có evidence sơ bộ**: thay reward bằng "RoE allow/deny", Claude hiểu được vì lý do là ngôn ngữ thường. Nhưng mới test 1 case, cần multi-case ở Phase 2.

📁 Log: `logs/scenario_2_roe_deny_20260611_133811.txt`

---

### Tình huống 3 — Đo lường giảm prompt

| | |
|---|---|
| **Tấn công gì** | Cùng 1 observation, chạy 2 cách: **Mode A** (kiểu paper — nhồi tất cả vào prompt, kể cả raw bit) vs **Mode B** (kiểu em — prompt ngắn, LLM tự query tool) |
| **Mong muốn** | Mode B có prompt do em viết NGẮN HƠN Mode A đáng kể |
| **Kết quả thực (mặt tốt)** | ✓ Prompt em viết: giảm **22.1%** (3,354 → 2,614 ký tự). User message giảm **71.1%** (554 → 160 ký tự) |
| **Kết quả không mong muốn** | ✗ TOTAL token model thực sự xử lý lại **TĂNG 333%** ở Mode B (19,491 → 84,397) do SDK wrapper + multi-turn. Wall time cũng tăng 105% (14.16s → 29.03s) |

**Chứng minh**: ở phần em chủ động viết, MCP gọn hơn đáng kể. Phần SDK tự inject (Claude Code wrapper) thì nằm ngoài tầm kiểm soát.

**⚠ Lưu ý quan trọng**: test này chỉ chạy trên **1 observation giả nhỏ** (1 host). **CHƯA test** với observation thật của CybORG CAGE 4 (5+ host, nhiều process). Kết quả token có thể khác hẳn khi observation lớn — chưa biết hướng nào, phải đo ở Phase 2 với multi-step.

📁 Log: `logs/scenario_3_token_compare_20260611_133841.txt`

---

## Bonus — 11 unit test deterministic

Ngoài 3 tình huống LLM, em có 11 unit test pure Python (không gọi LLM) verify:

- 4 test decoder 8-bit → JSON (no compromise / admin+busy / skip self / IOC extraction)
- 3 test rule restore-needs-admin (denied khi user / allowed khi admin / denied khi host không trong threats)
- 2 test rule block-rate-limit (first allowed / second denied)
- 1 test rule decoy-rate-limit (max 2)
- 1 test fallback default cho action không có rule

**Kết quả**: **11/11 pass** trong <1 giây.

📁 Log: `logs/offline_tests_20260611_133751.txt`

---

## Tổng kết theo 3 lỗi của paper TH3

| Lỗi paper | Cách em fix | Bằng chứng | Trạng thái |
|---|---|---|---|
| **1. LLM ảo giác đọc 8-bit** | Pre-decode bit → JSON, expose qua MCP tool | Tình huống 1: Claude đọc `compromise_level: "admin"`, không bao giờ thấy `[0,0,0,0,0,1,1,1]` | ✓ Giải quyết kiến trúc |
| **2. LLM bị prompt định nghĩa action lung lay** | RoE là rào chắn deterministic — viết bằng Python, không qua LLM | Tình huống 2 Part A + 7 unit test rule | ✓ Verified ở quy mô nhỏ |
| **3. LLM không có hàm thưởng** | Thay reward bằng "RoE allow/deny" — LLM hiểu được vì lý do là ngôn ngữ thường | Tình huống 2 Part B — nhưng denial inject thủ công, chưa test full loop runtime | △ Evidence sơ bộ, cần Phase 2 |

**+ Phát hiện ngoài kỳ vọng**: trong một lần thử scenario 2, em cố tình đưa Claude một "directive" sai ("block ngay không cần investigate"). Claude **từ chối tuân thủ**, yêu cầu investigate trước. → Prompt + tool design tự nó cũng là **1 lớp phòng vệ** bên cạnh RoE.

---

## Những gì em chưa test

| Mục | Lý do chưa test |
|---|---|
| Token consumption trên CybORG observation thật | Scenario 3 chỉ chạy trên 1 host giả; CybORG thật có 5+ host, nhiều process |
| Multi-step episode 500 step | Chưa wire 4 RL KEEP agent vào CybORG; cần ~2-3 ngày |
| Marginal token cost sau khi cache warm | Cần multi-step để đo |
| Loop deny → retry không inject thủ công | Scenario 2 Part B inject denial vào prompt; cần test runtime |
| Benchmark reward vs RL baseline (KEEP) | Cần full episode |
| Behaviour với 4 red agent variant của paper | Cần full episode |

---

## Tóm gọn

Em đã dựng **3 tình huống giả + 11 unit test** để stress test kiến trúc MCP+RoE. **Lỗi 1** (ảo giác) giải quyết kiến trúc nhờ pre-decoder. **Lỗi 2** (lệ thuộc prompt) verify được nhờ RoE deterministic. **Lỗi 3** (không reward) mới có evidence sơ bộ qua 1 case inject thủ công. **Prompt do em viết gọn hơn 22% so với kiểu nhồi như paper**, nhưng tổng token thực tế chưa kết luận được vì test mới ở quy mô 1 host. **Lý thuyết đứng vững ở quy mô nhỏ**, đủ cơ sở để đầu tư vào Phase 2 (chạy 500-step episode thật trên CybORG).

---

## Phụ lục — reproduce

```bash
cd /demo/feasibility-mcp-roe
pip3 install -r requirements.txt

# Chạy hết 4 test
python3 run_all_scenarios.py

# Hoặc từng cái
python3 tests/test_offline.py
python3 run_smoke.py
python3 scenario_2_roe_deny.py
python3 scenario_3_token_compare.py
```

**Log files** (chạy ngày 2026-06-11):
- `logs/offline_tests_20260611_133751.txt`
- `logs/scenario_1_happy_path_20260611_133751.txt`
- `logs/scenario_2_roe_deny_20260611_133811.txt`
- `logs/scenario_3_token_compare_20260611_133841.txt`
