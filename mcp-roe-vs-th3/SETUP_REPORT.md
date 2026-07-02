# Sprint 4 — So sánh Fair với TH3: Setup Report

**Học viên**: Trần Minh Vương
**Ngày lập**: 2026-07-01
**Nguồn gốc**: Sau khi Sprint 3 phát hiện Setup A của em không dùng prompt giống TH3, dẫn đến so sánh không fair giữa "MCP+RoE" và "baseline TH3".

---

## 1. Vì sao cần một project mới

Trong Sprint 3, khi mở rộng dữ liệu benchmark từ n=1 lên n=2 và thêm biến thể Setup C-active, em phát hiện ra vấn đề khoa học nghiêm trọng:

- **Setup A của em không dùng prompt TH3**. Thay vào đó, em viết một prompt ~200 dòng tiếng Việt có bổ sung IOC rules và Analyse threshold — những thứ TH3 không có trong prompt gốc `acd2025/base.yml` (142 dòng).
- **Setup C thêm MCP + RoE trên nền prompt cũng khác TH3**. Vì thế khi Setup C so với Setup A, em đã cô lập được biến số "MCP+RoE"; nhưng khi Setup C so với **kết quả TH3 paper báo cáo**, em đang so sánh **4 biến số cùng lúc**: prompt content, interaction paradigm, safety layer, model.
- Kết quả: em không thể claim "MCP+RoE tốt hơn baseline TH3", vì baseline "TH3" em đang so là baseline của em, không phải TH3 thật.

Project cũ `feasibility-mcp-roe/` vẫn giữ nguyên (đã có dữ liệu Sprint 1–3). Project mới `mcp-roe-vs-th3/` được xây riêng cho **thí nghiệm so sánh fair** — mọi biến số ngoài "MCP+RoE" đều được giữ nguyên như TH3.

---

## 2. Câu hỏi nghiên cứu Sprint 4

Ba câu hỏi cần trả lời:

### Câu hỏi 1 — Prompt content đóng vai trò gì?

Khi thay prompt tự viết bằng prompt TH3 nguyên bản (acd2025/base.yml), Setup A đạt reward bao nhiêu? So sánh với:
- Setup A Sprint 3 của em (prompt tự viết): **−802.5 ± 194.5**
- TH3 paper báo cáo GPT-4o-mini: **≈ −1850**
- TH3 paper báo cáo o3-mini: **≈ −500**

Kết quả trả lời: prompt content đóng bao nhiêu phần trăm gap giữa Haiku và o3-mini, còn lại là do model.

### Câu hỏi 2 — MCP paradigm có giá trị khi giữ nguyên prompt content?

Setup C dùng **cùng prompt content** với Setup A (TH3 acd2025/base.yml) nhưng đổi interaction paradigm sang MCP tool calling multi-turn. So sánh:
- A (single-shot JSON) vs C (multi-turn tool call)
- Cả hai cùng nội dung ngữ cảnh, cùng model

Nếu C > A → MCP paradigm có giá trị bổ sung.
Nếu C ≈ A → MCP paradigm chỉ là stylistic change, không thay đổi khả năng defense.
Nếu C < A → MCP paradigm gây overhead (multi-turn cost, deny loop) mà không tạo giá trị.

### Câu hỏi 3 — RoE deterministic có giá trị bảo vệ khi được thiết kế theo reward function?

RoE V3 (thiết kế cho Sprint 4) là bộ rule **được tối ưu theo mechanics của reward function CAGE 4** — không phải theo "an toàn nghiệp vụ chung chung" như RoE V2. Cụ thể:
- RoE V2 hỏi: "Action này có safety không?"
- RoE V3 hỏi: "Action này có phạt Green fail hoặc cho phép Red Impact không?"

Nếu RoE V3 thực sự phản ánh đúng reward mechanics → LLM + RoE V3 phải đạt reward tốt hơn LLM đơn thuần.

---

## 3. Thiết kế thí nghiệm

### 3.1 Hai setup cần benchmark

| Setup | Prompt content | Interaction paradigm | Safety layer | Model |
|---|---|---|---|---|
| **A-TH3** (baseline faithful) | acd2025/base.yml (nguyên bản tiếng Anh) | Single-shot JSON | Không | Claude Haiku 4.5 |
| **C-TH3** (đóng góp luận văn) | acd2025/base.yml (nguyên bản tiếng Anh) + đoạn ngắn về MCP tool | MCP multi-turn tool call | RoE V3 (deny/approve thuần) | Claude Haiku 4.5 |

