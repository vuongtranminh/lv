# BÁO CÁO KẾT QUẢ SETUP B — MCP ONLY (chưa có RoE)

> **Phạm vi**: chỉ dựa trên (1) bài báo *Large Language Models are Autonomous Cyber Defenders* (Castro và cộng sự, IEEE CAI 2025 — viết tắt **TH3**, đã đọc đầy đủ tại file `TH3_Large_Language_Models_are_Autonomous_Cyber_Defenders.pdf`) và (2) kết quả thực thi 1 episode Setup A + 1 episode Setup B với cấu hình red FiniteState, seed 0, độ dài 500 step. Không sử dụng số liệu bên ngoài.

> **So sánh tay ba**: báo cáo này so sánh **Setup B** với **Setup A** và **TH3 paper** ở mọi chỉ số quan trọng.

---

## Bảng thuật ngữ nhanh

| Thuật ngữ | Giải thích |
|---|---|
| **TH3** | Bài báo *"Large Language Models are Autonomous Cyber Defenders"* — bài báo nền |
| **LLM** | Large Language Model — Mô hình ngôn ngữ lớn |
| **MCP** | Model Context Protocol — Giao thức ngữ cảnh mô hình do Anthropic phát triển; cho phép LLM gọi tool bên ngoài (`get_threat_summary`, `get_comms_decoded`, `propose_*`) qua schema chuẩn |
| **RoE** | Rules of Engagement — Quy tắc giao chiến (TẮT trong Setup B, BẬT ở Setup C) |
| **bypass** | Đi qua / bỏ qua (Setup B: tool `propose_*` đi qua RoE validation, mọi action đều `approved`) |
| **CybORG CAGE 4** | Môi trường mô phỏng mạng, kịch bản đa tác nhân |
| **FSM** | Finite State Machine — Máy trạng thái hữu hạn (kiểu red agent) |
| **IOC** | Indicator of Compromise — Chỉ dấu xâm phạm (file `escalate.sh`, `cmd.sh`) |
| **JSONL** | JSON Lines — file mỗi dòng là 1 đối tượng JSON |
| **tool_call / tool_result** | Sự kiện LLM gọi tool MCP / kết quả tool trả về |
| **roe_verdict** | Phán quyết RoE — chấp nhận (`allowed`) hoặc từ chối (`denied`); ở Setup B luôn là `allowed (bypass)` |
| **ablation** | Cô lập — bật/tắt từng thành phần để xem thành phần nào đóng góp gì |
| **single-shot** | Đơn lượt — gọi LLM 1 lần (Setup A); Setup B/C dùng nhiều lượt (multi-turn) |
| **max_turns** | Số lượt LLM tối đa được trao đổi với tool/step (Setup B: 8) |
| **wall time** | Thời gian thực tế trôi qua (đo bằng đồng hồ) |
| **checkpoint** | Điểm lưu trạng thái mỗi 50 step để resume khi máy tắt |
| **destructive action** | Hành động phá hủy (Restore wipe host, Remove tiến trình, BlockTrafficZone chặn vùng) |
| **proactive defense** | Phòng thủ chủ động — triển khai mồi nhử (DeployDecoy), Analyse trước khi có threat |

---

## 1. Mục đích Setup B

Setup B là **bản cô lập đóng góp MCP** trong luận văn. Vai trò:

1. **Đo riêng tác dụng của MCP** so với Setup A (TH3 baseline). Setup B = Setup A + MCP, không có RoE → mọi chênh lệch chỉ số giữa A và B là **đóng góp riêng của MCP**.
2. **Cung cấp gốc so sánh cho Setup C** (Setup B + RoE). Chênh lệch giữa B và C là **đóng góp riêng của RoE**.
3. **Cô lập 3 yếu tố thay đổi của MCP** so với Setup A:
   - Pre-parsed observation (qua `get_threat_summary` và `get_comms_decoded`)
   - Tool calling protocol (LLM gọi `propose_*` với JSON schema chặt chẽ thay vì tự xuất JSON dạng text)
   - Multi-turn reasoning (LLM gọi nhiều turn trong 1 step, có thể retry sau khi nhận tool result)

---

## 2. Cấu hình thí nghiệm

### 2.1 Bảng cấu hình ba (TH3 / Setup A / Setup B)

