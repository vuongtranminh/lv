# BÁO CÁO TỔNG KẾT SPRINT 4 — SO SÁNH FAIR MCP+RoE VỚI TH3

**Học viên**: Trần Minh Vương
**Ngày lập**: 2026-07-05
**Phạm vi**: Sprint 4 — so sánh fair MCP+RoE với TH3 baseline trên cùng prompt

---

## MỤC LỤC

1. [Tóm tắt điều hành](#1-tóm-tắt-điều-hành)
2. [Bối cảnh và mục tiêu](#2-bối-cảnh-và-mục-tiêu)
3. [Thiết kế thí nghiệm](#3-thiết-kế-thí-nghiệm)
4. [Kết quả benchmark](#4-kết-quả-benchmark)
5. [Phân tích cơ chế](#5-phân-tích-cơ-chế)
6. [Các phát hiện quan trọng](#6-các-phát-hiện-quan-trọng)
7. [Hạn chế](#7-hạn-chế)
8. [Hướng phát triển Sprint 5+](#8-hướng-phát-triển-sprint-5)
9. [Kết luận](#9-kết-luận)

---

## 1. TÓM TẮT ĐIỀU HÀNH

Sprint 4 thực hiện thí nghiệm **so sánh fair** giữa MCP+RoE (đóng góp luận văn) và baseline TH3 (Castro et al., IEEE CAI 2025) khi giữ nguyên biến số **prompt content** (byte-identical với `acd2025/base.yml`) và **model** (Claude Haiku 4.5).

### Kết quả tổng hợp qua 3 red variants

| Red variant | A-TH3 (baseline) | C-TH3 (MCP+RoE V3) | Delta |
|---|---|---|---|
| **FiniteState** (n=4) | −3280 ± 3616 | **−1807.5 ± 875** | **C hơn A +1472.5** ✅ |
| **AggressiveFSM** (n=2) | −2150 ± 990 | **−2007.5 ± 718** | C hơn A +142.5 ⚠️ |
| **StealthyFSM** (n=2) | **−960 ± 290** | −1377.5 ± 909 | **A hơn C +417.5** ❌ |

### Kết luận trung tâm

**MCP+RoE V3 có giá trị PHỤ THUỘC red variant** — không phải "MCP+RoE luôn tốt hơn TH3" như em claim ban đầu:

1. **Red unpredictable** (FiniteState): **MCP+RoE cực tốt** — cải thiện +1472 điểm, giảm variance 4 lần
2. **Red predictable** (AggressiveFSM): **MCP+RoE neutral** — improvement trong noise (+142)
3. **Red stealth** (StealthyFSM): **MCP+RoE COUNTER-PRODUCTIVE** — làm hại reward −417 điểm

Đây là finding tinh tế hơn nhiều so với claim ban đầu, mở ra hướng nghiên cứu về **adaptive RoE** — quota động theo red behavior.

### Phát hiện phụ

- **Phase confusion bug trong TH3 gốc**: 76% response A-TH3 hiểu SAI phase encoding (env phase=1 = MissionA active, LLM đọc "Phase 1" = Pre-planning trong prompt)
- **MCP giảm confusion GIÁN TIẾP**: từ 76% (A) xuống 27% (C) — chủ yếu do tool call chiếm turn budget
- **Ep0 seed=0 là outlier extreme cho FiniteState**: A-TH3 ep0 = −8685 (worst case), do combined luck của Red path + RL blue stochastic

---

## 2. BỐI CẢNH VÀ MỤC TIÊU

### 2.1 Vì sao có Sprint 4

Sprint 3 phát hiện Setup A cũ của em (`feasibility-mcp-roe/paper_style.py`) đã bị "buff" nhiều so với TH3 gốc — thêm IOC rules, Analyse threshold, Sleep guidance. Nên khi so "C tốt hơn A", **không thể claim** MCP+RoE tốt hơn baseline TH3 — vì A của em không phải TH3 thật.

Sprint 4 giải quyết bằng cách:
- Dùng **CHÍNH XÁC prompt TH3** (`acd2025/base.yml`, byte-identical) cho cả A-TH3 và C-TH3
- Chỉ khác 2 chỗ output format (JSON → MCP tool call) cho Setup C
- So sánh mean ± std trên nhiều red variants

### 2.2 Ba câu hỏi nghiên cứu

1. **Prompt content đóng vai trò gì?** — TH3 prompt trên Haiku 4.5 đạt reward bao nhiêu?
2. **MCP paradigm có giá trị khi giữ nguyên prompt?** — Chuyển JSON → tool call có cải thiện không?
3. **RoE V3 có giá trị khi thiết kế theo reward function?** — 6 rule deterministic có cải thiện không?

---

## 3. THIẾT KẾ THÍ NGHIỆM

### 3.1 Cấu hình chung

| Yếu tố | Giá trị |
|---|---|
| Môi trường | CybORG CAGE 4 |
| Model LLM | Claude Haiku 4.5 |
| Blue agent LLM | `blue_agent_4` (public/admin/office zones) |
| 4 blue agent còn lại | ReactRemoveBlueAgent (RL baseline TH3) |
| Số step/episode | 500 |
| Số episode/config | n ≥ 2 (FiniteState n=4, các red khác n=2) |

### 3.2 Prompt

**Nguồn**: `llms-are-acd-main/CybORG/Agents/LLMAgents/config/prompts/acd2025/base.yml` (142 dòng tiếng Anh, byte-identical với TH3 gốc)

**Setup A-TH3**: load nguyên bản, output single-shot JSON
**Setup C-TH3**: load nguyên bản + **thay thế in-place** 2 đoạn liên quan output format:
- Đoạn "Respond EXACTLY with one response as a dictionary..." → đoạn hướng dẫn dùng MCP tools
- 5 example JSON → 5 example tool call

**Tất cả section khác giữ 100% byte-identical** với TH3.

### 3.3 RoE V3 — 6 rule reward-focused

| Rule | Nội dung | Căn cứ reward |
|---|---|---|
| R1 | Restore chỉ khi admin + critical zone active phase | Restore tốn 5 tick downtime |
| R2 | Cấm Block operational zone active phase | Block gây ASF −10/lần |
| R3 | Max 5 Restore/episode | Cascade damage limit |
| R4 | Max 2 Analyse/host | Analyse lần 3+ không thêm info |
| R5 | Max 2 decoy/host, max 10 tổng/ep | Chống spam decoy cascade |
| R6 | Sleep luôn approve | Sleep chi phí 0 |

### 3.4 Red variants đã test

| Red variant | Mô tả | Đặc điểm |
|---|---|---|
| **FiniteStateRedAgent** | Balanced FSM, transitions ngẫu nhiên | Attack path unpredictable |
| **AggressiveFSMAgent** | Ưu tiên loud scan | Attack path predictable, dễ bị detect |
| **StealthyFSMAgent** | Ưu tiên quiet scan | Attack path chậm, lén lút |

Còn 2 red variants **CHƯA test**: ImpactFSM, DegradeServiceFSM (hướng Sprint 5).

---

## 4. KẾT QUẢ BENCHMARK

### 4.1 Bảng reward tổng hợp

**Data quality**: 26/26 file log SẠCH 100% (0 rate limit sau khi rerun ep1 FiniteState nhiễm rate limit).

| Red variant | Setup | ep0 | ep1 | ep2 | ep3 | Mean | Std |
|---|---|---|---|---|---|---|---|
| **FiniteState** | A-TH3 (n=4) | −8685 | −1675 | −1715 | −1045 | −3280 | ±3616 |
| | C-TH3 (n=4) | −750 | −1645 | −1965 | −2870 | −1807.5 | ±875 |
| **AggressiveFSM** | A-TH3 (n=2) | −2850 | −1450 | | | −2150 | ±990 |
| | C-TH3 (n=2) | −2515 | −1500 | | | −2007.5 | ±718 |
| **StealthyFSM** | A-TH3 (n=2) | −755 | −1165 | | | −960 | ±290 |
| | C-TH3 (n=2) | −2020 | −735 | | | −1377.5 | ±909 |

### 4.2 So với TH3 paper (Hình 5)

| Baseline | Reward |
|---|---|
| Sàn: không có blue nào | −6334 |
| Trần: 5 blue = RL KEEP | −451 |
| 1 LLM GPT-4o-mini + 4 RL KEEP | ~−1850 |
| 1 LLM o3-mini + 4 RL KEEP | ~−500 |
| **Sprint 4 A-TH3 FiniteState mean** | **−3280** (giữa GPT-4o-mini và no-blue) |
| **Sprint 4 C-TH3 FiniteState mean** | **−1807.5** (gần GPT-4o-mini) |
| **Sprint 4 C-TH3 FiniteState best case** | **−750** (gần o3-mini) |

### 4.3 Delta C vs A theo red variant

| Red | Delta (C - A, dương = C tốt hơn) | Ý nghĩa |
|---|---|---|
| **FiniteState** | **+1472.5** | MCP+RoE giá trị RẤT CAO |
| **AggressiveFSM** | **+142.5** | Trong noise, không significant |
| **StealthyFSM** | **−417.5** | MCP+RoE COUNTER-PRODUCTIVE |

---

## 5. PHÂN TÍCH CƠ CHẾ

### 5.1 Vì sao MCP+RoE có 3 kịch bản khác nhau

**Setup A-TH3 hành xử Y HỆT nhau ở cả 3 red**:
- Sleep: 0-1
- Analyse: 181-184
- DeployDecoy: 315-319
- LLM Haiku không "biết" đang bị red variant nào — chỉ theo prompt template

→ Reward khác biệt hoàn toàn do **red attack effectiveness**, không phải LLM behavior.

**Setup C-TH3 với RoE V3 R5 (MAX_DECOYS_TOTAL=10)**:

| Red variant | Blue A spam ~319 decoys | Blue C cap 10 decoys | Kết quả |
|---|---|---|---|
| **FiniteState** (random) | 319 decoys gây cascade damage → phạt cao | 10 decoys → tránh cascade | **C tốt hơn** ✅ |
| **AggressiveFSM** (loud) | 319 decoys, RL blue detect được | 10 decoys, RL blue vẫn detect | **Neutral** ⚠️ |
| **StealthyFSM** (slow) | 315 decoys = **rải thảm bẫy** → catch quiet scans | 10 decoys → mật độ loãng → Stealthy có kẽ hở | **A tốt hơn** ❌ |

### 5.2 Cơ chế RoE V3 chặn LLM sai — bằng chứng định lượng

Trong C-TH3 FiniteState ep0 (500 step):
- **889 RoE verdicts** (LLM đề xuất tổng cộng)
- **599 deny (67.4%)** — RoE chặn 2/3 đề xuất của LLM
- **R5 (decoy quota)**: chặn **212 lần** DeployDecoy dư thừa
- **R4 (analyse per-host)**: chặn **103 lần** Analyse spam

**Bằng chứng deterministic**: cả 2 ep C-TH3 FiniteState đều dừng đúng **10 decoy** — không phải 9, không phải 11. R5 cap chính xác.

### 5.3 Phát hiện phase confusion — Bug prompt design TH3

**Mismatch giữa prompt và env**:

| Env value | Env meaning | Prompt gọi | Kết quả |
|---|---|---|---|
| 0 | Planning | "Phase 1 (Pre-planning)" | Match ✓ |
| 1 | **MissionA active** | **Prompt gọi "Phase 2A"** | LLM đọc "Phase 1" → hiểu SAI là Pre-planning ✗ |
| 2 | MissionB active | "Phase 2B" | Ambiguous |

**Thống kê phase confusion per-step** (trong 167 step khi env đang ở MissionA active):

| Setup | Confusion rate |
|---|---|
| A-TH3 mean | **~76%** |
| C-TH3 mean | **~27%** (3× thấp hơn) |

**Vì sao C-TH3 confusion ít hơn** (3 giả thuyết đã test):

| Giả thuyết | Bằng chứng | Đóng góp giảm confusion |
|---|---|---|
| Tool call chiếm turn budget | A 96.4% chunks mention phase; C chỉ 10.4% | **~80%** |
| Structured state giảm confusion | A 85.7% wrong per mention; C 64.4% | **~20%** |
| Multi-turn cho self-correction | LLM không tự sửa, chỉ ít nói | ~0% |

→ MCP paradigm giảm phase confusion **GIÁN TIẾP** qua turn budget, không phải self-correction.

### 5.4 Phân tích ep0 outlier −8685 (A-TH3 FiniteState)

**Damage timeline**:

| Step window | ep0 cumulative | ep3 cumulative | Chênh |
|---|---|---|---|
| 0-200 | −510 | −545 | −35 (gần bằng nhau) |
| 200-300 | −1780 | −55 | **+1725** (ep0 bùng nổ) |
| 300-500 | **−6395** | −455 | +5940 |

**Nguyên nhân**: Ep0 seed=0 rơi vào scenario "worst-case combination":
- Red FiniteState may mắn thâm nhập operational_zone_a **trước step 168** (Phase 1 activation)
- Khi Phase 1 kích hoạt → mỗi RIA/LWF/ASF trong operational zone phạt **−10**
- Red persistent → damage cascade 100-155/step

**Ep3 seed=3 tránh được**: Red không thâm nhập operational_zone_a → damage nhỏ đều.

→ **Env stochasticity** (Red + RL blue random) là nguồn variance chính, KHÔNG phải LLM behavior.

### 5.5 Định lượng lợi ích MCP đã chứng minh (giữ từ Sprint 1-3, xác nhận Sprint 4)

| Hạn chế TH3 | Sprint 4 evidence | Trạng thái |
|---|---|---|
| Ảo giác 8-bit | **0 parse fail** trên toàn bộ 26 file log | ✅ Giải quyết |
| Ảo giác hostname | Hostname validation reject 100% invalid names | ✅ Giải quyết |
| Destructive actions không căn cứ | RoE R1 chặn Restore user-level (rule fires khi cần) | ✅ Giải quyết |

---

## 6. CÁC PHÁT HIỆN QUAN TRỌNG

### Finding #1: Baseline TH3 trên Haiku 4.5 hoạt động KÉM

- A-TH3 FiniteState mean = **−3280** (giữa GPT-4o-mini −1850 và no-blue −6334)
- Ep0 outlier −8685 **TỆ HƠN CẢ NO-BLUE** → LLM đôi khi làm phản tác dụng
- Cho thấy Haiku 4.5 kém xa o3-mini (reasoning model) trên task defense complex

### Finding #2: MCP+RoE cải thiện CÓ ĐIỀU KIỆN theo red variant

- FiniteState: C hơn A **+1472** (rất tốt)
- AggressiveFSM: C hơn A **+142** (neutral)
- StealthyFSM: **A hơn C +417** (counter-productive)

Đây là finding trung tâm — reframe claim ban đầu "MCP+RoE luôn tốt hơn".

### Finding #3: RoE V3 giảm variance 4× với FiniteState

A-TH3 std ±3616 (do ep0 outlier) vs C-TH3 std ±875 — RoE V3 cap decoy tránh worst-case disaster.

### Finding #4: RoE V3 rule cụ thể có tác dụng đo được

- R5 (decoy quota) chặn 212 đề xuất/episode → decoy dừng đúng 10 cả 2 ep
- R4 (analyse max/host) chặn 103 đề xuất/episode → phân tán qua 23 host

### Finding #5: MCP giảm phase confusion GIÁN TIẾP

- A-TH3 confusion 76% → C-TH3 confusion 27% (giảm 3 lần)
- Cơ chế chính: **turn budget** (~80%) và **structured state** (~20%)
- LLM Haiku KHÔNG có khả năng self-correction (không tự sửa dù multi-turn)

### Finding #6: Bug prompt design của TH3 gốc chưa được document

Prompt TH3 dùng ngữ hệ "Phase 1/2A/2B" nhưng env trả integer `0/1/2` → mismatch → LLM Haiku hiểu SAI phase encoding 76% thời gian. Có thể o3-mini xử lý được nhưng Haiku thì không.

### Finding #7: RoE V3 CẦN ADAPTIVE

Hard-coded `MAX_DECOYS_TOTAL=10` **overfit cho FiniteState**:
- Với FiniteState: 10 decoys đủ → tránh cascade
- Với StealthyFSM: 10 decoys quá ít → mất khả năng detect slow scans
- Cần **quota động** dựa trên red behavior signal

### Finding #8: Ep0 seed=0 là outlier do env stochasticity

Damage explosion sau step 200 do Red may mắn thâm nhập operational zone → Phase 1 penalty −10 nhân lên → −8685. Các seed khác (1, 2, 3) tránh được → mean ±376 (rất ổn định).

---

## 7. HẠN CHẾ

### 7.1 Data limitations

- **n=2 cho AggressiveFSM và StealthyFSM** — chỉ đủ tối thiểu tính std, chưa có significance thống kê
- **Chỉ test 3/5 red variants** — thiếu ImpactFSM, DegradeServiceFSM
- **Chỉ Haiku 4.5** — chưa test Sonnet, Opus, o3-mini

### 7.2 Method limitations

- **Chỉ 1/5 blue agent là LLM** — 4 blue còn lại là RL baseline chung → biến số RL random có thể lây sang comparison
- **Phase confusion** ảnh hưởng cả A và C — chưa fix để so sánh "clean"
- **RoE V3 hard-coded quota** — không adaptive theo red

### 7.3 Scope limitations

- Sprint 4 tập trung so sánh **reward**, chưa đo interpretability, latency, cost metric
- Chưa document được **case study cụ thể** trong luận văn (need write Chapter 5)

---

## 8. HƯỚNG PHÁT TRIỂN SPRINT 5+

### 8.1 Complete 5 red variants (theo TH3 paper)

- **ImpactFSM** — kẻ tấn công tập trung Impact action → RIA nhiều
- **DegradeServiceFSM** — làm chậm dịch vụ dần → cascade LWF/ASF

Ước tính: 4 lần chạy × 2 setup × ~4h/ep = **~32 giờ benchmark**.

### 8.2 Adaptive RoE

Sửa RoE V3 để **quota động** theo red behavior:

```python
# Pseudocode
if red_scan_events_last_50_steps > threshold_high:
    MAX_DECOYS_TOTAL = 20  # tăng decoy khi nhiều Red scan
elif red_scan_events_last_50_steps < threshold_low:
    MAX_DECOYS_TOTAL = 5   # giảm khi Red im lặng (có thể Stealthy đã compromise?)
```

Test lại 3 red variants → xem có cải thiện được cả 3 kịch bản không.

### 8.3 Fix phase encoding

Sửa prompt để match env:
- Đổi "Phase 1 (Pre-planning)" → "Phase 0 (Planning)"
- Đổi "Phase 2A" → "Phase 1 (MissionA active)"
- Đổi "Phase 2B" → "Phase 2 (MissionB active)"

Chạy lại A-TH3 và C-TH3 → xem confusion giảm bao nhiêu, reward cải thiện bao nhiêu.

### 8.4 Multi-model comparison

Test với **Claude Sonnet 4.6** và **Opus 4.8** — kiểm chứng finding "context-dependent value" có holds cho model mạnh hơn không.

### 8.5 Extend interpretability metrics

Ngoài reward, đo:
- **# tool calls**/step (proxy cho complexity của reasoning)
- **RoE deny rate** per rule (cơ chế đang chặn cái gì)
- **Latency** per step
- **Token cost** per episode

---

## 9. KẾT LUẬN

Sprint 4 chuyển từ claim đơn giản "MCP+RoE tốt hơn TH3" sang câu chuyện tinh tế hơn:

> *"MCP+RoE V3 có giá trị PHỤ THUỘC context tấn công. Cải thiện đáng kể với red unpredictable (chặn cascade damage), neutral với red predictable, và có thể COUNTER-PRODUCTIVE với red stealth (quota cap làm mất khả năng detect). Hard-coded quota `MAX_DECOYS_TOTAL=10` overfit cho FiniteState. RoE V3 cần adaptive để phù hợp mọi red variant."*

### Đóng góp khoa học đã chứng minh

1. **MCP eliminates ảo giác 8-bit** (0 parse fail / 26 file log)
2. **RoE deterministic chặn hành động sai** — 67% đề xuất LLM bị deny theo rule reward-focused
3. **RoE giảm variance 4×** với red unpredictable (safety net cho worst-case)
4. **MCP giảm phase confusion GIÁN TIẾP** qua turn budget (finding phụ)
5. **Phát hiện bug prompt design TH3 gốc** (mismatch phase encoding)
6. **Context-dependent value** của RoE (finding mới, quan trọng)

### Câu hỏi mở

- Nếu adaptive RoE có thể handle được cả 3 red variants → MCP+RoE trở thành "universal improvement"?
- Model mạnh hơn (Sonnet/Opus/o3-mini) có gặp phase confusion không? Có làm C-TH3 lép vế nữa không?
- Có tồn tại "worst case" tương tự ep0 FiniteState cho AggressiveFSM và StealthyFSM không (cần chạy nhiều n hơn)?

### Sản phẩm Sprint 4 để bàn giao

- **Code**: [mcp-roe-vs-th3/](https://github.com/vuongtranminh/lv/tree/main/mcp-roe-vs-th3) — 12 file Python + tests
- **Prompt**: [feasibility/prompts/acd2025/base.yml](https://github.com/vuongtranminh/lv/blob/main/mcp-roe-vs-th3/feasibility/prompts/acd2025/base.yml) — byte-identical với TH3
- **Data**: 26 file benchmark (12 audit + 12 detailed JSONL + 12 joint_reward)
- **Báo cáo**:
  - [SETUP_REPORT.md](https://github.com/vuongtranminh/lv/blob/main/mcp-roe-vs-th3/SETUP_REPORT.md) — thiết kế thí nghiệm
  - [KET_QUA_SPRINT_4.md](https://github.com/vuongtranminh/lv/blob/main/mcp-roe-vs-th3/KET_QUA_SPRINT_4.md) — kết quả chi tiết (1117 dòng)
  - [BAO_CAO_TONG_KET_SPRINT_4.md](https://github.com/vuongtranminh/lv/blob/main/mcp-roe-vs-th3/BAO_CAO_TONG_KET_SPRINT_4.md) — file này (báo cáo tổng kết)

---

**Trần Minh Vương** — Sprint 4 hoàn thành ngày 2026-07-05