**Điểm mấu chốt**: prompt CONTENT y hệt nhau. Chỉ khác paradigm (JSON vs MCP tool call) và layer RoE. Model giữ nguyên Haiku 4.5.

### 3.2 Số lượng benchmark

Giai đoạn 1 (Sprint 4 tuần này):
- A-TH3 × FiniteState × 2 episode
- C-TH3 × FiniteState × 2 episode

Tổng: 4 episode × ~500 step × ~11 giây/step = **~6 giờ wall time cho A-TH3** (single-shot nhanh) + **~8 giờ wall time cho C-TH3** (multi-turn) = **~14 giờ**.

Giai đoạn 2 (nếu Giai đoạn 1 cho signal rõ):
- A-TH3 × AggressiveFSM × 2 episode
- C-TH3 × AggressiveFSM × 2 episode
- Thêm ~14 giờ.

### 3.3 Log format — đầy đủ để phân tích posthoc

Mọi episode ghi 3 loại log:

**File 1: `detailed_<setup>_<red>_ep<N>.jsonl`** — JSON Lines chi tiết
- Mỗi step ghi các event: `step_start`, `state_extracted`, `llm_query`, `llm_response_chunk`, `tool_call`, `tool_result`, `roe_verdict`, `action_proposed`, `action_materialized`, `step_end`
- Nội dung `state` bao gồm: mission_phase, threats (hostname + compromise_level + IOCs), comms decoded, last_action, last_action_status, tất cả hostname trong subnet
- Nội dung `action_materialized` bao gồm: cyborg_action, final_str
- Nội dung `roe_verdict` bao gồm: rule triggered, allowed, reason, suggested (nếu có)

**File 2: `audit_<setup>_<red>_ep<N>.csv`** — CSV per-step summary
- step, agent, state_summary, llm_reasoning_snippet, proposed_action, rejected_attempts, final_action

**File 3: `joint_reward_<setup>_<red>_ep<N>.json`** — kết quả tổng
- cumulative_joint_reward, step_rewards (list 500 số), wall_time_seconds, mcp_enabled, roe_enabled

Log này đủ để trích:
- Action distribution (đã có script `analyse_action_distribution.py`)
- Zone-wise reward attribution (script mới cần viết)
- RoE deny statistics (script mới cần viết)
- Latency phân tích (đã có event timestamps)

---

## 4. Prompt content — dùng nguyên bản TH3

### 4.1 File nguồn

Nguồn gốc: `llms-are-acd-main/CybORG/Agents/LLMAgents/config/prompts/acd2025/base.yml` (142 dòng, tiếng Anh, do TH3 tác giả UCSC viết cho paper IEEE CAI 2025).

Trong project này lưu tại: `mcp-roe-vs-th3/feasibility/prompts/acd2025/base.yml` — **giữ đúng tên và cấu trúc thư mục như TH3, byte-identical với bản gốc**. Đã verify bằng `diff` — 0 khác biệt.

**Không dịch tiếng Việt, không sửa dòng nào** — giữ 100% faithful. Lý do:
- Dịch có thể vô tình đổi nghĩa
- So sánh với TH3 báo cáo yêu cầu prompt giống hệt
- Claude Haiku 4.5 xử lý tiếng Anh tốt

### 4.2 Thay đổi giữa Setup A-TH3 và Setup C-TH3 so với TH3 gốc

**Nguyên tắc thiết kế**: KHÔNG sửa `acd2025/base.yml` — file này byte-identical với TH3 gốc. Với Setup C, driver load file này rồi **tìm ĐÚNG chỗ và thay thế** (in-place substitution) 2 đoạn liên quan đến output format. Các phần khác giữ nguyên 100%.

#### Setup A-TH3 — KHÔNG thay đổi gì

- Load `feasibility/prompts/acd2025/base.yml`
- Parse YAML, extract trường `content` (137 dòng sau khi PyYAML dedent block scalar)
- Dùng nguyên xi làm system prompt cho LLM
- LLM output JSON theo instruction đã ghi trong prompt: `{"action": "...", "reason": "..."}`
- **Số dòng thay đổi so với TH3**: 0

#### Setup C-TH3 — 2 thay thế IN-PLACE, không append gì