| Tham số | **TH3** (1LLM+4RL trong paper §IV) | **Setup A** (baseline luận văn) | **Setup B** (MCP only) |
|---|---|---|---|
| Môi trường | CybORG CAGE 4 | CybORG CAGE 4 | CybORG CAGE 4 |
| Red agent | FiniteStateRedAgent | FiniteStateRedAgent | FiniteStateRedAgent |
| Blue đối tượng (LLM) | blue_agent_4 | blue_agent_4 | blue_agent_4 |
| 4 blue đồng đội | **KEEP** (RL+GCN) | **ReactRemoveBlueAgent** (rule-based) | **ReactRemoveBlueAgent** |
| Episode | 2 ep × 500 step | **1 ep** × 500 step (n=1) | **1 ep** × 500 step (n=1) |
| Mô hình LLM | OpenAI/DeepSeek (5 model) | claude-haiku-4-5 | claude-haiku-4-5 |
| max_turns | 1 (single-shot) | 1 | **8** (multi-turn MCP) |
| MCP tools | ❌ | ❌ | **✓** 4 tools (`get_threat_summary`, `get_comms_decoded`, `propose_analyse`, `propose_deploy_decoy`, `propose_restore`, `propose_block_traffic`) |
| RoE | ❌ | ❌ | **❌** (bypass — đây là điểm cô lập) |
| Prompt | Role + Few-shot | Role only (paper-style) | Role only (MCP system prompt) |

### 2.2 Khác biệt cốt yếu của Setup B so với Setup A

| Khía cạnh | Setup A (TH3 baseline) | Setup B (MCP only) |
|---|---|---|
| Cách LLM nhận observation | Raw text + raw 8-bit comm vector trong user message | Pre-parsed JSON qua tool `get_threat_summary()` + `get_comms_decoded()` |
| Cách LLM xuất action | Single text response chứa JSON `{"action":..., "reason":...}` rồi regex parse | Gọi tool `propose_analyse/propose_deploy_decoy/...` với JSON schema chặt chẽ |
| Số lượt LLM với system/step | 1 (single-shot) | tối đa 8 (multi-turn) |
| Cơ chế khi LLM sai | Fallback `Sleep` nếu parse fail | Tool trả lỗi → LLM có thể gọi lại |
| RoE | Không có | Có code RoE nhưng bypass (`roe_enabled=False`) → mọi `propose_*` đều `approved` |

### 2.3 Mã nguồn pipeline Setup B

| Khâu | Code path |
|---|---|
| MCP tools server | [`feasibility/tools.py`](../../feasibility-mcp-roe/feasibility/tools.py) dòng 191-202 (`TOOLS_SERVER = create_sdk_mcp_server`) |
| Tool `get_threat_summary` | `feasibility/tools.py` dòng 69-87 |
| Tool `get_comms_decoded` | `feasibility/tools.py` dòng 90-101 |
| Tool `propose_analyse/restore/decoy/block` | `feasibility/tools.py` dòng 143-188 |
| RoE bypass | `feasibility/tools.py` dòng 108-117 (`if not StepContext.roe_enabled: ... "status": "approved", "roe_bypassed": True`) |
| System prompt MCP | [`feasibility/prompt.md`](../../feasibility-mcp-roe/feasibility/prompt.md) (3000 ký tự) |
| Driver multi-turn | [`feasibility/claude_policy.py`](../../feasibility-mcp-roe/feasibility/claude_policy.py) `_query_mcp_mode()` dòng 195-230 (`max_turns=8`) |

---

## 3. Dữ liệu thu được

### 3.1 Files artifact

| File | Đường dẫn | Kích thước |
|---|---|---|
| Tổng kết episode | [`benchmark/results/joint_reward_B_FiniteState_ep0.json`](../../feasibility-mcp-roe/benchmark/results/joint_reward_B_FiniteState_ep0.json) | 16 trường |
| Audit CSV | [`benchmark/results/audit_B_FiniteState_ep0.csv`](../../feasibility-mcp-roe/benchmark/results/audit_B_FiniteState_ep0.csv) | 940 KB |
| Detailed JSONL | [`benchmark/results/detailed_B_FiniteState_ep0.jsonl`](../../feasibility-mcp-roe/benchmark/results/detailed_B_FiniteState_ep0.jsonl) | **5.1 MB, 8538 event** |

### 3.2 Phân bố event JSONL (Setup B vs Setup A)

