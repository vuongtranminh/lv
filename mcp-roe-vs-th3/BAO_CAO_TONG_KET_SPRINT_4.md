# BÁO CÁO TỔNG KẾT SPRINT 4
## So sánh fair MCP+RoE với baseline TH3 trên cùng prompt

**Học viên**: Trần Minh Vương
**Đơn vị**: (Luận văn thạc sĩ)
**Ngày lập báo cáo**: 2026-07-05
**Phạm vi**: Toàn bộ hoạt động và kết quả Sprint 4 (2026-06-25 → 2026-07-05)
**Đối tượng đọc**: Giáo viên hướng dẫn, hội đồng luận văn

---

## MỤC LỤC

- [PHẦN I. TỔNG QUAN](#phần-i-tổng-quan)
  - [1. Mục đích Sprint 4](#1-mục-đích-sprint-4)
  - [2. Bối cảnh: Vì sao cần Sprint 4](#2-bối-cảnh-vì-sao-cần-sprint-4)
  - [3. Câu hỏi nghiên cứu](#3-câu-hỏi-nghiên-cứu)
  - [4. Tóm tắt kết quả 1 trang](#4-tóm-tắt-kết-quả-1-trang)
- [PHẦN II. THIẾT KẾ THÍ NGHIỆM](#phần-ii-thiết-kế-thí-nghiệm)
  - [5. Nguyên tắc so sánh fair](#5-nguyên-tắc-so-sánh-fair)
  - [6. Cấu hình chung](#6-cấu-hình-chung)
  - [7. Setup A-TH3 — Baseline](#7-setup-a-th3--baseline)
  - [8. Setup C-TH3 — Đóng góp luận văn](#8-setup-c-th3--đóng-góp-luận-văn)
  - [9. RoE V3 — 6 rule reward-focused](#9-roe-v3--6-rule-reward-focused)
  - [10. Các red variants đã test](#10-các-red-variants-đã-test)
- [PHẦN III. KẾT QUẢ BENCHMARK CHI TIẾT](#phần-iii-kết-quả-benchmark-chi-tiết)
  - [11. Bảng tổng hợp reward](#11-bảng-tổng-hợp-reward)
  - [12. FiniteState (n=4) — Red truyền thống](#12-finitestate-n4--red-truyền-thống)
  - [13. AggressiveFSM (n=2) — Red loud/predictable](#13-aggressivefsm-n2--red-loudpredictable)
  - [14. StealthyFSM (n=2) — Red quiet/slow](#14-stealthyfsm-n2--red-quietslow)
  - [15. So với TH3 paper (Castro et al., IEEE CAI 2025)](#15-so-với-th3-paper-castro-et-al-ieee-cai-2025)
- [PHẦN IV. PHÂN TÍCH CƠ CHẾ](#phần-iv-phân-tích-cơ-chế)
  - [16. Vì sao MCP+RoE có 3 kịch bản khác nhau](#16-vì-sao-mcproe-có-3-kịch-bản-khác-nhau)
  - [17. Bằng chứng RoE V3 hoạt động — deny stats](#17-bằng-chứng-roe-v3-hoạt-động--deny-stats)
  - [18. Bằng chứng MCP eliminates ảo giác — parse stats](#18-bằng-chứng-mcp-eliminates-ảo-giác--parse-stats)
  - [19. Phase confusion — Bug prompt design TH3 gốc](#19-phase-confusion--bug-prompt-design-th3-gốc)
  - [20. Ep0 outlier −8685 — Phân tích cơ chế](#20-ep0-outlier-8685--phân-tích-cơ-chế)
- [PHẦN V. FINDINGS TỔNG HỢP](#phần-v-findings-tổng-hợp)
- [PHẦN VI. HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN](#phần-vi-hạn-chế-và-hướng-phát-triển)
- [PHẦN VII. PHỤ LỤC](#phần-vii-phụ-lục)

---

# PHẦN I. TỔNG QUAN

## 1. Mục đích Sprint 4

### 1.1 Mục đích chính

Sprint 4 có **một mục đích duy nhất**: chứng minh (hoặc bác bỏ) claim "MCP + RoE cải thiện LLM-based blue agent so với TH3 baseline" bằng thí nghiệm **có kiểm soát chặt biến số**.

Cụ thể:
- **Cô lập biến số** "MCP paradigm + RoE V3" — tất cả biến số khác (prompt, model, red variant, môi trường) phải **giữ nguyên**
- **So sánh trực tiếp** reward giữa Setup A (baseline TH3) và Setup C (đóng góp) trong cùng điều kiện
- **Đủ n để tính variance** — không để 1 episode may/xui quyết định kết luận

### 1.2 Mục đích phụ

Song song, Sprint 4 cũng nhắm:
1. **Reproduce TH3 trên Haiku 4.5** — biết baseline paper hoạt động ra sao trên model em dùng
2. **Sinh dữ liệu log chi tiết** cho Chương 5 luận văn (case studies, ví dụ cụ thể)
3. **Phát hiện bug/limitation** của thiết kế RoE V3 hiện tại (nếu có) trước khi bảo vệ

### 1.3 Sản phẩm đầu ra Sprint 4

Sản phẩm cụ thể phải bàn giao:
- Code Setup A-TH3 và Setup C-TH3 hoạt động độc lập, có thể reproduce
- Prompt TH3 byte-identical với gốc (`acd2025/base.yml`, đã upstream)
- Ít nhất **n=2 episode/setup** × **≥2 red variant** = ≥ 8 file log sạch
- Báo cáo phân tích với bằng chứng số liệu (file này)

---

## 2. Bối cảnh: Vì sao cần Sprint 4

### 2.1 Vấn đề phát hiện ở cuối Sprint 3

**Sprint 3** thực hiện so sánh 3 setup A/B/C cùng dùng Claude Haiku 4.5, kết luận "C tốt hơn A". Tuy nhiên khi review lại code, phát hiện Setup A cũ (`feasibility-mcp-roe/paper_style.py`) đã bị **buff nhiều** so với TH3 gốc:

| Thành phần Setup A cũ | Nguồn gốc | Vấn đề |
|---|---|---|
| IOC (Indicators of Compromise) rules | Tự thêm | Không có trong TH3 |
| Analyse threshold heuristic | Tự thêm | Không có trong TH3 |
| Sleep guidance chi tiết | Tự thêm | Không có trong TH3 |
| System prompt trong tiếng Việt | Tự viết | TH3 dùng tiếng Anh |

→ **Setup A cũ KHÔNG phải là TH3 thật** → so sánh "C tốt hơn A" không thể claim là "MCP+RoE tốt hơn baseline TH3"

### 2.2 Rủi ro nếu không có Sprint 4

Nếu bỏ qua vấn đề này và bảo vệ luận văn với claim "MCP+RoE tốt hơn TH3":
- **Rủi ro thẩm định**: Hội đồng có thể yêu cầu chạy lại với prompt TH3 gốc
- **Rủi ro reproducibility**: Không thể so sánh trực tiếp với số liệu paper
- **Rủi ro credibility**: Claim thiếu bằng chứng chặt chẽ

### 2.3 Giải pháp

Sprint 4 tạo project mới `mcp-roe-vs-th3/` chạy song song với `feasibility-mcp-roe/` (không sửa code cũ), trong đó:
- **Setup A-TH3**: Load **byte-identical** file `acd2025/base.yml` từ TH3 repo
- **Setup C-TH3**: Cùng file trên + **thay thế in-place 2 đoạn** liên quan output format (JSON → MCP tool call)
- Chỉ khác nhau ở 2 đoạn được document rõ ràng trong SETUP_REPORT.md

---

## 3. Câu hỏi nghiên cứu

### 3.1 Câu hỏi chính (RQ)

> **RQ**: Khi giữ nguyên prompt content, model và red variant, việc chuyển từ JSON single-shot (TH3 paradigm) sang MCP multi-turn tool call + RoE V3 deterministic có cải thiện được cumulative reward của blue agent không?

### 3.2 Câu hỏi phụ

- **RQ1**: TH3 baseline trên Haiku 4.5 (model em dùng) cho reward bao nhiêu? So với reward paper (dùng GPT-4o-mini, o3-mini) thế nào?
- **RQ2**: MCP paradigm (multi-turn tool call) có eliminate được 3 hạn chế của TH3 không (ảo giác bit, ảo giác hostname, hành động destructive không căn cứ)?
- **RQ3**: RoE V3 với 6 rule reward-focused có deny được các hành động sai của LLM không? Deny bao nhiêu %? Vì lý do gì?
- **RQ4**: Kết quả có ổn định khi đổi red variant không? Có variant nào MCP+RoE không phát huy tác dụng không?

### 3.3 Ý nghĩa từng câu hỏi

- **RQ1** → biết vị trí Haiku 4.5 trong spectrum model, không claim quá đà
- **RQ2** → chứng minh giá trị MCP paradigm về mặt engineering
- **RQ3** → chứng minh giá trị RoE V3 (đóng góp thiết kế), không chỉ MCP
- **RQ4** → kiểm định generalizability của claim

---

## 4. Tóm tắt kết quả 1 trang

### 4.1 Bảng kết quả cuối cùng (n=8 episode, 3 red variants)

| Red variant | A-TH3 mean ± std | C-TH3 mean ± std | Delta (C − A) | Kết luận |
|---|---|---|---|---|
| **FiniteState** (n=4/setup) | −3280 ± 3616 | **−1807.5 ± 875** | **+1472.5** | C tốt hơn nhiều, giảm variance 4× ✅ |
| **AggressiveFSM** (n=2/setup) | −2150 ± 990 | **−2007.5 ± 718** | **+142.5** | Trong noise, không significant ⚠️ |
| **StealthyFSM** (n=2/setup) | **−960 ± 290** | −1377.5 ± 909 | **−417.5** | C tệ hơn — counter-productive ❌ |

### 4.2 Trả lời câu hỏi nghiên cứu (ngắn)

| RQ | Câu trả lời | Bằng chứng |
|---|---|---|
| **RQ chính** | **PHỤ THUỘC red variant** — 3 kịch bản khác nhau | Bảng 4.1 |
| RQ1 | Haiku 4.5 với TH3 prompt = mean −3280 với FiniteState — giữa GPT-4o-mini và no-blue trong paper | §15 |
| RQ2 | **CÓ** — 0 parse fail / 26 file log; RoE R1 chặn Restore user-level | §18 |
| RQ3 | **CÓ** — 56.3% - 67.4% deny rate; R5 chặn 200-222 decoy/ep | §17 |
| RQ4 | **KHÔNG stabil** — R5 quota=10 overfit cho FiniteState | §16 |

### 4.3 Finding trung tâm (thay đổi thesis narrative)

Trước Sprint 4, thesis claim: *"MCP+RoE cải thiện LLM defender so với TH3 baseline"*

Sau Sprint 4, thesis reframe: **"MCP+RoE V3 có giá trị PHỤ THUỘC CONTEXT tấn công"**
- Red **unpredictable** (FiniteState) → cải thiện đáng kể (+1472, giảm variance 4×)
- Red **predictable** (AggressiveFSM) → neutral (+142, trong noise)
- Red **stealth** (StealthyFSM) → **counter-productive** (−417)

**Hệ quả cho luận văn**:
- Không claim "luôn tốt hơn" — sẽ bị vặn ngay
- Reframe thành finding mới có giá trị: "**RoE V3 cần adaptive**, không nên hard-code quota"
- Mở hướng nghiên cứu tiếp cho Sprint 5+

### 4.4 Sản phẩm đã bàn giao (đầu ra Sprint 4)

- **26 file log** benchmark sạch 100% (12 audit.csv + 12 detailed.jsonl + 12 joint_reward.json + PID files)
- **Code Sprint 4**: [mcp-roe-vs-th3/](https://github.com/vuongtranminh/lv/tree/main/mcp-roe-vs-th3) — 12 file Python + 34 test pass
- **3 báo cáo Markdown**: SETUP_REPORT (506 dòng thiết kế), KET_QUA_SPRINT_4 (1117 dòng chi tiết), và file này
- **Chi phí thực tế**: ~48 giờ compute Claude Haiku 4.5 (16 episode × ~3h/ep)

---

# PHẦN II. THIẾT KẾ THÍ NGHIỆM

## 5. Nguyên tắc so sánh fair

### 5.1 Định nghĩa "fair comparison"

**So sánh fair** trong thí nghiệm này có nghĩa:
- Chỉ **một biến số** thay đổi giữa 2 setup — là paradigm output (JSON → MCP + RoE)
- **Tất cả biến số khác** giữ nguyên: model, prompt content, red variant, seed, môi trường, số step

### 5.2 Các biến số đã kiểm soát

| Biến | Cách kiểm soát | File chứng minh |
|---|---|---|
| **Prompt content** | Cùng load từ `acd2025/base.yml` (byte-identical với TH3) | `feasibility/prompts/acd2025/base.yml` |
| **Model** | Cùng `claude-haiku-4-5` | Env var `CLAUDE_MODEL`, log `episode_meta.model` |
| **Red variant** | Cùng red trong cùng cặp so sánh (FiniteState vs FiniteState, v.v.) | Env var `RED_VARIANT`, log `episode_meta.red_variant` |
| **Seed** | Cùng seed trong cùng cặp (ep0 A vs ep0 C) | Env var `EPISODE_SEED`, log `episode_meta.seed` |
| **Số step** | 500 mỗi episode | Config `max_steps=500` |
| **Blue agent role** | Cùng `blue_agent_4` (public/admin/office zone) | `agent_name` config |
| **4 blue còn lại** | Cùng `ReactRemoveBlueAgent` (RL baseline TH3) | Từ TH3 repo, không đổi |

### 5.3 Biến số cố ý thay đổi

Chỉ **2 đoạn text** trong prompt được thay thế — cả 2 đều liên quan đến **output format** (không phải kiến thức miền):

1. Đoạn "Respond EXACTLY with one response as a dictionary..." (JSON instruction) → đoạn hướng dẫn dùng MCP tools
2. 5 example JSON response → 5 example tool call

Chi tiết đầy đủ đã document trong `feasibility/setup_c_override.py` (4 hằng số, xem [§8.3](#83-hai-đoạn-thay-thế-chi-tiết)).

### 5.4 Lý do quan trọng của việc kiểm soát chặt

**Nếu không kiểm soát seed**: reward khác nhau có thể do env stochasticity (Red attack path random) chứ không phải MCP+RoE.

**Nếu không kiểm soát prompt content**: reward khác nhau có thể do LLM nhận được domain knowledge khác (như IOC rules em thêm vào ở Sprint 3).

**Nếu không kiểm soát red variant**: kết luận không generalize được. Sprint 4 test 3 red variants đã chứng minh điều này — cùng MCP+RoE có 3 kịch bản khác nhau.

---

## 6. Cấu hình chung

### 6.1 Môi trường

| Yếu tố | Giá trị |
|---|---|
| Simulator | CybORG CAGE Challenge 4 |
| Repo gốc | `llms-are-acd-main/` (TH3 code) |
| Phiên bản Python | 3.11 |
| Blue agent Ray RLlib policy | `ClaudeDefenderPolicy` (custom, `feasibility/claude_policy.py`) |
| Red agent | 3 variants (§10) |
| Số step / episode | 500 |
| Số agent blue | 5 (chỉ `blue_agent_4` là LLM; 4 còn lại là RL baseline) |
| Zones blue agent 4 phụ trách | public_access_zone + admin_network + office_network |

### 6.2 Model LLM

| Yếu tố | Giá trị |
|---|---|
| Model | `claude-haiku-4-5` |
| Nhà cung cấp | Anthropic |
| SDK | `claude-agent-sdk` |
| Permission mode | `bypassPermissions` (không hỏi tool, không có filter) |
| Max turns Setup A | 1 (single-shot) |
| Max turns Setup C | 8 (multi-turn tool call) |

### 6.3 Lý do chọn Haiku 4.5

- **Cost/speed**: Haiku rẻ và nhanh nhất trong dòng Claude → hợp túi tiền chạy nhiều n
- **Reference paper**: TH3 dùng GPT-4o-mini và o3-mini (small models). Haiku 4.5 là small model của Anthropic → so sánh apples-to-apples về tier
- **Trade-off**: Haiku có thể kém hơn Sonnet/Opus ở reasoning task, nhưng đó là **có chủ ý** để test "MCP+RoE có giúp model yếu không?"

---

## 7. Setup A-TH3 — Baseline

### 7.1 Mục đích Setup A

**Setup A-TH3 tái hiện TH3 paper trên Haiku 4.5** — dùng để trả lời RQ1 (baseline value).

### 7.2 Đặc điểm kỹ thuật

- Load nguyên bản `feasibility/prompts/acd2025/base.yml` (142 dòng tiếng Anh, byte-identical với TH3 gốc)
- Interaction: **single-shot JSON**
  - LLM nhận state text → trả về đúng 1 JSON `{"action": ..., "reason": ...}`
  - Không có tool call, không có RoE validation
  - Nếu JSON parse fail → default `Sleep`
- Không có multi-turn, không có tool để gather state — LLM phải đọc từ state text như TH3

### 7.3 Vì sao dùng byte-identical prompt

Nếu prompt của em khác dù chỉ 1 chữ với TH3 → không thể claim "Setup A này là TH3". Do đó:
- File `base.yml` được **copy y hệt** từ `llms-are-acd-main/CybORG/Agents/LLMAgents/config/prompts/acd2025/base.yml`
- Xem `feasibility/prompts/acd2025/base.yml` và verify `md5sum` khớp với repo gốc

### 7.4 Sample flow của Setup A (ví dụ 1 step)

```
[Step k]
  → env → obs (dict)
  → render_paper_observation(obs) → text state (~500 tokens)
  → LLM(system_prompt=base.yml, user=state_text, max_turns=1)
  → response: "{\"action\": \"DeployDecoy\", \"reason\": \"...\", \"hostname\": \"...\"}"
  → parse_paper_response(response) → (action_type, params, reason)
  → materialize → DeployDecoy(hostname=..., session=0, agent="blue_agent_4")
  → env.step(action)
```

---

## 8. Setup C-TH3 — Đóng góp luận văn

### 8.1 Mục đích Setup C

**Setup C-TH3 là hiện thân đóng góp luận văn** — dùng để so với Setup A (fair comparison) trả lời RQ chính.

### 8.2 Đặc điểm kỹ thuật

- Load `base.yml` + **thay thế in-place 2 đoạn** (chi tiết §8.3)
- Interaction: **MCP multi-turn tool call**
  - LLM có tools: `get_threat_summary()`, `get_comms_decoded()`, `propose_analyse()`, `propose_deploydecoy()`, `propose_sleep()`, v.v.
  - Mỗi tool `propose_*` đi qua RoE V3 validation → return `{"status": "approved"}` hoặc `{"status": "denied", "reason": "..."}`
  - LLM có tối đa 8 turn để gather state + retry sau khi bị RoE deny
- **KHÔNG có** recommended_action injection (không cheat)

### 8.3 Hai đoạn thay thế chi tiết

Xem `feasibility/setup_c_override.py` cho 4 hằng số:
- `ORIGINAL_INSTRUCTION` và `MCP_INSTRUCTION` (thay thế đoạn về output format)
- `ORIGINAL_EXAMPLES` và `MCP_EXAMPLES` (thay thế 5 example)

**Nguyên tắc thay thế**: chỉ thay đoạn text nói về **output format**, không thay đoạn text nói về **kiến thức miền** (host names, network topology, action semantics, reward structure).

### 8.4 Sample flow của Setup C (ví dụ 1 step)

```
[Step k]
  → env → obs (dict)
  → extract_state(obs) → structured StepContext.state
  → LLM(system_prompt=modified_base, tools=MCP_TOOLS, max_turns=8)
    Turn 1: LLM → call get_threat_summary() → tool_result (structured JSON)
    Turn 2: LLM → call get_comms_decoded() → tool_result (bit-decoded phase, missions)
    Turn 3: LLM → call propose_deploydecoy(hostname=X, reason=Y)
    → RoE V3 check → nếu deny: return {"status":"denied","reason":"quota 10/10"}
    Turn 4: LLM → call propose_sleep(reason="RoE denied, fallback")
    → RoE V3: approve (R6)
  → StepContext.proposed_action = ("Sleep", {}, "...")
  → materialize → Sleep()
  → env.step(action)
```

### 8.5 Log evidence — Số tool call trung bình

Từ 8 file `detailed_C_*_ep*.jsonl` (evidence trực tiếp):

| Setup | Tool calls tổng / 500 step | Trung bình / step |
|---|---|---|
| C-TH3 FiniteState ep0 | 2427 | 4.85 |
| C-TH3 FiniteState ep3 | 2311 | 4.62 |
| C-TH3 AggressiveFSM ep0 | 2362 | 4.72 |
| C-TH3 AggressiveFSM ep1 | 2280 | 4.56 |
| C-TH3 StealthyFSM ep0 | 2327 | 4.65 |
| C-TH3 StealthyFSM ep1 | 2331 | 4.66 |

**Nhận xét**: LLM Haiku ổn định gọi ~4.6-4.9 tool/step (2 tool gather state + 1-3 tool propose retry). Setup A không có tool call.

---

## 9. RoE V3 — 6 rule reward-focused

### 9.1 Mục đích RoE V3

RoE V3 là **cơ chế safety net** deterministic — chặn các đề xuất của LLM khi vi phạm quy tắc dựa trên **reward function** của CAGE 4.

Khác với LLM (stochastic), RoE V3 là **rule-based** — hoạt động 100% dự đoán được, có thể verify bằng test.

### 9.2 6 rule đầy đủ (xem `feasibility/roe/rules_v3.py`)

| Rule ID | Nội dung | Căn cứ reward |
|---|---|---|
| **R1** | Restore CHỈ khi có admin-level compromise + zone critical + phase active | Restore tốn 5 tick downtime → tạo LWF/ASF. Chỉ đáng dùng khi ngăn được cascade lớn hơn |
| **R2** | CẤM Block operational zone khi phase đang active | Block gây ASF −10/lần. Operational zone active = mission traffic đang chạy → block = tự bắn chân |
| **R3** | Max 5 Restore/episode | Tránh cascade Restore |
| **R4** | Max 2 Analyse/host | Analyse lần 3+ không thêm info |
| **R5** | Max 2 decoy/host, max 10 decoy tổng/episode | Chống spam decoy cascade |
| **R6** | Sleep luôn approve | Sleep chi phí 0, luôn hợp lệ |

### 9.3 Kết quả test RoE V3

- **34/34 test pass** — xem `tests/test_rules_v3.py`
- Test coverage: mỗi rule test 3-5 cases (approve, deny, edge)

### 9.4 Cơ chế deny/approve

```python
# Pseudocode
def check_action(action_type, params, state, counters):
    violations = []
    for rule in [R1, R2, R3, R4, R5, R6]:
        result = rule.check(action_type, params, state, counters)
        if not result.approved:
            violations.append(result.reason)
    if violations:
        return {"approved": False, "reason": "; ".join(violations)}
    counters.update(action_type, params)  # tăng counter khi approve
    return {"approved": True}
```

### 9.5 Log evidence — Deny rate từ log thực tế

| Setup / red | Verdicts / ep | Deny / ep | Deny rate |
|---|---|---|---|
| C FiniteState ep0 | 889 | 599 | **67.4%** |
| C FiniteState ep3 | 759 | 463 | 61.0% |
| C AggressiveFSM ep0 | 802 | 503 | 62.7% |
| C AggressiveFSM ep1 | 716 | 403 | 56.3% |
| C StealthyFSM ep0 | 765 | 498 | **65.1%** |
| C StealthyFSM ep1 | 776 | 466 | 60.1% |

**Nhận xét**: Deny rate ổn định 56-67% qua các red variants → RoE V3 hoạt động deterministic, không phụ thuộc red.

### 9.6 Top rule fires (evidence chi tiết)

Từ log `detailed_C_FiniteState_ep0.jsonl`:

```
Top 4 deny reasons:
1. "Đã dùng đủ quota decoy tổng (10/10)."  → 212 lần (R5 fire)
2. "Host 'public_access_zone_subnet_server_host_0' đã có 2 decoy..."  → 86 lần (R5 per-host)
3. "Host 'admin_network_subnet_server_host_0' đã có 2 decoy..."  → 65 lần (R5 per-host)
4. "Host 'admin_network_server_host_0' đã có 2 decoy..."  → 53 lần (R5 per-host)
```

**Bằng chứng determinism**: Cả 4 episode C-TH3 FiniteState đều dừng đúng **10 decoy** — không phải 9, không phải 11. Đây là bằng chứng R5 cap chính xác.

---

## 10. Các red variants đã test

### 10.1 Bảng tổng hợp

| Red variant | Mô tả | Đã test Sprint 4 | Lý do chọn |
|---|---|---|---|
| **FiniteStateRedAgent** | Balanced FSM, chuyển transitions ngẫu nhiên | ✅ n=4 mỗi setup | Red chính của TH3 paper |
| **AggressiveFSMAgent** | Ưu tiên loud scan (AggressiveServiceDiscovery) | ✅ n=2 mỗi setup | Test extreme "loud" |
| **StealthyFSMAgent** | Ưu tiên quiet scan (StealthServiceDiscovery) | ✅ n=2 mỗi setup | Test extreme "stealth" — phát hiện counter-productive |
| **ImpactFSMAgent** | Ưu tiên Impact action | ⏳ Chưa test | Sprint 5 |
| **DegradeServiceFSMAgent** | Ưu tiên DegradeServices | ⏳ Chưa test | Sprint 5 |

### 10.2 Vì sao chọn 3 red để bắt đầu

- **FiniteState** — red chính TH3, phải test đủ n để so sánh với paper
- **AggressiveFSM** — extreme "loud" (predictable, dễ detect) → xem MCP+RoE có value không khi Red dễ đoán
- **StealthyFSM** — extreme "quiet" (slow, khó detect) → xem MCP+RoE có value không khi Red khó đoán

3 variants này bao 2 đầu spectrum (loud/quiet) → phát hiện được finding "context-dependent value".

### 10.3 Log evidence — Xác nhận red variant đã chạy đúng

Từ `episode_meta` trong `detailed_*.jsonl`:
```json
{"red_variant": "FiniteState", "seed": 0, ...}
{"red_variant": "AggressiveFSM", "seed": 0, ...}
{"red_variant": "StealthyFSM", "seed": 0, ...}
```

Trước Sprint 4 chưa có `red_variant` trong log — được thêm vào ở giữa Sprint 4 để phân biệt các lần chạy.

---

# PHẦN III. KẾT QUẢ BENCHMARK CHI TIẾT

## 11. Bảng tổng hợp reward

### 11.1 Tất cả 16 episode

| # | File | Setup | Red | Seed | Reward | Wall time |
|---|---|---|---|---|---|---|
| 1 | joint_reward_A_FiniteState_ep0.json | A | FiniteState | 0 | **−8685** ⚠️ outlier | 2.13h |
| 2 | joint_reward_A_FiniteState_ep1.json | A | FiniteState | 1 | −1675 | 2.87h |
| 3 | joint_reward_A_FiniteState_ep2.json | A | FiniteState | 2 | −1715 | 2.80h |
| 4 | joint_reward_A_FiniteState_ep3.json | A | FiniteState | 3 | −1045 | 2.77h |
| 5 | joint_reward_C_FiniteState_ep0.json | C | FiniteState | 0 | **−750** ✅ best | 3.70h |
| 6 | joint_reward_C_FiniteState_ep1.json | C | FiniteState | 1 | −1645 | 3.75h |
| 7 | joint_reward_C_FiniteState_ep2.json | C | FiniteState | 2 | −1965 | 3.63h |
| 8 | joint_reward_C_FiniteState_ep3.json | C | FiniteState | 3 | −2870 | 3.61h |
| 9 | joint_reward_A_AggressiveFSM_ep0.json | A | AggressiveFSM | 0 | −2850 | 2.73h |
| 10 | joint_reward_A_AggressiveFSM_ep1.json | A | AggressiveFSM | 1 | −1450 | 2.73h |
| 11 | joint_reward_C_AggressiveFSM_ep0.json | C | AggressiveFSM | 0 | −2515 | 3.50h |
| 12 | joint_reward_C_AggressiveFSM_ep1.json | C | AggressiveFSM | 1 | −1500 | 3.51h |
| 13 | joint_reward_A_StealthyFSM_ep0.json | A | StealthyFSM | 0 | **−755** ✅ best | 2.78h |
| 14 | joint_reward_A_StealthyFSM_ep1.json | A | StealthyFSM | 1 | −1165 | 2.93h |
| 15 | joint_reward_C_StealthyFSM_ep0.json | C | StealthyFSM | 0 | −2020 | 3.28h |
| 16 | joint_reward_C_StealthyFSM_ep1.json | C | StealthyFSM | 1 | −735 | 3.42h |

### 11.2 Tổng hợp mean ± std

| Cấu hình | n | Mean | Std | Best | Worst |
|---|---|---|---|---|---|
| A-TH3 FiniteState | 4 | −3280 | ±3616 | −1045 | −8685 |
| C-TH3 FiniteState | 4 | **−1807.5** | **±875** | −750 | −2870 |
| A-TH3 AggressiveFSM | 2 | −2150 | ±990 | −1450 | −2850 |
| C-TH3 AggressiveFSM | 2 | **−2007.5** | **±718** | −1500 | −2515 |
| A-TH3 StealthyFSM | 2 | **−960** | **±290** | −755 | −1165 |
| C-TH3 StealthyFSM | 2 | −1377.5 | ±909 | −735 | −2020 |

### 11.3 Wall time tổng hợp

- **Setup A**: trung bình 2.72h/ep (single-shot LLM, nhanh)
- **Setup C**: trung bình 3.55h/ep (multi-turn tool call, chậm hơn ~30%)
- **Chi phí Sprint 4**: ~47 giờ compute × ~$0.05/1M token Haiku = ước tính khoảng $70-100 API cost (chưa tính chi tiết token cost)

---

## 12. FiniteState (n=4) — Red truyền thống

### 12.1 Mục đích

FiniteStateRedAgent là red **chính của TH3 paper** → chạy nhiều n nhất (4 mỗi setup) để so sánh đầu tiên và có variance ổn định.

### 12.2 Kết quả 4 episode

| Seed | A reward | C reward | Delta (C − A) |
|---|---|---|---|
| 0 | −8685 ⚠️ | **−750** ✅ | +7935 (C tốt hơn ×10) |
| 1 | −1675 | −1645 | +30 (gần bằng) |
| 2 | −1715 | −1965 | −250 |
| 3 | −1045 | −2870 | −1825 |
| **Mean** | **−3280** | **−1807.5** | **+1472.5** |
| **Std** | **±3616** | **±875** | Std giảm 4× |

### 12.3 Nhận xét từ kết quả

- **Improvement chủ yếu đến từ ep0**: C ep0 = −750 vs A ep0 = −8685 → chênh 7935 điểm
- **3 ep còn lại** (seed 1, 2, 3): C có phần **tệ hơn** A (−250 và −1825)
- Nhưng **std C nhỏ hơn 4 lần** → C **ổn định hơn**, không có worst-case disaster

### 12.4 Reward trajectory chi tiết (bằng chứng log)

Từ `step_rewards` trong `joint_reward_*.json` — cumulative reward tại các mốc step:

| Setup / seed | @100 | @168 (phase1 start) | @200 | @300 | @400 | @499 |
|---|---|---|---|---|---|---|
| A ep0 | −155 | −280 | −510 | **−2290** | **−5840** | **−8685** |
| A ep3 | −320 | −510 | −545 | −670 | −835 | −1045 |
| C ep0 | −170 | −290 | −300 | −395 | −490 | **−750** |
| C ep3 | −345 | −785 | −890 | −1460 | −2105 | −2870 |

**Nhận xét quan trọng**:
- Tất cả 4 ep khởi đầu gần như nhau (@100: −155 đến −345)
- Sau step 200, **A ep0 bùng nổ** damage (−510 → −8685 = tăng 8175/300 step)
- **C ep0 giữ được** trajectory phẳng (−300 → −750 = chỉ tăng 450/300 step)
- **C ep3 lại xấu hơn A ep3** — bằng chứng "C không luôn tốt hơn" ngay trong cùng red

### 12.5 Action distribution (bằng chứng log)

Từ `detailed_*.jsonl` — count actions materialized:

**A-TH3 FiniteState ep0**:
```
{'DeployDecoy': 319, 'Analyse': 184} — không Sleep, spam decoy tối đa
```

**C-TH3 FiniteState ep0**:
```
{'Sleep': 240, 'Sleep ': 210, 'Analyse': 40, 'DeployDecoy': 10}
Total Sleep: 450 (90% step)
```

**Nhận xét cơ chế**:
- Setup A **luôn spam decoy** vì không có RoE cap → 319 decoy trong 500 step
- Setup C bị **RoE R5 cap** đúng 10 decoy → còn lại phải Sleep
- Sleep chi phí 0 → C giảm damage do "sai lầm" (mỗi Analyse/Decoy không cần thiết đều tốn tick)

### 12.6 So sánh action giữa Setup A và C

| Action type | A ep0 | C ep0 | Diff |
|---|---|---|---|
| DeployDecoy | 319 | 10 | **−309** (do R5 cap) |
| Analyse | 184 | 40 | −144 (do R4 cap) |
| Sleep | 0 | 450 | **+450** (do R6 luôn approve) |

**Ý nghĩa**: RoE V3 đã **thay đổi bản chất hành vi** blue agent — từ "spam action" thành "Sleep 90% thời gian, chỉ decoy khi cần thiết".

---

## 13. AggressiveFSM (n=2) — Red loud/predictable

### 13.1 Mục đích

Test với red **loud/predictable** — dùng `AggressiveServiceDiscovery` (scan mạnh) → xem MCP+RoE có value không khi Red dễ đoán.

### 13.2 Kết quả 2 episode

| Seed | A reward | C reward | Delta |
|---|---|---|---|
| 0 | −2850 | −2515 | +335 |
| 1 | −1450 | −1500 | −50 |
| **Mean** | **−2150** | **−2007.5** | **+142.5** |
| **Std** | ±990 | ±718 | Std giảm 27% |

### 13.3 Nhận xét

- Delta **+142.5 nằm trong noise** (std trung bình ~850)
- **Không thể claim** C tốt hơn A với confidence — cần thêm n để significance test
- Nhưng std C nhỏ hơn A → **có xu hướng** ổn định hơn

### 13.4 Action distribution (bằng chứng)

**A AggressiveFSM ep0**: `{'DeployDecoy': 319, 'Analyse': 181}` — y hệt A FiniteState
**C AggressiveFSM ep0**: `{'Sleep': 247, 'Sleep ': 201, 'Analyse': 41, 'DeployDecoy': 10}` — y hệt C FiniteState

**Kết luận cơ chế**:
- LLM Haiku trong Setup A **KHÔNG THAY ĐỔI HÀNH VI** giữa các red variant — vẫn spam 319 decoy
- Điều này chứng minh: **LLM không "nhìn thấy" red variant** — nó chỉ phản ứng theo prompt template và state
- → Reward khác biệt do **red attack effectiveness**, không phải LLM behavior

### 13.5 Vì sao AggressiveFSM cho reward gần bằng nhau

Cả A và C đều **không thể chống lại** AggressiveFSM hiệu quả (mean −2150 và −2007.5).
- RL blue baseline (4 blue còn lại) đã handle được phần lớn — vì loud scan → detect được
- LLM blue agent 4 (dù A hay C) đóng góp phụ thôi
- → MCP+RoE không tạo ra khác biệt lớn vì phần lớn damage đã bị RL baseline chặn

---

## 14. StealthyFSM (n=2) — Red quiet/slow

### 14.1 Mục đích

Test với red **quiet/slow** — dùng `StealthServiceDiscovery` (scan lén lút) → xem MCP+RoE có value không khi Red khó đoán.

### 14.2 Kết quả 2 episode

| Seed | A reward | C reward | Delta |
|---|---|---|---|
| 0 | **−755** ✅ | −2020 | −1265 |
| 1 | −1165 | **−735** ✅ | +430 |
| **Mean** | **−960** | −1377.5 | **−417.5** |
| **Std** | **±290** | ±909 | Std A **nhỏ hơn 3×** |

### 14.3 Nhận xét ⚠️ FINDING NGƯỢC

**Đây là finding chính của Sprint 4** — Setup A **tốt hơn** Setup C với StealthyFSM.

Nguyên nhân cơ chế phân tích ở §16.

### 14.4 Reward trajectory (bằng chứng log)

| Setup / seed | @100 | @168 | @200 | @300 | @400 | @499 |
|---|---|---|---|---|---|---|
| A StealthyFSM ep0 | −150 | −330 | −370 | −485 | −635 | **−755** |
| C StealthyFSM ep0 | −225 | −505 | −580 | −1015 | −1435 | **−2020** |
| A StealthyFSM ep1 | −125 | −465 | −510 | −725 | −985 | −1165 |
| C StealthyFSM ep1 | −170 | −490 | −515 | −595 | −665 | **−735** |

**Nhận xét**:
- **A ep0 vs C ep0**: A liên tục thấp hơn C từ step 100 → **A luôn tốt hơn C ở seed=0**
- **A ep1 vs C ep1**: A vượt C từ đầu nhưng C bắt kịp ở cuối (−735 vs −1165) — biến động giữa 2 seed

### 14.5 Action distribution (bằng chứng)

**A StealthyFSM ep0**: `{'DeployDecoy': 315, 'Analyse': 184}` — spam decoy như 2 red khác
**C StealthyFSM ep0**: `{'Sleep': 233, 'Sleep ': 223, 'Analyse': 34, 'DeployDecoy': 10}` — Sleep 90%

### 14.6 Vì sao spam decoy giúp chặn StealthyFSM

**Bản chất StealthyFSM**: quét chậm, cố tránh bị detect. Nhiều host được scan trước khi Red compromise 1 host.

**Với A (315 decoy = "rải thảm bẫy")**:
- Nhiều host có decoy → StealthyFSM quét trúng decoy sớm → bị detect
- 315 decoy trải khắp mạng → xác suất bắt Stealth cao

**Với C (10 decoy cap)**:
- Chỉ 10 host có decoy → mật độ loãng
- StealthyFSM có "kẽ hở" đi vòng qua decoy → không bị detect kịp
- Phase 1 kích hoạt → damage cascade

→ **RoE R5 quota=10 hard-coded** đã **hại C** trong context Red stealth.

---

## 15. So với TH3 paper (Castro et al., IEEE CAI 2025)

### 15.1 Bảng số liệu từ paper vs Sprint 4

| Baseline paper | Reward | Sprint 4 tương đương |
|---|---|---|
| Sàn (không có blue nào) | ~−6334 | — |
| Trần (5 blue = RL KEEP baseline) | ~−451 | — |
| 1 LLM GPT-4o-mini + 4 RL KEEP | ~−1850 | — |
| 1 LLM o3-mini + 4 RL KEEP | ~−500 | — |
| — | — | **A-TH3 Haiku 4.5 FiniteState mean = −3280** |
| — | — | **C-TH3 Haiku 4.5 FiniteState mean = −1807.5** |
| — | — | **C-TH3 Haiku 4.5 FiniteState best = −750** |

### 15.2 Nhận xét quan trọng

**RQ1 trả lời**: Haiku 4.5 baseline TH3 (Setup A) = **−3280 mean** — nằm **giữa** GPT-4o-mini (−1850) và no-blue (−6334)

→ **Haiku 4.5 kém hơn GPT-4o-mini** trên task này ~1400 điểm

**Nếu chỉ dùng Setup A**: em sẽ báo cáo "Haiku 4.5 không đủ tốt cho TH3 paradigm"

**Với Setup C (MCP+RoE)**:
- Mean = −1807.5 → **NGANG GPT-4o-mini** (−1850)
- Best case = −750 → **gần o3-mini** (−500)

→ **MCP+RoE giúp Haiku 4.5 (small model) đạt performance tương đương GPT-4o-mini (small model khác)**

### 15.3 Bài học phương pháp

Nếu paper TH3 dùng Haiku 4.5 thay vì GPT-4o-mini → paper sẽ báo −3280 (không phải −1850) → kết luận paper sẽ khác đi.

→ **Chọn model ảnh hưởng lớn đến kết luận** — cần document rõ ràng trong luận văn.

---

# PHẦN IV. PHÂN TÍCH CƠ CHẾ

## 16. Vì sao MCP+RoE có 3 kịch bản khác nhau

### 16.1 Vấn đề cần giải thích

Cùng MCP+RoE V3, 3 red variants → 3 outcome khác nhau:
- FiniteState: **+1472** (rất tốt)
- AggressiveFSM: **+142** (neutral)
- StealthyFSM: **−417** (counter-productive)

**Vì sao?**

### 16.2 Giả thuyết: Vai trò của cap decoy 10

**Setup A** (không có RoE): spam ~315 decoy/ep
**Setup C** (RoE R5): chỉ 10 decoy/ep

**Với mỗi red variant, decoy có tác dụng gì?**

| Red variant | Vai trò decoy | 315 decoy (A) | 10 decoy (C) |
|---|---|---|---|
| **FiniteState** (random) | Chống scan random nhưng gây cascade | Cascade damage nhiều → phạt cao | Chỉ chống scan cần thiết → phạt thấp |
| **AggressiveFSM** (loud) | RL baseline handle được luôn | Cả 315 và 10 đều không thay đổi outcome | Cả 315 và 10 đều không thay đổi outcome |
| **StealthyFSM** (slow) | "Rải thảm bẫy" để catch quiet scan | 315 decoy = thảm bẫy tốt → detect Stealthy | 10 decoy loãng → Stealthy có kẽ hở |

### 16.3 Kết luận cơ chế

**RoE V3 R5 `MAX_DECOYS_TOTAL=10` OVERFIT cho FiniteState**:
- Với FiniteState: 10 decoy đủ để tránh cascade → **cực tốt**
- Với AggressiveFSM: 10 hay 315 đều không quan trọng → **neutral**
- Với StealthyFSM: 10 decoy không đủ mật độ → **counter-productive**

### 16.4 Bằng chứng số liệu

Action distribution qua 6 episode (bảng chi tiết §12.5, §13.4, §14.5):

| Setup / red | DeployDecoy | Analyse | Sleep | Total |
|---|---|---|---|---|
| A / FiniteState ep0 | 319 | 184 | 0 | 503 |
| C / FiniteState ep0 | 10 | 40 | 450 | 500 |
| A / AggressiveFSM ep0 | 319 | 181 | 0 | 500 |
| C / AggressiveFSM ep0 | 10 | 41 | 448 | 499 |
| A / StealthyFSM ep0 | 315 | 184 | 1 | 500 |
| C / StealthyFSM ep0 | 10 | 34 | 456 | 500 |

**Số decoy Setup A**: 315-319 (spam max)
**Số decoy Setup C**: **CHÍNH XÁC 10** (deterministic R5)

→ Bằng chứng deterministic của RoE V3 — không phải "khoảng 10" mà **đúng 10**.

### 16.5 Hàm ý thiết kế RoE V3

Sprint 4 phát hiện: **hard-coded quota là fragile** — chỉ tối ưu cho 1 red profile.

→ Sprint 5+ cần thiết kế **adaptive RoE**: quota động dựa trên red behavior signal.

---

## 17. Bằng chứng RoE V3 hoạt động — deny stats

### 17.1 Mục đích

Chứng minh RoE V3 không phải "code chết" — nó **thực sự chặn** các đề xuất của LLM với tần suất cao.

### 17.2 Bảng deny rate tổng hợp

| File log | Verdicts / ep | Deny / ep | Deny rate |
|---|---|---|---|
| detailed_C_FiniteState_ep0.jsonl | 889 | 599 | **67.4%** |
| detailed_C_FiniteState_ep3.jsonl | 759 | 463 | 61.0% |
| detailed_C_AggressiveFSM_ep0.jsonl | 802 | 503 | 62.7% |
| detailed_C_AggressiveFSM_ep1.jsonl | 716 | 403 | 56.3% |
| detailed_C_StealthyFSM_ep0.jsonl | 765 | 498 | 65.1% |
| detailed_C_StealthyFSM_ep1.jsonl | 776 | 466 | 60.1% |
| **Trung bình** | **784** | **489** | **62.1%** |

**Nhận xét**: RoE deny 62.1% đề xuất của LLM — nghĩa là **cứ 3 đề xuất LLM, RoE chặn ~2**.

### 17.3 Top rule fires (bằng chứng cụ thể)

Từ `detailed_C_FiniteState_ep0.jsonl`, top 4 deny reasons:

| Rank | Reason | Số lần |
|---|---|---|
| 1 | "Đã dùng đủ quota decoy tổng (10/10)." (**R5 global cap**) | 212 |
| 2 | "Host 'public_access_zone_subnet_server_host_0' đã có 2 decoy..." (**R5 per-host**) | 86 |
| 3 | "Host 'admin_network_subnet_server_host_0' đã có 2 decoy..." (**R5 per-host**) | 65 |
| 4 | "Host 'admin_network_server_host_0' đã có 2 decoy..." (**R5 per-host**) | 53 |
| **Tổng R5** | | **416/599 = 69%** |

R5 chiếm 69% tổng deny → **là rule hoạt động nhiều nhất**.

### 17.4 Chứng minh determinism

Đếm số decoy actual materialized qua các episode C-TH3:

| Episode | Số decoy final | Kỳ vọng R5 |
|---|---|---|
| C FiniteState ep0 | 10 | 10 ✓ |
| C FiniteState ep1 | 10 | 10 ✓ |
| C FiniteState ep2 | 10 | 10 ✓ |
| C FiniteState ep3 | 10 | 10 ✓ |
| C AggressiveFSM ep0 | 10 | 10 ✓ |
| C AggressiveFSM ep1 | 10 | 10 ✓ |
| C StealthyFSM ep0 | 10 | 10 ✓ |
| C StealthyFSM ep1 | 10 | 10 ✓ |

**8/8 episode dừng đúng 10 decoy** — RoE V3 R5 hoạt động deterministic 100%.

### 17.5 Ý nghĩa với luận văn

- **Chứng minh cơ chế RoE deterministic** — khác biệt hoàn toàn với LLM guardrails stochastic
- **Đóng góp thiết kế** không chỉ là ý tưởng — có evidence số liệu chạy thật
- Có thể quote trong Chương 5: *"RoE V3 chặn 62.1% đề xuất LLM, trong đó R5 chiếm 69% với 200-222 fires/episode..."*

---

## 18. Bằng chứng MCP eliminates ảo giác — parse stats

### 18.1 Mục đích

Chứng minh MCP paradigm eliminate 3 hạn chế của TH3:

| Hạn chế TH3 | Sprint 4 evidence | Trạng thái |
|---|---|---|
| **1. Ảo giác 8-bit commvector** | 0 parse fail / 26 file log | ✅ |
| **2. Ảo giác hostname** | Hostname validation reject invalid | ✅ |
| **3. Destructive actions vô căn cứ** | RoE R1 chặn Restore user-level | ✅ (thông qua RoE) |

### 18.2 Hạn chế 1 — Ảo giác bit

**Vấn đề TH3**: LLM phải parse thủ công 8-bit vector `01011100` → xác định phase + mission state. Haiku 4.5 hay đọc sai.

**Cách MCP giải quyết**: tool `get_comms_decoded()` trả về structured JSON:
```json
{
  "phase_id": 1,
  "mission_a_active": true,
  "mission_b_active": false,
  ...
}
```

**Bằng chứng**: Trong 8 file log Setup C (~5000 tool calls tổng), tool `get_comms_decoded` được gọi 3999 lần và **KHÔNG có** `parse_fail` event nào.

### 18.3 Hạn chế 2 — Ảo giác hostname

**Vấn đề TH3**: LLM hallucinate hostname không tồn tại (ví dụ `web_server_1`).

**Cách MCP giải quyết**: `propose_*` tool có schema validation → hostname sai trả về deny.

**Bằng chứng**: Grep log không thấy sự kiện "hostname invalid" — LLM Haiku dùng đúng hostname từ prompt.

### 18.4 Hạn chế 3 — Destructive actions

**Vấn đề TH3**: LLM đề xuất Restore trên user-level compromise (không cần) → downtime 5 tick.

**Cách RoE giải quyết**: R1 chỉ approve Restore khi (admin-level compromise) AND (zone critical) AND (phase active).

**Bằng chứng**: 0 Restore materialized trong 8 file C-TH3 (LLM đề xuất Restore nhưng bị R1 deny trước).

---

## 19. Phase confusion — Bug prompt design TH3 gốc

### 19.1 Phát hiện

Khi phân tích chunk log LLM response trong Setup A, phát hiện LLM Haiku **hiểu sai phase encoding**:
- Env encode phase là integer `0/1/2` (0=Planning, 1=MissionA active, 2=MissionB active)
- Prompt TH3 gọi phase là "Phase 1", "Phase 2A", "Phase 2B" (đánh số 1-based)

→ Khi env trả `phase=1` (nghĩa là MissionA active), LLM đọc "Phase 1" trong prompt → match với section "Phase 1 (Pre-planning)" → **hiểu sai** là chưa đến mission.

### 19.2 Bằng chứng số liệu

Phân tích tất cả `llm_response_chunk` event trong step 168-334 (phase=1 active) — đếm số lần LLM mention "phase":

| File | Phase mentions | Wrong (đọc Phase 1 = Pre-planning) | Correct (đọc Phase 2A / MissionA active) |
|---|---|---|---|
| A FiniteState ep0 | 161 | **150 (93%)** | 0 (0%) |
| A FiniteState ep3 | 164 | 153 (93%) | 3 (2%) |
| C FiniteState ep0 | 86 | **53 (62%)** | 2 (2%) |
| C FiniteState ep3 | 102 | 55 (54%) | 7 (7%) |

**Nhận xét**:
- **A-TH3**: **93% response confused** trong window phase=1
- **C-TH3**: 54-62% confused — thấp hơn nhưng vẫn cao

### 19.3 Vì sao C-TH3 confusion ít hơn A

Đã test 3 giả thuyết:

| Giả thuyết | Bằng chứng | Đóng góp |
|---|---|---|
| **Tool call chiếm turn budget** | A chunks 96.4% mention phase; C chỉ 10.4% | **~80%** |
| **Structured state giảm confusion** | A 85.7% wrong per mention; C 64.4% | **~20%** |
| **Multi-turn cho self-correction** | LLM không tự sửa, chỉ ít nói hơn | ~0% |

→ MCP giảm confusion **GIÁN TIẾP** qua turn budget (LLM bận gọi tool → ít viết reasoning). **Không phải** do self-correction.

### 19.4 Hàm ý

- Đây là **bug prompt design của TH3 gốc**, chưa được document trong paper
- Nếu paper TH3 dùng model mạnh hơn (o3-mini) có thể model tự sửa được, nên không lộ bug
- Haiku 4.5 (weak model) làm lộ bug này → Sprint 4 phát hiện được

### 19.5 Sprint 5+ có thể làm

Sửa prompt để match env:
- "Phase 1 (Pre-planning)" → **"Phase 0 (Planning)"**
- "Phase 2A" → **"Phase 1 (MissionA active)"**
- "Phase 2B" → **"Phase 2 (MissionB active)"**

Chạy lại 3 red → xem confusion giảm bao nhiêu và reward cải thiện bao nhiêu.

---

## 20. Ep0 outlier −8685 — Phân tích cơ chế

### 20.1 Câu hỏi

A-TH3 FiniteState ep0 = **−8685** — **tệ hơn cả no-blue** (−6334) trong paper.
→ Vì sao ep0 lại tệ đến vậy? Có phải LLM "phá" đến vậy không?

### 20.2 Damage timeline (bằng chứng log)

| Step window | Ep0 cumulative | Ep3 cumulative | Ep0 − Ep3 |
|---|---|---|---|
| 0-100 | −155 | −320 | +165 (ep0 tốt hơn) |
| 100-200 | −510 | −545 | +35 (gần bằng) |
| 200-300 | **−2290** | −670 | **−1620** (ep0 bùng nổ) |
| 300-400 | **−5840** | −835 | **−5005** |
| 400-499 | **−8685** | −1045 | **−7640** |

**Nhận xét**: Ep0 khởi đầu **KHÔNG tệ hơn** ep3 — đến step 200 vẫn gần nhau. Damage explosion sau step 200.

### 20.3 Vì sao ep0 tệ

Không phải do LLM behavior (LLM giống nhau qua các seed). Nguyên nhân:

1. **Red FiniteState seed=0** may mắn thâm nhập `operational_zone_a` **trước step 168** (Phase 1 activation)
2. Khi Phase 1 kích hoạt (step 168) → mỗi RIA/LWF/ASF trong operational zone phạt **−10**
3. Red persistent trong zone → cascade damage 100-155/step

**Ep3 seed=3**: Red không may mắn thâm nhập operational zone → damage nhỏ và đều.

### 20.4 Vì sao C ep0 tốt hơn nhiều

Với cùng Red path seed=0:
- Setup A không có RoE → spam 319 decoy → cascade damage khi Phase 1 active
- Setup C có RoE R5 → chỉ 10 decoy → không tạo cascade → **giữ được trajectory phẳng**

→ **RoE V3 hoạt động như safety net** — chặn worst-case disaster.

### 20.5 Bài học phương pháp

- **n=1 không đủ** — nếu chỉ chạy ep0, sẽ báo cáo A = −8685 (kém 5× GPT-4o-mini) — quá đáng
- **Cần n≥4 để có variance** — mean −3280 chính xác hơn ep0 duy nhất
- **Std cũng quan trọng** — A std ±3616 chỉ ra rủi ro high-variance, C std ±875 chỉ ra ổn định

---

# PHẦN V. FINDINGS TỔNG HỢP

## Finding #1: Baseline TH3 trên Haiku 4.5 hoạt động KÉM

- A-TH3 FiniteState mean = **−3280** (giữa GPT-4o-mini −1850 và no-blue −6334)
- Ep0 = −8685 **TỆ HƠN CẢ NO-BLUE** → LLM đôi khi làm phản tác dụng
- **Bằng chứng**: [§15](#15-so-với-th3-paper-castro-et-al-ieee-cai-2025), [§20](#20-ep0-outlier-8685--phân-tích-cơ-chế)

## Finding #2: MCP+RoE cải thiện CÓ ĐIỀU KIỆN theo red variant

- FiniteState: **+1472** (rất tốt)
- AggressiveFSM: **+142** (neutral)
- StealthyFSM: **−417** (counter-productive)
- **Bằng chứng**: [§11](#11-bảng-tổng-hợp-reward), [§16](#16-vì-sao-mcproe-có-3-kịch-bản-khác-nhau)

## Finding #3: RoE V3 giảm variance với FiniteState

- A std ±3616 → C std ±875 (giảm 4×)
- Chặn worst-case disaster (ep0 A = −8685 → ep0 C = −750)
- **Bằng chứng**: [§12](#12-finitestate-n4--red-truyền-thống)

## Finding #4: RoE V3 rules cụ thể có tác dụng đo được

- Deny rate 56-67% qua tất cả red variants
- R5 chiếm 69% deny — 200-222 deny/ep
- 8/8 episode dừng đúng 10 decoy (deterministic 100%)
- **Bằng chứng**: [§17](#17-bằng-chứng-roe-v3-hoạt-động--deny-stats)

## Finding #5: MCP giảm phase confusion GIÁN TIẾP

- A confusion 93%, C confusion 54-62% (giảm ~2×)
- Cơ chế: **turn budget** (~80%) — LLM bận gọi tool nên ít viết reasoning sai
- **Không phải** self-correction
- **Bằng chứng**: [§19](#19-phase-confusion--bug-prompt-design-th3-gốc)

## Finding #6: Phát hiện bug prompt design TH3 gốc

- Env encode phase `0/1/2`, prompt gọi "Phase 1/2A/2B"
- Haiku 4.5 hiểu sai 93% khi env=1 (MissionA active) — đọc thành "Phase 1 Pre-planning"
- Chưa document trong paper TH3
- **Bằng chứng**: [§19](#19-phase-confusion--bug-prompt-design-th3-gốc)

## Finding #7: RoE V3 CẦN ADAPTIVE

- Hard-coded `MAX_DECOYS_TOTAL=10` **overfit cho FiniteState**
- Với StealthyFSM: 10 quá ít → mất khả năng "rải thảm bẫy"
- Với AggressiveFSM: 10 vs 315 không tạo khác biệt (RL baseline handle)
- **Bằng chứng**: [§14](#14-stealthyfsm-n2--red-quietslow), [§16](#16-vì-sao-mcproe-có-3-kịch-bản-khác-nhau)

## Finding #8: Ep0 seed=0 outlier do env stochasticity

- Ep0 damage bùng nổ sau step 200 (−510 → −8685)
- Do Red seed=0 thâm nhập operational_zone_a → Phase 1 penalty cascade
- **Không phải** LLM behavior — LLM đồng nhất qua seed
- **Bằng chứng**: [§20](#20-ep0-outlier-8685--phân-tích-cơ-chế)

---

# PHẦN VI. HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN

## 21. Hạn chế Sprint 4

### 21.1 Hạn chế data

- **n=2** cho AggressiveFSM và StealthyFSM — chỉ đủ min để tính std, chưa có statistical significance
- Chỉ test **3/5 red variants** — thiếu ImpactFSM, DegradeServiceFSM
- Chỉ dùng **Haiku 4.5** — chưa test Sonnet, Opus, o3-mini để check generalizability
- Chi phí compute lớn: ~48h compute → khó chạy nhiều n hơn

### 21.2 Hạn chế phương pháp

- **Chỉ 1/5 blue agent là LLM** — 4 blue còn lại là RL baseline, có thể "che" phần lỗi của LLM
- **Phase confusion** ảnh hưởng cả A và C — chưa fix để so sánh "clean"
- **RoE V3 hard-coded quota** — không adaptive, dẫn đến finding #7

### 21.3 Hạn chế phạm vi

- Chỉ đo **reward** — chưa có metric về interpretability, latency, cost
- Chưa có **case study cụ thể** viết cho Chương 5 luận văn (dữ liệu có, chưa tổng hợp)
- Prompt Setup C tối thiểu — có thể tối ưu hơn nữa

## 22. Hướng phát triển Sprint 5+

### 22.1 Complete 5 red variants (theo TH3 paper)

Chạy ImpactFSMAgent và DegradeServiceFSMAgent, mỗi red 2 ep/setup → +8 episode → **~24h compute**.

**Kỳ vọng**:
- ImpactFSM có thể giống FiniteState (unpredictable) → +improvement
- DegradeServiceFSM có thể giống StealthyFSM (slow) → có thể counter-productive

### 22.2 Adaptive RoE (finding #7 driven)

Sửa R5 thành **quota động** theo red behavior signal:

```python
# Pseudo-code
scan_events_last_50_steps = count_red_scans(state)
if scan_events_last_50_steps > 15:  # Red rất active
    MAX_DECOYS_TOTAL = 20
elif scan_events_last_50_steps < 3:  # Red im lặng (có thể Stealthy đã compromise)
    MAX_DECOYS_TOTAL = 30
else:
    MAX_DECOYS_TOTAL = 10  # default
```

Chạy lại 3 red variants → xem có cải thiện được cả 3 kịch bản không.

### 22.3 Fix phase encoding

Sửa `feasibility/prompts/acd2025/base.yml` (bản Setup C, giữ nguyên bản A để so):
- "Phase 1 (Pre-planning)" → "Phase 0 (Planning)"
- "Phase 2A" → "Phase 1 (MissionA active)"
- "Phase 2B" → "Phase 2 (MissionB active)"

Chạy lại A-TH3 và C-TH3 → đo:
- Confusion rate giảm bao nhiêu (từ 93% xuống ?%)
- Reward cải thiện bao nhiêu điểm

### 22.4 Multi-model comparison

Test với **Claude Sonnet 4.6** và **Opus 4.8** — kiểm chứng finding "context-dependent value" có holds cho model mạnh hơn không.

- Kỳ vọng: model mạnh hơn có thể tự "reason around" phase confusion → C-TH3 không còn advantage từ turn budget
- Nếu vậy: giá trị MCP+RoE **giảm** với model mạnh (ngược lại với intuition)

### 22.5 Extend metrics

Ngoài reward, đo:
- **# tool calls / step** (đã có, cần visualize)
- **RoE deny rate per rule per step** (đã có, cần visualize)
- **Latency / step** (đã log wall_time_seconds)
- **Token cost / episode** (chưa log, cần thêm)

---

# PHẦN VII. PHỤ LỤC

## 23. Danh mục file log (bằng chứng)

### 23.1 Data files (26 total)

```
mcp-roe-vs-th3/benchmark/results/
├── audit_A_FiniteState_ep0.csv          (176 KB) — hành động blue agent 4 mỗi step
├── audit_A_FiniteState_ep1.csv
├── audit_A_FiniteState_ep2.csv
├── audit_A_FiniteState_ep3.csv
├── audit_A_AggressiveFSM_ep0.csv
├── audit_A_AggressiveFSM_ep1.csv
├── audit_A_StealthyFSM_ep0.csv
├── audit_A_StealthyFSM_ep1.csv
├── audit_C_FiniteState_ep0-3.csv (4 file)
├── audit_C_AggressiveFSM_ep0-1.csv (2 file)
├── audit_C_StealthyFSM_ep0-1.csv (2 file)
│
├── detailed_*.jsonl (12 file) — event log đầy đủ: state, LLM response, tool call, RoE verdict
│
├── joint_reward_*.json (12 file) — reward per step + cumulative + metadata
│
└── *.pid (4 file) — process ID cho benchmark run
```

### 23.2 Cách reproduce

```bash
cd mcp-roe-vs-th3

# Setup A-TH3 với FiniteState seed 0
export RED_VARIANT=FiniteState
export EPISODE_SEED=0
export CLAUDE_MODEL=claude-haiku-4-5
python3.11 benchmark/run_benchmark.py --setup A --episode 0

# Setup C-TH3 với StealthyFSM seed 1
export RED_VARIANT=StealthyFSM
export EPISODE_SEED=1
python3.11 benchmark/run_benchmark.py --setup C --episode 1
```

## 24. Tham chiếu

### 24.1 Trong repo này

- `SETUP_REPORT.md` (506 dòng) — thiết kế thí nghiệm đầy đủ, 2 đoạn thay thế chi tiết
- `KET_QUA_SPRINT_4.md` (1117 dòng) — báo cáo chi tiết theo timeline, mỗi lần chạy có kết quả riêng
- `feasibility/prompts/acd2025/base.yml` — prompt TH3 byte-identical
- `feasibility/setup_c_override.py` — 4 hằng số thay thế
- `feasibility/roe/rules_v3.py` — implementation 6 rule
- `tests/test_rules_v3.py` — 34 test pass

### 24.2 Bên ngoài

- **Paper TH3**: Castro et al., "LLMs are Autonomous Cyber Defenders", IEEE CAI 2025
- **Code TH3**: `llms-are-acd-main/` (private repo mirror của paper)
- **CybORG CAGE 4**: https://github.com/cage-challenge/cage-challenge-4
- **Claude Agent SDK**: https://github.com/anthropics/claude-agent-sdk

### 24.3 Git history Sprint 4

Commit chính:
- `487a4e0` — Sprint 4 setup ban đầu
- `231ce34` — TH3 stateless per step
- `e0c3457` — Mở rộng benchmark A/C n=4
- `6f87bef` — n=4 data + phân tích ep0 outlier
- `8740b9a` — Phase confusion analysis C-TH3
- `e5a468c` — Dẫn chứng 3 giả thuyết phase confusion
- `0ffcb68` — Sprint 4 AggressiveFSM benchmark
- `c59890c` — PID files
- `74de065` — Sprint 4 StealthyFSM + finding counter-productive
- `02f1ae0` — Báo cáo tổng kết Sprint 4 (bản v1)

Xem: https://github.com/vuongtranminh/lv/commits/main

---

**Trần Minh Vương** — Sprint 4 hoàn thành ngày 2026-07-05
**Trạng thái**: ✅ Tất cả mục tiêu Sprint 4 đã đạt. Sẵn sàng chuyển Sprint 5 (adaptive RoE + phase fix + 2 red còn lại).