- Load cùng `acd2025/base.yml` như Setup A
- Tìm và thay đúng 2 đoạn liên quan output format (JSON → MCP)
- Các phần khác (# DESCRIPTION, # ENVIRONMENT RULES, # COMMVECTOR FORMAT, # OBSERVATION STRUCTURE, ## AVAILABLE ACTIONS) giữ nguyên 100%
- **Kích thước**: Setup C prompt = 138 dòng (chỉ dài hơn TH3 gốc 1 dòng do đoạn MCP dài hơn đoạn JSON 1 dòng)

#### Bảng so sánh chi tiết theo section

| Section trong prompt | TH3 gốc (`base.yml`) | Setup A-TH3 | Setup C-TH3 |
|---|---|---|---|
| `# DESCRIPTION` (mô tả vai trò) | 3 câu đầu | Giữ nguyên | Giữ nguyên |
| **[Instruction output format]** ("Respond EXACTLY with one response as a dictionary...") | 6 dòng | Giữ nguyên | **THAY THẾ bằng MCP instruction** (7 dòng) |
| `## AVAILABLE ACTIONS` (Remove/Restore/Block/Allow/DeployDecoy/Analyse) | 6 dòng | Giữ nguyên | Giữ nguyên |
| **[Example responses]** (5 JSON examples) | 11 dòng | Giữ nguyên | **THAY THẾ bằng 5 MCP tool call examples** (11 dòng) |
| `# ENVIRONMENT RULES` (network structure, defense setup, mission phases, reward structure) | 40 dòng | Giữ nguyên | Giữ nguyên |
| `# COMMVECTOR FORMAT` (blue agent networks, bit decoding) | 22 dòng | Giữ nguyên | Giữ nguyên |
| `# OBSERVATION STRUCTURE` (last action status, suspicious activity levels) | 20 dòng | Giữ nguyên | Giữ nguyên |
| **Tổng số dòng** | 137 | 137 (identical) | 138 (+1) |

#### Thay thế 1 — Instruction output format

**GỐC (TH3 `base.yml`)** — bị xóa trong Setup C:

```
Respond EXACTLY with one response as a dictionary with the following keys:
- action: ONLY ONE action from `## AVAILABLE ACTIONS`, always including the required parameter. For <hostname>, you can ONLY execute an action on hosts from your assigned network in
`## BLUE AGENT NETWORKS` with your assigned BLUE AGENT number. For <subnet_id>, you can choose ANY subnet from the network.
- reason: ONLY ONE reason for your choice.

Review examples from `## EXAMPLE RESPONSES` if you are unsure.
```

**THAY THẾ (Setup C)** — chèn vào ĐÚNG vị trí đoạn gốc bị xóa:

```
Each turn, use MCP tools to interact with the environment:
- Call `get_threat_summary()` and `get_comms_decoded()` to gather structured state. Commvector bits are already decoded — you do NOT need to parse bits manually.
- Call EXACTLY ONE `propose_<action>` tool to commit an action. For <hostname>, you can ONLY execute an action on hosts from your assigned network in
`## BLUE AGENT NETWORKS` with your assigned BLUE AGENT number. For <subnet_id>, you can choose ANY subnet from the network. Include a brief `reason` argument.
- A deterministic Rules of Engagement (RoE) layer validates each proposal. If a tool returns `{"status": "denied", "reason": "...", "suggested": "..."}`, read the reason and propose a DIFFERENT action that respects the constraint.

Review examples from `## EXAMPLE RESPONSES` if you are unsure.
```

**Giải thích tiếng Việt — Thay đổi gì và tại sao**:

- **Dòng 1** ("Each turn, use MCP tools..."): Thay câu "Respond EXACTLY with one response as a dictionary" (yêu cầu output JSON). Đây là điểm mấu chốt — Setup C dùng MCP tool call thay vì text JSON. Nếu không thay dòng này, LLM sẽ tuân theo instruction gốc và output JSON text, bỏ qua các MCP tool có sẵn.

- **Bullet 1** (`get_threat_summary` + `get_comms_decoded`): Thêm vào để LLM biết có 2 tool để lấy state. TH3 gốc không cần vì state đến trong text observation. Với MCP, LLM phải chủ động gọi tool. Câu "commvector bits are already decoded" quan trọng — nhắc LLM không cần decode bit thủ công (đây chính là hạn chế 1 của TH3 mà MCP giải quyết).

- **Bullet 2** (`propose_<action>` với ràng buộc hostname): Giữ NGUYÊN câu ràng buộc "For <hostname>, you can ONLY execute an action on hosts from your assigned network..." — đây là ràng buộc domain của TH3, không phải MCP-specific. Chỉ đổi từ "action" (JSON key) sang "propose_<action> tool".

- **Bullet 3** (RoE layer): Đây là thêm mới hoàn toàn — mô tả cơ chế deny/approve của RoE. Nếu không có bullet này, LLM sẽ không biết deny nghĩa là gì, có thể lặp lại action bị deny → tốn turn budget, không phản ứng threat kịp. Câu "propose a DIFFERENT action that respects the constraint" đã proven trong Sprint 2 (322/323 lần LLM retry thành công sau deny).

- **Dòng cuối** ("Review examples from ..."): Giữ NGUYÊN — chỉ vì section `## EXAMPLE RESPONSES` vẫn tồn tại (nhưng examples đã đổi từ JSON sang MCP tool call ở thay thế thứ 2).

#### Thay thế 2 — 5 example responses

**GỐC (TH3 `base.yml`)** — bị xóa:

```
## EXAMPLE RESPONSES
- Example 1:
{"action": "Remove host:restricted_zone_a_subnet_user_host_0", "reason": "Host has been compromised"}
- Example 2:
{"action": "BlockTrafficZone subnet:operational_zone_a_subnet", "reason": "Zone is in an active mission phase"}
- Example 3:
{"action": "Analyse host:restricted_zone_b_subnet_server_host_2", "reason": "Host is in a mission-critical zone"}
- Example 4:
{"action": "Restore host:restricted_zone_b_subnet_server_host_2", "reason": "Host has been detected to have a privileged escalation"}
- Example 5:
{"action": "DeployDecoy host:restricted_zone_a_subnet_server_host_1", "reason": "Preventative measure to detect red activity"}
```

**THAY THẾ (Setup C)**:

```
## EXAMPLE RESPONSES
- Example 1:
propose_remove(hostname="restricted_zone_a_subnet_user_host_0", reason="Host has been compromised")
- Example 2:
propose_block_traffic(target_zone="operational_zone_a_subnet", reason="Zone is in an active mission phase")
- Example 3:
propose_analyse(hostname="restricted_zone_b_subnet_server_host_2", reason="Host is in a mission-critical zone")
- Example 4:
propose_restore(hostname="restricted_zone_b_subnet_server_host_2", reason="Host has been detected to have a privileged escalation")
- Example 5:
propose_deploy_decoy(hostname="restricted_zone_a_subnet_server_host_1", reason="Preventative measure to detect red activity")
```

**Giải thích tiếng Việt — Thay đổi gì và tại sao**:

- **Số ví dụ**: 5 → 5 (giữ nguyên số lượng)
- **Nội dung nghiệp vụ**: giữ NGUYÊN — cùng 5 action trên cùng 5 hostname, cùng lý do:
  - Example 1: Remove trên `restricted_zone_a_subnet_user_host_0` với lý do "Host has been compromised"
  - Example 2: Block operational_zone_a với lý do "Zone is in an active mission phase"
  - Example 3: Analyse trên restricted_zone_b_subnet_server_host_2
  - Example 4: Restore trên restricted_zone_b_subnet_server_host_2 với lý do privileged escalation
  - Example 5: DeployDecoy trên restricted_zone_a_subnet_server_host_1
- **CHỈ thay đổi**: format từ JSON dictionary `{"action": "Remove host:...", "reason": "..."}` sang tool call signature `propose_remove(hostname="...", reason="...")`

- **Vì sao phải đổi cả examples**: Nếu chỉ đổi instruction (thay thế 1) mà giữ nguyên examples JSON, LLM sẽ thấy conflict — bảo dùng MCP tool nhưng ví dụ lại là JSON. LLM có thể chọn theo examples (cụ thể hơn instruction) → output JSON. Cần đổi cả examples cho consistent.

- **Action → tool name mapping** (giữ nguyên semantic):
  - `Remove host:X` → `propose_remove(hostname="X", ...)`
  - `BlockTrafficZone subnet:X` → `propose_block_traffic(target_zone="X", ...)`
  - `Analyse host:X` → `propose_analyse(hostname="X", ...)`
  - `Restore host:X` → `propose_restore(hostname="X", ...)`
  - `DeployDecoy host:X` → `propose_deploy_decoy(hostname="X", ...)`

#### Cơ chế implementation — Python string.replace()

File `feasibility/setup_c_override.py` chứa 4 hằng số:

- `JSON_OUTPUT_INSTRUCTION_ORIGINAL` — chuỗi gốc TH3 cần thay
- `MCP_INTERACTION_INSTRUCTION` — chuỗi thay thế cho Setup C
- `EXAMPLE_RESPONSES_ORIGINAL` — 5 JSON examples gốc TH3
- `EXAMPLE_RESPONSES_MCP` — 5 tool call examples

Hàm `build_setup_c_prompt(th3_base_content)`:
1. Assert `JSON_OUTPUT_INSTRUCTION_ORIGINAL` tồn tại trong content → nếu không, raise (TH3 đã update, cần review)
2. `content.replace(JSON_OUTPUT_INSTRUCTION_ORIGINAL, MCP_INTERACTION_INSTRUCTION)`
3. Assert `EXAMPLE_RESPONSES_ORIGINAL` tồn tại → nếu không, raise
4. `content.replace(EXAMPLE_RESPONSES_ORIGINAL, EXAMPLE_RESPONSES_MCP)`
5. Return prompt đã substitute

Cơ chế fail-fast qua assert đảm bảo nếu TH3 update `base.yml` sau này, code sẽ báo lỗi rõ ràng thay vì âm thầm bỏ qua thay thế.

#### Tóm tắt bằng 1 câu

> Setup C = Setup A với **2 chỗ thay thế in-place** (instruction output format + 5 example responses) — chỉ đổi từ JSON output sang MCP tool call, mọi phần khác của prompt TH3 giữ nguyên 100% byte-identical.

```
# OUTPUT PROTOCOL
Instead of returning a JSON dictionary, use the provided MCP tools:
- Call `get_threat_summary()` and `get_comms_decoded()` first to gather state
- Then call exactly ONE `propose_<action>` tool to commit an action
- If a proposal is denied by policy, read the reason and try a different action

The reasoning content of `# DESCRIPTION` and `# ENVIRONMENT RULES` still applies —
follow those rules when deciding which action to propose.
```

Đoạn này KHÔNG thêm decision rules, KHÔNG thêm hostname format, KHÔNG thêm IOC guidance. Chỉ đơn giản giải thích **cách output**. Vì vậy content "kiến thức miền" vẫn giống hệt Setup A-TH3.

---

## 5. RoE V3 — thiết kế theo reward function

### 5.1 Nguyên tắc thiết kế

Khác với RoE V2 (Sprint 2, safety-focused):

| Khía cạnh | RoE V2 (cũ) | RoE V3 (mới) |
|---|---|---|
| Nguyên lý | "Bảo vệ khỏi hành động phá hủy không có căn cứ" | "Tối ưu reward — deny khi hành động sẽ gây phạt gián tiếp" |
| Cơ chế active suggestion | Có (`recommended_action`) | **KHÔNG** — chỉ deny/approve thuần |
| Số rule | 8 (4 precondition + 4 rate-limit) | 6 (tất cả có căn cứ reward) |
| Cách LLM biết action tiếp theo | `recommended_action` inject vào state | **LLM tự quyết** dựa trên prompt TH3 |

Lý do bỏ `recommended_action`:
- Recommended_action làm blur ranh giới "LLM defense" và "RoE-driven defense"
- Nếu LLM chỉ làm theo recommended_action, thực chất RoE đang làm defense — không phải LLM
- RoE V3 chỉ can thiệp khi LLM sai (deny) → khi đó phản hồi lý do → LLM tự chọn lại

### 5.2 Sáu quy tắc RoE V3 + căn cứ reward

#### R1 — `rule_restore_only_admin_and_critical`

**Rule**: Deny Restore nếu **KHÔNG** thoả cả hai:
- Compromise level của host = admin
- Host thuộc mission-critical zone của phase hiện tại (operational_zone_a Phase 1, operational_zone_b Phase 2)

**Căn cứ reward**: Restore tốn 5 tick → 5 step host offline → mỗi step Green fail LWF/ASF trong 5 step. Tổng phạt gián tiếp ~5-10 điểm nếu zone thường, ~50 điểm nếu operational active. Chỉ đáng khi ngăn được RIA trong operational active zone (mỗi lần −10, có thể xảy ra 5-10 lần trong phần còn lại của episode).

#### R2 — `rule_block_operational_forbidden`

**Rule**: Deny BlockTrafficZone nếu target zone = operational_zone_a trong Phase 1, hoặc operational_zone_b trong Phase 2.

**Căn cứ reward**: Block operational active zone → Green trong zone không truy cập được service ngoài → ASF fail liên tục cho đến khi Allow. Zone active phạt −10/ASF fail.

#### R3 — `rule_restore_max_per_episode`

**Rule**: Deny Restore nếu đã Restore đủ 5 lần trong episode.

**Căn cứ reward**: Mỗi Restore trung bình gây 3-5 Green fail cascade. 5 Restore ~ 15-25 phạt gián tiếp. Vượt 5 lần = quá nhiều cascade damage.

#### R4 — `rule_analyse_max_per_host`

**Rule**: Deny Analyse cùng host nếu đã Analyse host đó 2 lần trong episode.

**Căn cứ reward**: Analyse tốn 2 tick agent busy. Analyse lần 3+ không mang lại info mới (env trả snapshot đầy đủ). Tick busy = Blue không phản ứng được → Red có thêm cơ hội RIA.

#### R5 — `rule_decoy_quota`

**Rule**: Deny DeployDecoy nếu (host đã có ≥ 2 decoy) HOẶC (tổng decoy episode ≥ 10).

**Căn cứ reward**: Decoy chi phí 0 nhưng nhiều decoy làm nhiễu tín hiệu — nhân viên Green có thể vô tình truy cập → cascade khó lường. Giới hạn tương tự RoE V2.

#### R6 — `rule_sleep_always_ok`

**Rule**: Approve Sleep KHÔNG ĐIỀU KIỆN — bất kể state.

**Căn cứ reward**: Sleep chi phí 0 direct và 0 gián tiếp (Green không phụ thuộc Blue action để làm việc, chỉ phụ thuộc host state). Sleep là default an toàn nhất.

### 5.3 Không có rule nào chặn LLM Sleep khi có threat

Đây là **khác biệt LỚN** so với RoE V2 + prompt_active.md ở Sprint 3.

Lý do bỏ `rule_no_sleep_when_threat`:
- Sprint 3 chứng minh: khi buộc LLM hành động thay Sleep → reward tệ hơn (−890 điểm cho 29 action)
- Buộc hành động là **đi ngược reward mechanics** — tối ưu thực sự là "chỉ act khi cần"
- Nếu prompt TH3 tự dạy LLM khi nào cần act (mà đó là điều acd2025/base.yml LÀM), thì RoE không cần ép nữa

---

## 6. Kỳ vọng kết quả

### 6.1 Bảng dự đoán trước khi chạy

Dựa trên reasoning từ Sprint 3:

| Setup | Reward kỳ vọng | Lý do |
|---|---|---|
| **A-TH3 baseline** (Haiku, TH3 prompt) | **−700 đến −1200** | Prompt TH3 giàu context hơn Sprint 3 A → tốt hơn (−802). Nhưng Haiku yếu hơn o3-mini → không đạt −500 |
| **C-TH3** (Haiku, TH3 prompt + MCP + RoE V3) | **−600 đến −1000** | RoE V3 chặn action cascade damage. Nhưng multi-turn overhead có thể làm bằng hoặc chậm hơn A |

### 6.2 Ba kịch bản có thể xảy ra và hàm ý

**Kịch bản 1 — C-TH3 > A-TH3 rõ rệt** (vd C −650, A −900):
- **Hàm ý**: MCP+RoE V3 có giá trị bổ sung khi prompt giống nhau
- **Luận văn claim**: "MCP+RoE cải thiện reward baseline TH3 khoảng +250 điểm khi cùng model + cùng prompt content"
- **Đây là kết quả mong đợi cho luận văn**

**Kịch bản 2 — C-TH3 ≈ A-TH3** (chênh < 1σ):
- **Hàm ý**: MCP+RoE V3 không thêm gì về reward khi prompt đủ giàu context
- **Luận văn re-scope**:
  - Giữ claim MCP giải quyết hallucination bit + hostname (đã chứng minh)
  - Giữ claim RoE guarantee no unfounded destructive actions
  - Bỏ claim "cải thiện reward"
  - Thêm negative finding: "MCP+RoE là safety layer, không phải performance layer"

**Kịch bản 3 — C-TH3 < A-TH3** (C tệ hơn):
- **Hàm ý**: MCP paradigm gây overhead mà không mang lại giá trị
- **Nguyên nhân có thể**:
  - Deny loop tiêu tốn turn budget
  - LLM chưa quen dùng tool, tự do JSON tốt hơn
  - RoE V3 rule có logic bug
- **Luận văn**: báo cáo trung thực, đề xuất tương lai (multi-hop tool call, better rule design)

### 6.3 Analysis pipelines em sẽ chạy sau khi có data

1. **Reward mean ± std cho 2 setup** — bảng chính
2. **Action distribution comparison** — Sleep%, số host can thiệp, phân bố 6 action
3. **Zone × Phase reward attribution** — mỗi setup phạt bao nhiêu ở operational_zone_a Phase 1, restricted_zone_b Phase 2, v.v.
4. **RoE V3 rule statistics** — mỗi rule fire bao nhiêu lần trong C-TH3, LLM có bị block gây tệ không
5. **Latency comparison** — average step time, tool call count trung bình mỗi step

---

## 7. Cấu trúc project mới

```
mcp-roe-vs-th3/
├── SETUP_REPORT.md                     ← file này
├── README.md                            ← quick start
│
├── feasibility/
│   ├── prompts/
│   │   ├── acd2025/
│   │   │   ├── base.yml                ← BYTE-IDENTICAL với TH3 gốc (single source of truth)
│   │   │   └── base.md                 ← Extract từ base.yml, readable — dùng cho Setup A
│   │   ├── setup_c_final.md            ← Setup C prompt SAU khi 2 chỗ thay thế (readable)
│   │   └── regenerate_md.py            ← Script tái sinh 2 file .md từ base.yml
│   │
│   ├── setup_c_override.py              ← Chứa 4 hằng số: 2 đoạn gốc + 2 đoạn thay thế
│   ├── paper_style_th3.py               ← Setup A driver (load base.yml, single-shot JSON)
│   ├── prompt_th3_mcp.py                ← Setup C driver (base.yml + build_setup_c_prompt)
│   ├── tools.py                         ← 7 MCP tool, KHÔNG có recommended_action
│   ├── state_extractor.py               ← từ feasibility-mcp-roe (đã reuse)
│   ├── context.py                       ← simplified — không có active_mode
│   ├── detailed_logger.py               ← từ feasibility-mcp-roe (đã reuse)
│   ├── audit.py                         ← từ feasibility-mcp-roe (đã reuse)
│   ├── claude_policy.py                 ← driver 2 setup
│   │
│   └── roe/
│       ├── __init__.py
│       ├── policy_engine.py             ← engine (unchanged API)
│       └── rules_v3.py                  ← 6 rule mới, thiết kế cho reward
│
├── benchmark/
│   ├── run_benchmark.py                 ← runner có --tag, --setup A/C, --red variant
│   ├── analyse_action_distribution.py   ← reuse
│   ├── analyse_zone_attribution.py      ← MỚI: reward theo zone × phase
│   ├── analyse_roe_v3_stats.py          ← MỚI: RoE V3 rule fire statistics
│   └── results/                          ← output benchmark
│
├── tests/
│   ├── test_rules_v3.py                 ← 34 test cho RoE V3 (34/34 pass)
│   ├── test_th3_prompt_load.py          ← test load prompt file OK
│   └── test_integration.py              ← smoke test end-to-end
│
└── docs/
    ├── COMPARISON_SPRINT3.md            ← so sánh Sprint 3 và Sprint 4 findings
    └── ANALYSIS_PIPELINE.md             ← hướng dẫn chạy analysis scripts
```

**Ghi chú về prompt files**:

- `feasibility/prompts/acd2025/base.yml` là **single source of truth**: đúng cấu trúc thư mục và tên file như TH3 gốc, nội dung **byte-identical**, không sửa dòng nào. Đây là prompt canonical TH3 dùng cho IEEE CAI 2025.
- `feasibility/prompts/acd2025/base.md` là bản extract readable của `base.yml` (chỉ có trường `content`, bỏ YAML wrapper). **Không sửa tay** — dùng `regenerate_md.py` để đồng bộ nếu `base.yml` update.
- `feasibility/prompts/setup_c_final.md` là **Setup C prompt sau khi thay thế 2 chỗ** (in-place substitution): xem sẵn được toàn bộ prompt cuối cùng LLM Setup C nhận, không cần chạy code. Được generate từ `base.yml` + `setup_c_override.py` bằng `regenerate_md.py`.
- **Runtime behavior**: driver Setup A load `base.yml` (parse YAML → extract content). Driver Setup C load `base.yml` + apply `build_setup_c_prompt()` để thay thế 2 đoạn.
  - Có thể switch sang load thẳng `.md` để bỏ YAML parser dependency (không đổi behavior LLM).
- Xem §4.2 chi tiết 2 đoạn thay thế + giải thích tiếng Việt tại sao thay.

---

## 8. Lộ trình thực thi Sprint 4

### Ngày 1 (2026-07-01)
- ✓ Tạo project scaffold
- ✓ Viết SETUP_REPORT.md (file này)
- ✓ Copy acd2025/base.yml sang project mới
- ✓ Viết rules_v3.py (6 rule)
- ✓ Viết test_rules_v3.py

### Ngày 2 (2026-07-02)
- Viết `paper_style_th3.py` + `prompt_th3_mcp.py` (đầu cắm cho 2 setup)
- Viết `tools.py` phiên bản không có recommended_action
- Viết `claude_policy.py` adapter
- Viết `run_benchmark.py`
- Smoke test integration (10 step mỗi setup)

### Ngày 3-4 (2026-07-03 và 07-04)
- Benchmark **A-TH3 × FiniteState × 2 ep** (~4 giờ)
- Benchmark **C-TH3 × FiniteState × 2 ep** (~8 giờ)
- Chạy nền qua đêm

### Ngày 5 (2026-07-05)
- Chạy analysis pipelines (mục 6.3)
- Cập nhật SETUP_REPORT.md với section "Kết quả thực tế + phân tích"
- Viết `docs/COMPARISON_SPRINT3.md` — so sánh với Sprint 3
- Quyết định có mở rộng sang AggressiveFSM không

### Ngày 6-7 (2026-07-06 và 07-07)
- Nếu Kịch bản 1 (C > A): mở rộng AggressiveFSM, có kết quả solid cho luận văn
- Nếu Kịch bản 2 (C ≈ A): viết lại Chương 5 với negative finding
- Nếu Kịch bản 3 (C < A): điều tra RoE V3 rule có bug không, có thể phải chạy lại

---

## 9. Rủi ro và phương án dự phòng

| Rủi ro | Khả năng | Phương án |
|---|---|---|
| Prompt TH3 tiếng Anh nguyên bản không hoạt động tốt trên Haiku (Haiku hiểu tiếng Việt tốt hơn?) | Thấp — Claude native English | Nếu cần, dịch section MCP OUTPUT sang tiếng Anh Việt hoá nhẹ |
| RoE V3 rule có logic bug làm C tệ hơn dự kiến | Trung | Test suite 12+ test cover cả edge case. Phân tích RoE stats posthoc |
| Multi-turn MCP tốn nhiều token → rate limit | Thấp | Đã chạy Sprint 3 nhiều lần không gặp |
| Benchmark 14h vượt quota tuần | Thấp | Sprint 4 chỉ có A-TH3 + C-TH3, không có active nữa → khả thi |
| Haiku model bottleneck — dù prompt đầy đủ vẫn tệ | Trung | Nếu Kịch bản 3 xảy ra, thảo luận trong luận văn "model limitation" — không phải bug của MCP+RoE |

---

## 10. Cam kết đạt được sau Sprint 4

Sau khi hoàn thành Sprint 4, em sẽ có:

1. **Bảng số liệu 4 episode fair** (2 setup × 2 ep) — μ ± σ tính được, so sánh trực tiếp MCP+RoE vs baseline TH3 khi giữ nguyên prompt.
2. **Tất cả log JSONL đầy đủ** — cho phép phân tích sâu bất cứ khía cạnh nào của behavior LLM.
3. **Ba script phân tích** — action distribution, zone attribution, RoE stats.
4. **Kết luận rõ ràng** cho một trong 3 kịch bản → định hướng chương Kết luận luận văn.
5. **RoE V3** — thiết kế mới có bằng chứng lý thuyết từ reward function CAGE 4, không chỉ heuristic.

Đây là dữ liệu **đủ để bảo vệ luận văn**, dù kết quả C > A, C ≈ A, hay C < A — vì cả 3 đều là finding khoa học có giá trị khi được document rigorously.

---

**Trần Minh Vương** — 2026-07-01