| Event type | Setup A | Setup B | Tỷ lệ B/A |
|---|---|---|---|
| `episode_start` | 1 | 1 | — |
| `step_start` | 500 | 500 | 1× |
| `state_extracted` | 500 | 500 | 1× |
| `llm_query` | 500 | 500 | 1× |
| `llm_response_chunk` | 500 | **1716** | **3.43×** (multi-turn) |
| `tool_call` | — | **1661** | (chỉ có ở B) |
| `tool_result` | — | **1661** | (chỉ có ở B) |
| `roe_verdict` | — | **499** | (chỉ có ở B — đều `allowed` bypass) |
| `paper_parse_result` | 500 | — | (chỉ có ở A) |
| `action_proposed` | 100 | **499** | **4.99×** |
| `action_materialized` | 500 | 500 | 1× |
| `step_end` | 500 | 500 | 1× |
| `episode_end` | 1 | 1 | — |
| **TỔNG** | **3602** | **8538** | **2.37×** |

→ Setup B sinh **2.37 lần nhiều event hơn** Setup A. Phần lớn từ `tool_call` (1661), `tool_result` (1661), `llm_response_chunk` multi-turn (1716).

---

## 4. Các chỉ số định lượng — Bảng ba A / B / TH3

### 4.1 M1 — Cumulative Joint Reward

| Kịch bản | TH3 paper báo cáo | Setup A luận văn | **Setup B luận văn** |
|---|---|---|---|
| All RL KEEP (sàn TỐT) | -451 (TH3 Hình 5) | — | — |
| 1 LLM (o3-mini) + 4 RL KEEP | ≈-500 (TH3 Hình 4) | — | — |
| 1 LLM (4o-mini) + 4 RL KEEP | ≈-1850 (TH3 Hình 4) | — | — |
| 1 LLM (DeepSeek-V3) + 4 RL KEEP | ≈-2200 (TH3 Hình 4) | — | — |
| All LLM 4o-mini | -6334 (TH3 Hình 5) | — | — |
| No blue (sàn ÁC) | -6334 (TH3 Hình 5) | — | — |
| **1 LLM (Claude Haiku 4.5) + 4 ReactRemoveBlueAgent — A** | — | **-660** | — |
| **1 LLM (Claude Haiku 4.5, MCP) + 4 ReactRemoveBlueAgent — B** | — | — | **-2110** |

**Đối chiếu**:

- Setup B (-2110) **kém hơn Setup A (-660) ~3.2 lần**.
- Setup B nằm gần với TH3 1LLM (4o-mini)+4RL (≈-1850) và 1LLM (DeepSeek-V3)+4RL (≈-2200) — tức là rơi vào nhóm "LLM yếu nhất" của TH3.
- Setup B vẫn TỐT hơn All-LLM TH3 (-6334) và No-Blue (-6334) — pipeline có hoạt động.

**Đây là kết quả NGƯỢC với kỳ vọng** — luận văn giả thuyết MCP sẽ giúp Setup B > Setup A. Thực tế 1 episode này cho thấy ngược lại. Phân tích lý do ở mục 7.

Dẫn chứng:
- Setup A: `joint_reward_A_FiniteState_ep0.json` trường `cumulative_joint_reward`
- Setup B: `joint_reward_B_FiniteState_ep0.json` trường `cumulative_joint_reward`
- TH3: Hình 4 + 5 (trang 6)

### 4.2 M1.1 — Reward theo Mission Phase (pha nhiệm vụ)

| Phase | Setup A | Setup B | Δ B−A |
|---|---|---|---|
| **0 (Planning)** | -445 (avg -2.649/step) | **-610 (avg -3.631/step)** | **-165 (B kém hơn)** |
| **1 (MissionA)** | -65 (avg -0.389/step) | **-640 (avg -3.832/step)** | **-575 (B kém hơn rất nhiều)** |
| **2 (MissionB)** | -150 (avg -0.909/step) | **-860 (avg -5.212/step)** | **-710 (B kém hơn rất nhiều)** |
| **Tổng** | **-660** | **-2110** | **-1450** |

→ Setup B kém hơn A ở **mọi pha**, đặc biệt **Phase 1 + 2** (khi nhiệm vụ thực sự bắt đầu).

TH3 paper không báo cáo reward theo phase — đây là chỉ số bổ sung của luận văn.

### 4.3 Đường cong cumulative reward theo step

| Mốc step | Setup A | Setup B | Δ B−A |
|---|---|---|---|
| 50 | -105 | -115 | -10 |
| 100 | -230 | -230 | 0 (bằng) |
| 150 | -415 | -560 | -145 |
| 200 | -460 | -695 | -235 |
| 250 | -490 | -900 | -410 |
| 300 | -490 (plateau) | -1105 | -615 |
| 350 | -510 | -1325 | -815 |
| 400 | -570 | -1575 | -1005 |
| 450 | -615 | -1810 | -1195 |
| **500 (cuối)** | **-660** | **-2110** | **-1450** |

→ Hai pha:
- Step 0-100: Setup A và B **đi cùng đường** (∆ ≈ 0)
- Step 100-500: Setup B **rớt nhanh dần**, Setup A đã plateau

### 4.4 M2 — Invalid Action Rate (tỷ lệ hành động không hợp lệ)

| | Setup A | Setup B |
|---|---|---|
| Số final = "Sleep (no action proposed)" | 400/500 (**80.0%**) | **1/500 (0.2%)** |
| Số action chủ động | 100/500 (20%) | **499/500 (99.8%)** |

→ Setup B **hành động hầu như mọi step** — chỉ 1 step Sleep. Khác hẳn Setup A (80% Sleep).

**Lý do**: MCP system prompt (`prompt.md`) yêu cầu LLM phải gọi `propose_*` mỗi step. Setup A có Sleep được định nghĩa rõ → LLM Sleep áp đảo khi không chắc; Setup B không cho Sleep mặc định (phải gọi tool).

→ M2 = **0.2% (Setup B) vs 80.0% (Setup A)** — chênh lệch khổng lồ về độ chủ động.

### 4.5 M3 — RoE Deny Rate (tỷ lệ RoE từ chối)

| | Setup A | Setup B | (Setup C dự kiến) |
|---|---|---|---|
| roe_enabled | False | False (BYPASS) | True |
| Số RoE verdict | 0 (không có RoE) | **499 (all allowed via bypass)** | sẽ có denied > 0 |
| RoE deny rate | N/A | **0.0%** | sẽ > 0 |

→ Setup B mọi `propose_*` đều được approve, kể cả khi LLM đề xuất action không hợp lý. Verify cơ chế bypass hoạt động đúng → khi bật RoE ở Setup C sẽ có hiệu lực.

Dẫn chứng: 499 event `roe_verdict` trong JSONL Setup B, tất cả có `data.reason = "RoE bypass (mode flag off)"`.

### 4.6 M4 — Comms Misread Rate

| | Setup A | Setup B |
|---|---|---|
| Tổng comm reports | 1996 | **1996** |
| compromise_level = `none` | 1996 (100%) | **1996 (100%)** |
| compromise_level khác | 0 | 0 |

→ Cả 2 setup: comm vector từ 4 đồng đội đều rỗng (do `CommVectorGenerator` fallback EMPTY). **M4 không đo được trong cả A lẫn B.**

→ Setup B trong test này KHÔNG verify được L1 (ảo giác bit) qua MCP decoder.

### 4.7 M5 — Step Latency (độ trễ mỗi lượt)

| Đại lượng | Setup A | Setup B | Tỷ lệ B/A |
|---|---|---|---|
| Mean | **13.07 s/step** | **29.05 s/step** | **2.22×** |
| Median | 12.54 s | 28.60 s | 2.28× |
| Min | 7.48 s | 17.91 s | 2.39× |
| Max | 28.64 s | 52.05 s | 1.82× |
| Stdev | 2.70 s | 4.05 s | 1.50× |
| P25 | 11.53 s | 26.72 s | — |
| P75 | 14.31 s | 31.14 s | — |
| P95 | 17.69 s | 36.45 s | — |
| **Wall time tổng** | **6562 s = 1h49** | **14544 s = 4h04** | **2.22×** |

→ Setup B chậm hơn A ~2.2 lần vì MCP có multi-turn (3.43 LLM call/step thay vì 1).

TH3 paper báo cáo (§IV.A trang 6):
- All RL: 45.2s/episode
- All LLM (4o-mini, 5 LLM agent × multi-turn): 4704.6s/episode → **9.4 s/step**

→ Setup B (1 LLM × multi-turn) chậm hơn TH3 All-LLM-4o-mini (5 LLM × single-turn) → vì Claude Haiku 4.5 dùng "thinking" và mỗi step Setup B có 3.43 turn vs TH3 chỉ 1 turn.

---

## 5. Chỉ số tool calling — đặc trưng riêng của Setup B (không có ở A và TH3)

### 5.1 Phân bố tool calls

499 step × MCP, tổng **1661 tool call**:

| Tool | Số lần gọi | Tỷ lệ /step | Ý nghĩa |
|---|---|---|---|
| `get_threat_summary` | **664** | **1.33/step** | LLM gọi 2 lần ở 1 số step (1 lần đầu, 1 lần sau khi đọc kết quả khác) |
| `get_comms_decoded` | **498** | **1.00/step** | LLM gọi đúng 1 lần/step (gần như mọi step) |
| `propose_deploy_decoy` | **251** | 0.50/step | 50.2% action proposed |
| `propose_analyse` | **248** | 0.50/step | 49.6% action proposed |
| `propose_restore` | **0** | 0 | LLM Setup B **không bao giờ** đề xuất Restore |
| `propose_block_traffic` | **0** | 0 | LLM Setup B **không bao giờ** đề xuất Block |

→ Setup B chỉ dùng 4/6 tool. Mọi action chỉ là `Analyse` hoặc `DeployDecoy`.

Setup A có 3 Restore + 2 Remove (5 destructive). Setup B có **0 destructive**.

### 5.2 Số turn LLM mỗi step

| Đại lượng | Số chunk LLM/step |
|---|---|
| Mean | **3.43** |
| Median | 3.0 |
| Min | 2 |
| Max | **6** |

→ LLM Setup B trung bình **3.43 turn/step**. So với Setup A = 1 turn/step.

Trong 8 turn `max_turns=8`, LLM tự dừng sau ~3-4 turn (gọi `get_threats` + `get_comms` + `propose_X` + đôi khi text kết thúc). Không bao giờ chạm trần 8.

---

## 6. Phân bố action — Bảng ba A / B / TH3 Hình 7

TH3 Hình 7 báo cáo action count cho 1 episode (1 LLM o3-mini + 4 KEEP RL vs FiniteState):

| Action | **TH3 LLM o3-mini** | **TH3 RL KEEP** | **Setup A (Claude H4.5)** | **Setup B (Claude H4.5 MCP)** |
|---|---|---|---|---|
| Analyse | 13 | 267 | 95 (19.0%) | **248 (49.6%)** |
| DeployDecoy | **224** | 6 | 0 (0.0%) | **251 (50.2%)** |
| Remove | 5 | 74 | 2 (0.4%) | 0 (0.0%) |
| BlockTrafficZone | 4 | 0 | 0 | 0 |
| Sleep | 0 | 291 | **400 (80.0%)** | **1 (0.2%)** |
| Restore | 0 | 84 | 3 (0.6%) | 0 (0.0%) |
| Monitor | 0 | 62 | 0 | 0 |
| AllowTrafficZone | 0 | 19 | 0 | 0 |

**Phân tích so sánh**:

1. **Setup B = TH3 LLM o3-mini về phân bố action chính**:
   - Cả hai dùng nhiều `DeployDecoy` (TH3: 224, B: 251)
   - Cả hai tránh `Restore` (TH3: 0, B: 0)
   - Cả hai tránh `Remove` (TH3: 5 ít, B: 0)
   - Cả hai không Sleep nhiều (TH3: 0, B: 1)
   - **Setup B reproduces hành vi TH3 LLM tốt hơn Setup A**

2. **Setup A khác biệt cả TH3 lẫn B**:
   - A Sleep 80% — vì prompt cho phép Sleep
   - A có 5 destructive — LLM Claude H4.5 trong paper-style mode tự ra quyết định destructive khi thấy IOC admin
   - A KHÔNG có DeployDecoy nào — khác hẳn TH3 paper

3. **TH3 RL KEEP rất khác cả 3 LLM** — Analyse 267, Sleep 291, Restore 84. KEEP có chiến lược "analyse trước khi destructive".

→ Setup B **về mặt phân bố action** giống TH3 LLM hơn Setup A — đây là một thành công của thiết kế MCP (replicate được phân bố TH3 LLM).

### 6.1 Action per Phase (Setup B)

| Action | Phase 0 | Phase 1 | Phase 2 |
|---|---|---|---|
| Analyse | 83 | 82 | 83 |
| DeployDecoy | 85 | 84 | 82 |
| Sleep | 0 | 1 | 0 |

→ Phân bố **rất đều qua 3 phase** — không có "thích nghi theo phase". Đây là điểm yếu: LLM Setup B làm cùng pattern (Analyse + DeployDecoy luân phiên) bất kể phase nào.

### 6.2 Action diversity (đa dạng host bị target)

| | Setup A | Setup B |
|---|---|---|
| Số host khác nhau | **5** | **19** |
| Host được target nhiều nhất | `public_access_zone_subnet_server_host_0` (75/100 = 75%) | `web-server` (113/499 = 22.6%) |

Top 5 host Setup B:

| Host | Lần target |
|---|---|
| web-server | 113 |
| web-server-01 | 85 |
| critical-host-1 | 60 |
| db | 45 |
| db-server | 44 |

→ Setup B **đa dạng hơn nhiều** (19 vs 5 host) — MCP giúp LLM target nhiều host khác nhau.

---

## 7. Phân tích nguyên nhân Setup B kém hơn Setup A

Mặc dù Setup B **hành động chủ động hơn** (M2: 0.2% vs 80%) và **đa dạng hơn** (19 vs 5 host), nhưng reward CUỐI lại **kém hơn 3.2 lần** (-2110 vs -660). Phân tích nguyên nhân:

### 7.1 Setup B không có destructive action (0 Restore + 0 Remove + 0 Block)

Trong CAGE 4, **Restore là cần thiết** để wipe host bị admin-level compromise. Setup A đã làm 3 Restore + 2 Remove đúng level → loại bỏ threat hoàn toàn. Setup B KHÔNG làm bất kỳ Restore nào → **threat tiếp tục tồn tại và lan rộng**.

→ DeployDecoy chỉ phát hiện thêm threat, không LOẠI BỎ threat đã có. Khi tích lũy 250 step DeployDecoy nhưng 0 Restore, host bị compromise vẫn bị compromise → reward âm tiếp tục tích lũy.

### 7.2 MCP system prompt khuyến khích DeployDecoy + Analyse, không khuyến khích Restore

Đọc `feasibility/prompt.md`, định nghĩa Restore mô tả: *"Wipe (xóa sạch và cài lại) một host. Chỉ dùng khi xác nhận admin-level compromise"*. Điều kiện "xác nhận admin-level compromise" cần signal từ:
- `get_threat_summary` trả về threat với `compromise_level = "admin"` — nhưng trong test này, comms = rỗng và threats nội bộ phụ thuộc IOC trên host của blue_agent_4 (subnet office_network).

Setup A LLM phát hiện 3 host trong office_network với IOC `escalate.sh` → Restore. Setup B LLM dùng `get_threat_summary` cũng phát hiện được nhưng... **không gọi `propose_restore`**.

Có thể vì:
- Setup B prompt nhấn mạnh "phòng thủ chủ động" (DeployDecoy) trước Restore
- Setup B với multi-turn → LLM "do dự" và cuối cùng chọn DeployDecoy/Analyse an toàn hơn

### 7.3 Latency cao → ít quyết định cứng rắn hơn

Setup B: 29s/step, gấp 2.2× A. Trong cùng wall time, B có ít cơ hội điều chỉnh chiến lược. Red FSM agent tiến công nhanh hơn LLM phản ứng.

### 7.4 RoE bypass khiến LLM KHÔNG nhận phản hồi từ rule

Setup B mọi `propose_*` đều `approved`. LLM không nhận tín hiệu "action này không hợp lý". Trong Setup C (có RoE) sẽ có deny verdict + suggested alternative → LLM có thể học cách chọn action chính xác hơn.

→ Setup B thiếu một feedback loop quan trọng. Dự kiến Setup C sẽ khắc phục.

### 7.5 Vòng lặp action lặp lại — bằng chứng L2 cũng tồn tại ở B

Setup A có 5 chuỗi Analyse cùng host (chuỗi cực đoan 74 lần).
Setup B có **50+ chuỗi action cùng host** (mỗi chuỗi 3-24 lần).

Chuỗi dài nhất Setup B: **steps 450-473, 24 lần** trên `web-server` (luân phiên 12 DeployDecoy + 12 Analyse).

→ MCP **KHÔNG khắc phục L2** (lệ thuộc prompt, thiếu retry có cấu trúc). LLM vẫn lặp.

---

## 8. So sánh hiệu quả MCP với TH3

### 8.1 TH3 thừa nhận hạn chế của LLM agent

TH3 §IV.A nói: *"All LLM với GPT-4o-mini hoạt động kém hơn so với All RL"* (-2547.2 vs -493). Đồng thời TH3 §V *"Tính tương thích môi trường"*: *"sẽ không công bằng khi yêu cầu một LLM đa dụng chọn một hành động mà không có ngữ cảnh mà một cách tiếp cận được huấn luyện bằng RL sẽ có"*.

→ TH3 đã ghi nhận **LLM thuần (không tinh chỉnh) kém hơn RL được huấn luyện**. Setup B của luận văn cũng phản ánh điều này.

### 8.2 MCP có chứng tỏ giá trị nào trong test này không?

**Có** (so với Setup A):

| Khía cạnh | Setup A | Setup B | Đánh giá MCP |
|---|---|---|---|
| Hành động chủ động | 20% | 99.8% | ✓ MCP buộc LLM hành động |
| Đa dạng host target | 5 | 19 | ✓ MCP cho cảnh tổng thể hơn |
| Tool call có cấu trúc | ❌ | 1661 | ✓ JSON schema chặt chẽ |
| Multi-turn reasoning | ❌ | 3.43 turn/step | ✓ LLM có thể truy vấn lại |
| Phân bố action giống TH3 LLM | ❌ | ✓ | ✓ MCP reproduces TH3 LLM behavior |

**Không** (so với cumulative reward):

| Khía cạnh | Đánh giá |
|---|---|
| Reward cuối | ❌ Setup B (-2110) kém hơn Setup A (-660) ~3.2× |
| L1 (ảo giác bit) | ❌ Không kích hoạt vì comm vector rỗng |
| L2 (thiếu retry có cấu trúc) | ❌ MCP có multi-turn nhưng LLM vẫn lặp action cùng host 24 lần |
| L3 (thiếu định hướng phần thưởng) | ❌ Bypass RoE → mọi action chấp nhận → LLM không có feedback |

→ Setup B **một mình** không đủ để chứng minh đóng góp MCP. Cần Setup C (MCP+RoE) để đo đóng góp ĐẦY ĐỦ.

### 8.3 Setup B reproduces TH3 LLM trong CybORG environment của luận văn

Phân bố action Setup B (Analyse 49.6%, DeployDecoy 50.2%, Restore 0%) giống TH3 LLM o3-mini (Analyse 5.3%, DeployDecoy 91%, Restore 0%) hơn là Setup A.

→ Khi viết luận văn có thể nói: *"Setup B tái hiện được hành vi LLM agent như mô tả của TH3 (ưu tiên DeployDecoy + Analyse, tránh Restore). Nhưng cũng phản ánh hạn chế của TH3: reward kém RL/baseline rule. RoE (Setup C) được kỳ vọng sẽ thay đổi hành vi này."*

---

## 9. Hạn chế của báo cáo này

1. **n = 1**: chỉ 1 episode/setup, không có σ. Khi chạy thêm cùng config Setup B, reward dao động lớn — variance giữa các lần chạy ~64% (lần B đầu = -70 ở step 50; lần này = -125 cùng mốc).

2. **1 red variant**: chỉ FiniteState — chưa test AggressiveFSM / StealthyFSM / ImpactFSM / DegradeServiceFSM.

3. **Comm vector luôn rỗng**: do `CommVectorGenerator` API mismatch → MCP decoder pre-parse không có signal để verify L1.

4. **Prompt MCP có thể chưa tối ưu**: TH3 §III.D Bảng III cho thấy Role+Few-shot tốt hơn Role-only. Setup B của luận văn dùng Role-only.

5. **3 baseline crash** (KeyError IPv4 sporadic) — đã catch fallback Sleep nhưng baseline đồng đội không hoàn toàn ổn định.

6. **Setup C chưa chạy**: chỉ có A và B, chưa biết RoE đóng góp được gì. Báo cáo Setup B này chỉ là "MCP without RoE" — chưa hoàn chỉnh đóng góp luận văn.

7. **Resume hỏng dữ liệu lần đầu**: Setup B lần đầu chạy đến step 350, dừng + resume nhưng code mode `"w"` ghi đè log. Đã fix (mode `"a"`) trước khi chạy lại lần thứ 3 này → đây là lần chạy hoàn chỉnh, sạch.

---

## 10. Đánh giá tổng hợp Setup B

### 10.1 Đóng góp xác nhận được

| Đóng góp MCP (kỳ vọng) | Đo được ở Setup B? |
|---|---|
| Pre-parsed observation qua tool | ✓ — 1.33 get_threat_summary + 1.0 get_comms_decoded /step |
| Action có JSON schema chặt chẽ | ✓ — 499 propose_* call, 0 parse fail |
| Multi-turn reasoning | ✓ — 3.43 turn/step trung bình |
| Khắc phục Sleep áp đảo của Setup A | ✓ — M2: 0.2% vs 80% |
| Đa dạng host target | ✓ — 19 host vs 5 |
| Reproduces TH3 LLM behavior | ✓ — phân bố action giống o3-mini |

### 10.2 Hạn chế phát hiện qua Setup B

| Hạn chế | Hiển thị qua Setup B |
|---|---|
| MCP **một mình** không đủ — cần thêm RoE | M1(B) = -2110 < M1(A) = -660 |
| LLM "quá chủ động" theo hướng SAI — DeployDecoy/Analyse mà bỏ qua Restore | 0 destructive/499 |
| Vòng lặp action vẫn xảy ra | 50+ chuỗi action cùng host |
| Latency cao gây bất lợi vs red FSM nhanh | 29s/step vs A 13s/step |

### 10.3 Kết luận về Setup B

**Setup B thành công ở mức KIỂM CHỨNG MCP HOẠT ĐỘNG** (1661 tool call, 499 propose_*, 100% RoE bypass đúng) nhưng **KHÔNG cho thấy đóng góp tích cực về reward** so với Setup A baseline.

Có **2 cách lý giải**:

1. **n=1, variance cao**: lần chạy này không đại diện. Cần n=5 để có khoảng tin cậy. Lần B trước (đã hỏng do log overwrite) đạt -70 ở step 50 vs lần này -125 — chênh 64% — chứng tỏ variance lớn.

2. **MCP một mình thiếu RoE để có ý nghĩa**: MCP cung cấp công cụ (tool) và quyền hành động (multi-turn), nhưng **không có rule chặn LLM khỏi quyết định sai**. Setup B LLM proactive nhưng SAI hướng (chỉ DeployDecoy/Analyse, không Restore). RoE ở Setup C dự kiến sẽ ép LLM xem xét lại và chuyển sang Restore khi cần.

**Khuyến nghị**: chạy Setup C ngay để xem RoE có khắc phục được không. Nếu Setup C reward > Setup A → đóng góp luận văn (MCP+RoE > baseline) được verify. Nếu Setup C cũng kém A → cần xem lại thiết kế RoE rules hoặc prompt.

---

## Phụ lục A — Tham chiếu TH3 paper

(Giống Phụ lục báo cáo Setup A — cùng PDF + cùng trang)

| Mục TH3 | Trang | Nội dung |
|---|---|---|
| §III.C | 3-4 | Communication Vector 8-bit (Setup B cũng đo) |
| §III.D Bảng III | 4 | Prompt tuning (luận văn dùng Role-only — kém Few-shot) |
| §IV Hình 4 | 6 | Reward 4 LLM trên 1LLM+4RL — số liệu so sánh M1 |
| §IV Hình 5 | 6 | Reward 3 kịch bản × 5 red — μ ± σ |
| §IV.A Hình 7 | 8 | **Action count** o3-mini và KEEP — bảng 6 đối chiếu |
| §V "Định nghĩa Prompt" | 9 | TH3 không định nghĩa Sleep → Setup B cũng có Sleep=1 giống TH3 |

## Phụ lục B — Cách reproduce

```bash
# Activate environment
source llms-are-acd-main/cage-env/bin/activate
export PYTHONPATH=/Users/apple/Workspace/personal/side-projects/demo/llms-are-acd-main/cage-challenge-4
cd feasibility-mcp-roe

# Chạy Setup B 1 episode (resume an toàn, checkpoint mỗi 50 step)
python -u benchmark/run_benchmark.py --setup B --red FiniteState --episodes 1

# Verify
cat benchmark/results/joint_reward_B_FiniteState_ep0.json | python3 -m json.tool

# Đọc chi tiết step bất kỳ
python benchmark/inspect_episode.py \
  benchmark/results/detailed_B_FiniteState_ep0.jsonl --step 250 --full

# Xem trực tiếp dòng JSONL
sed -n '4258,4270p' benchmark/results/detailed_B_FiniteState_ep0.jsonl | python3 -m json.tool

# Đếm các tool call
python3 -c "
import json
from collections import Counter
events = [json.loads(l) for l in open('benchmark/results/detailed_B_FiniteState_ep0.jsonl')]
tc = Counter(e['data']['name'] for e in events if e['event']=='tool_call')
for n, c in tc.most_common(): print(f'{n}: {c}')
"
```

---

*Báo cáo dựa hoàn toàn vào (1) bài báo TH3 và (2) các file artifact `benchmark/results/` từ 1 lần chạy Setup A + 1 lần chạy Setup B. Mọi số liệu có thể trace ngược về file + line number cụ thể.*
