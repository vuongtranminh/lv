# PHÂN TÍCH REWARD CHI TIẾT — Tại sao A/B/C được điểm như vậy + Hướng khắc phục

> **Phạm vi**: phân tích `step_rewards` (vector 500 phần tử trong `joint_reward_*.json`) của 3 setup × FiniteState × 1 ep. Cross-reference với action LLM đã thực hiện. Đề xuất hướng khắc phục dựa trên kết quả.

---

## 1. Cơ chế tính reward trong CAGE 4

Theo TH3 §II.A (trang 3 bài báo):

> *"Hàm thưởng (reward function) cho các blue agent được thiết kế để nhận **hình phạt** (penalty) nếu các green agent không thể dùng tài nguyên. Điều này có thể xảy ra do:*
> 1. *Các hành động phòng thủ như **chặn một mạng** hoặc **khôi phục (restore) một máy chủ** (việc này tạm thời đưa máy chủ ra khỏi hoạt động một thời gian)*
> 2. *Các red agent gây **tác động (impact)** lên hệ thống của chúng"*

→ **3 nguồn phạt reward** trong CAGE 4:

| Nguồn phạt | Nguyên nhân | Liên quan đến setup nào |
|---|---|---|
| **A** Red impact | Red FSM gây ảnh hưởng đến dịch vụ green users | Tất cả 3 setup (red không đổi) |
| **B** Blue Restore | Wipe host → host tạm thời offline → green không dùng được | Chỉ Setup A (3 Restore), C không có (RoE chặn) |
| **C** Blue BlockTrafficZone | Chặn cả zone → green từ zone đó không dùng được | Không setup nào (0 Block trong tất cả) |
| **D** Blue Remove | Terminate process (chi phí nhỏ, ngắn) | Chỉ Setup A (2 Remove) |

**Reward dương = 0 (max)**. Không có thưởng — chỉ có phạt và "không phạt".

> Trong dữ liệu: max(step_reward) = 0 ở cả 3 setup → confirm không có reward dương.

---

## 2. Phân bố reward chi tiết — Bảng ba A/B/C

### 2.1 Phân loại step theo mức phạt

| Mức phạt | Setup A | Setup B | Setup C |
|---|---|---|---|
| **0** (không bị phạt) | **427 step (85.4%)** | 248 step (49.6%) | 327 step (65.4%) |
| -5 đến -10 (trung bình) | 57 step (11.4%) | **165 step (33.0%)** | 120 step (24.0%) |
| -10 đến -20 (nặng) | 3 step (0.6%) | 63 step (12.6%) | 30 step (6.0%) |
| -20 đến -50 (rất nặng) | 13 step (2.6%) | 24 step (4.8%) | 23 step (4.6%) |
| **Cumulative** | **-660** | **-2110** | **-1515** |

### 2.2 Top 5 step xấu nhất

| Setup | Step xấu nhất | Reward | Action LLM tại step | Phase |
|---|---|---|---|---|
| **A** | step 111 | -30 | Sleep | Phase 0 |
| **A** | step 22, 24, 81, 87 | -25 mỗi step | Sleep | Phase 0 |
| **B** | step 68, 125, 133 | -30 mỗi step | Analyse / DeployDecoy | Phase 0/1 |
| **B** | step 37, 50 | -25 | Analyse | Phase 0 |
| **C** | step 25 | **-35** (xấu nhất 3 setup) | Analyse | Phase 0 |
| **C** | step 141, 161 | -30 | Analyse | Phase 0/1 |
| **C** | step 44, 57 | -25 | DeployDecoy | Phase 0 |

→ **Tất cả step xấu nhất đều ở Phase 0** — red FSM tiến công sớm.

### 2.3 Step bị phạt nặng (<=-20) theo phase

| Phase | A | B | **C** |
|---|---|---|---|
| **0 (Planning)** | 13/168 (7.7%) | 12/168 (7.1%) | **17/168 (10.1%)** |
| 1 (MissionA) | 0/167 (0.0%) | 6/167 (3.6%) | 3/167 (1.8%) |
| 2 (MissionB) | 0/165 (0.0%) | 6/165 (3.6%) | 3/165 (1.8%) |
| **Tổng** | 13 | 24 | **23** |

**Quan sát**:
- Phase 0 là pha nguy hiểm nhất — red FSM bắt đầu chuỗi attack
- Setup A KHÔNG bị phạt nặng nào ở Phase 1+2 → red đã tiến tới ceiling sau Phase 0
- Setup B+C vẫn bị phạt rải rác ở Phase 1+2 → có khả năng do blue action gây thêm cost

---

## 3. Phân tích nguyên nhân từng setup

### 3.1 Setup A — Tại sao chỉ -660? "Strategy of doing nothing"

**Key insight**: 85.4% step reward = 0. LLM A Sleep áp đảo (400/500 = 80% step Sleep) → KHÔNG tác động môi trường → KHÔNG bị phạt từ action của blue.

**Phân tích Top 5 step xấu nhất A**:

| Step | Reward | Action A tại step | Action A ở step TRƯỚC |
|---|---|---|---|
| 22, 24, 81, 87, 111 | -25 đến -30 | **Sleep (12/13 step)** | **Sleep (13/13 step)** |

→ **Setup A bị phạt vì NGỦ KHI CẦN HÀNH ĐỘNG**. Tại 13/13 step phạt nặng, LLM A đã Sleep ở step liền trước → red FSM tích lũy compromise → đến step phạt thì green users không dùng được dịch vụ.

**5 destructive action của A** (3 Restore + 2 Remove):
- Đều ĐÚNG level (3 Restore trên host admin, 2 Remove trên host user)
- **Loại bỏ threat hoàn toàn** → sau đó các step liền sau không bị phạt
- Phụ phí Restore (host tạm offline): mỗi Restore có thể gây -X reward ở step đó, nhưng tránh được phạt tích lũy về sau

**Lý do A thắng (-660)**:
1. **Sleep là chiến lược "rẻ tiền"** — không có chi phí blue action
2. **Khi BUỘC phải action**, A làm ĐÚNG (5/5 destructive đúng level) → cắt được nguồn phạt từ red
3. Phase 1+2: 0% step bị phạt nặng → red đã đạt impact ceiling, A "ngủ qua bão"

**Điểm yếu A** (nếu test red khác):
- Strategy "ngủ" chỉ work khi red FSM có ceiling rõ. AggressiveFSM hoặc ImpactFSM có thể không bị plateau như FiniteState.
- 5 destructive đúng level là **may mắn** với prompt — nếu prompt không rõ về IOC, A có thể destructive sai

### 3.2 Setup B — Tại sao -2110? "Chủ động sai hướng"

**Key insight**: chỉ 49.6% step reward = 0 (so với A 85.4%). LLM B luôn action (99.8% non-Sleep) → mỗi action có chi phí ngầm hoặc tạo cơ hội cho red.

**Phân tích Top 5 step xấu nhất B**:

| Step | Reward | Action B tại step | Action B ở step TRƯỚC |
|---|---|---|---|
| 68, 125, 133 | -30 mỗi step | Analyse / DeployDecoy | DeployDecoy / Analyse |
| 37, 50 | -25 | Analyse | Analyse |

→ **Setup B bị phạt RỘNG**: 165 step bị phạt trung (-5 đến -10), 63 step phạt nặng. Pattern khác A.

**Action ở step trước khi phạt nặng**:
- 15/24 step: DeployDecoy ở step trước
- 9/24 step: Analyse ở step trước

→ **Mỗi DeployDecoy / Analyse không LOẠI BỎ threat** → red tiếp tục compromise → phạt tích lũy.

**3 nguồn gây thiệt hại B**:
1. **0 destructive** (vs A có 5) — threat không bị loại bỏ → green users chịu thiệt liên tục
2. **251 DeployDecoy** — mỗi DeployDecoy là 1 action chiếm slot quyết định, không cứu vãn được threat đã có
3. **Latency cao** (29s/step vs A 13s/step) — trong cùng wall time, red có nhiều "lần" tiến công hơn

**Vì sao B chủ động hơn A nhưng tệ hơn?**

Vì **chủ động sai hướng**:
- A: passive (Sleep), nhưng KHI active thì action ĐÚNG (Restore admin → cut threat)
- B: active 100%, nhưng action toàn DeployDecoy/Analyse — KHÔNG cắt được threat đã có

Phép so sánh: A như người bác sĩ giàu kinh nghiệm — chỉ phẫu thuật khi cần và phẫu thuật ĐÚNG. B như người bác sĩ thực tập — luôn khám và làm xét nghiệm nhưng không bao giờ kê thuốc → bệnh nhân không khỏi.

### 3.3 Setup C — Tại sao -1515? "Chủ động nhưng vẫn không Restore"

**Key insight**: 65.4% step reward = 0 (giữa A 85.4% và B 49.6%). RoE chặn DeployDecoy → C ít action hơn B → ít step có chi phí ngầm hơn B → reward tốt hơn B.

**Setup C cải thiện gì so với B?**

| Chỉ số | B | **C** | Δ C−B |
|---|---|---|---|
| Step reward=0 | 248 (49.6%) | **327 (65.4%)** | +79 step "không phạt" |
| Step phạt trung -5 đến -10 | 165 (33.0%) | 120 (24.0%) | -45 step phạt trung |
| Step phạt nặng <=-20 | 24 (4.8%) | 23 (4.6%) | -1 (tương đương) |

→ **RoE giảm số step bị phạt trung bình** (165 → 120). Không giảm phạt nặng (do red impact, blue không kiểm soát).

**Setup C còn yếu gì so với A?**

| Chỉ số | A | **C** | Δ C−A |
|---|---|---|---|
| Step reward=0 | 427 (85.4%) | 327 (65.4%) | **-100 step "không phạt"** |
| Step phạt trung -5 đến -10 | 57 (11.4%) | 120 (24.0%) | +63 step phạt trung |
| Step phạt nặng <=-20 | 13 (2.6%) | 23 (4.6%) | +10 step phạt nặng |

→ C có nhiều step bị phạt hơn A vì:
1. C action 99.4% step (vs A 20%) → mỗi action có chi phí ngầm
2. C không Restore (0 vs A 5) → threat không bị loại bỏ

**Top 5 step xấu nhất C** (step 25 = -35, xấu nhất 3 setup):

| Step | Reward | Action C tại step | Action C step TRƯỚC |
|---|---|---|---|
| 25 | **-35** | Analyse | Analyse |
| 141, 161 | -30 | Analyse | Analyse |
| 44, 57 | -25 | DeployDecoy | DeployDecoy |

→ Setup C có step "xấu nhất tuyệt đối" (-35) — đoạn Phase 0 đầu khi RoE deny nhiều, C "loay hoay" với Analyse trong khi red đã compromise được host.

---

## 4. Reward được trừ ở đâu? — Phân tích nguồn phạt

### 4.1 Phân loại phạt theo nguồn (theo TH3 §II.A)

**Nguồn 1: Red impact (TÁC ĐỘNG TỪ RED)**

Áp dụng cho **CẢ 3 SETUP** vì red FSM giống nhau. Phạt khi:
- Red Exploit → host bị compromise → green services trên host đó bị chậm/lỗi
- Red Impact → host bị degraded/disconnected → green users không dùng được
- Red PrivilegeEscalate → root access → red có thể đe doạ nhiều dịch vụ

**Cách giảm**: blue phải **Restore host bị compromise** để cắt nguồn red.
- A làm: 3 Restore admin → cắt được 3 host → giảm phạt từ Phase 1
- B làm: 0 Restore → mất Phase 1+2 vì threat không được cắt
- C làm: 0 Restore (đã đề xuất 1 nhưng RoE deny) → tương tự B

**Nguồn 2: Phụ phí từ Restore của blue (HOST DOWNTIME)**

Áp dụng:
- A: 3 Restore → 3 step có chi phí ngắn → tổng chi phí nhỏ so với lợi ích cắt threat
- B: 0 Restore → 0 chi phí từ nguồn này, nhưng KHÔNG cắt được threat
- C: 0 Restore → tương tự B

**Nguồn 3: Phụ phí từ BlockTrafficZone**

Không setup nào dùng (0 Block). Không liên quan.

**Nguồn 4: Phụ phí từ DeployDecoy/Analyse/Remove (CHI PHÍ NGẦM)**

CAGE 4 reward function có thể có chi phí ngầm cho các action — vd:
- DeployDecoy tiêu tốn tài nguyên server → green hosting bị giảm
- Analyse có thể tạo log alert → green system administrators bị "cảnh báo nhiễu"
- Remove gây ngắt session người dùng tạm thời

Không có thông tin chính xác về chi phí ngầm này trong CAGE 4 docs. Nhưng pattern dữ liệu cho thấy:
- A (20% action) → ít chi phí ngầm → 85.4% reward=0
- B+C (99%+ action) → nhiều chi phí ngầm → 50-65% reward=0

### 4.2 Bảng so sánh: TẠI SAO mỗi setup mất reward

| Setup | Cumulative | Nguyên nhân CHÍNH | Nguyên nhân PHỤ |
|---|---|---|---|
| **A** -660 | Mất ở Phase 0 (-445) do Sleep liên tục khi red tiến công | Mất ít ở Phase 1+2 vì red đã ceiling + Restore cắt threat |
| **B** -2110 | Mất ở Phase 1+2 (-1500) do KHÔNG Restore → threat tích lũy | Chi phí ngầm từ 250 DeployDecoy + 248 Analyse |
| **C** -1515 | Mất ở Phase 1+2 (-905) do KHÔNG Restore → threat tích lũy | Chi phí ngầm thấp hơn B (RoE giảm DeployDecoy 251→85) |

---

## 5. Setup C bị TRỪ ở đâu cụ thể?

### 5.1 Phân tích đoạn Phase 0 (step 0-167, mất -610)

C có **131 Analyse + 37 DeployDecoy** ở Phase 0. RoE deny 322 lần DeployDecoy trong toàn episode, phần lớn ở Phase 0 do quota max 2/host bị đạt nhanh.

| Step Phase 0 | Action C | Số step | Tỷ lệ |
|---|---|---|---|
| Analyse | 131 | 78.0% |
| DeployDecoy | 37 | 22.0% |
| Sleep | 0 | 0% |

→ C dành Phase 0 chủ yếu Analyse (do RoE deny DeployDecoy spam). Nhưng Analyse KHÔNG loại bỏ threat → red FSM vẫn compromise được. Kết quả: C mất -610 ở Phase 0 (gấp 1.4× A -445).

### 5.2 Phân tích đoạn Phase 1+2 (step 168-499, mất -905)

C có **281 Analyse + 48 DeployDecoy + 3 Sleep**. **0 Restore** mặc dù LLM thấy threats trong `get_threat_summary()`.

**Bằng chứng C "biết" có threat admin nhưng không Restore**:
- Setup B step 100+ đã từng đề xuất `propose_restore` 0 lần
- Setup C đề xuất 1 `propose_restore` duy nhất → bị RoE deny vì `rule_restore_needs_admin`
- Setup A LLM với cùng observation (raw text) phát hiện `escalate.sh` IOC → đề xuất Restore 3 lần thành công

→ **Vấn đề ở C**: `get_threat_summary` trả về JSON có `compromise_level` nhưng LLM **không trust signal đó đủ mạnh** để gọi Restore. Có thể prompt MCP yêu cầu điều kiện ngặt hơn.

### 5.3 Đoạn xấu nhất của C: step 25 = -35

Phải xem chi tiết JSONL step 25 để hiểu. Reward = -35 là phạt nặng nhất trong cả 3 setup. Có thể red compromise được 1 host trọng yếu (vd database server) → green users không dùng được dịch vụ chính.

LLM C tại step 25: Analyse → không cắt được threat. LLM tại step 24: Analyse → tương tự.

---

## 6. Hướng khắc phục

### 6.1 Khắc phục Setup C (đóng góp luận văn) — 5 đề xuất

**Đề xuất 1: Thêm rule POSITIVE — RoE gợi ý Restore khi điều kiện đủ**

Hiện tại RoE chỉ **DENY** (chặn). Cần thêm rule **SUGGEST** — RoE chủ động khuyến khích khi điều kiện thỏa:

```python
def rule_suggest_restore_when_admin(state: dict) -> SuggestedAction:
    """Khi 1+ host trong threats có compromise_level='admin', gợi ý Restore."""
    for threat in state.get("threats", []):
        if threat.get("compromise_level") == "admin":
            return SuggestedAction(
                action_type="Restore",
                params={"hostname": threat["hostname"]},
                priority="high",
                reason="Host admin compromise — Restore để cắt threat hoàn toàn"
            )
    return None
```

Thêm vào tool `get_threat_summary` response: nếu có suggestion, gắn `recommended_action`. LLM sẽ thấy gợi ý mỗi step.

**Đề xuất 2: Sửa prompt MCP nhấn mạnh Restore khi admin**

`feasibility/prompt.md` hiện viết Restore "Chỉ dùng khi xác nhận admin-level compromise" — quá rụt rè. Sửa thành:

> "**Restore là biện pháp HIỆU QUẢ NHẤT** để loại bỏ admin compromise. Khi `get_threat_summary` trả về threat với `compromise_level='admin'`, **HÃY GỌI propose_restore NGAY**. RoE sẽ deny nếu điều kiện chưa thỏa — đừng ngại thử."

**Đề xuất 3: Cho phép Sleep trong MCP**

Hiện tại MCP system prompt yêu cầu LLM "gọi chính xác MỘT tool propose_* mỗi lượt". Không có tool `propose_sleep`. Thêm:

```python
@tool("propose_sleep", "Không hành động lượt này — khi không có threat đáng kể")
async def propose_sleep(args):
    StepContext.proposed_action = ("Sleep", {}, args.get("reason", ""))
    return _text_result({"status": "approved"})
```

Khi LLM nhận thấy không có threat → Sleep → giảm chi phí ngầm như A.

**Đề xuất 4: Wire 8 rule v2 (đã có sẵn)**

`feasibility/roe/rules_v2.py` có 8 rule (4 precondition + 4 rate-limit) với 13/13 unit test pass. Hiện chỉ wire 3 rule v1. Wire v2 → có thêm:
- `rule_restore_phase_constraint` (không Restore trong Phase Planning)
- `rule_block_critical_zone_forbidden` (không block zone trọng yếu)
- `rule_no_block_when_busy` (không block khi đang IN_PROGRESS)
- `rule_decoy_global_quota` (max 10 decoy/ep tổng)
- `rule_restore_max_per_episode` (max 5 Restore/ep)

**Đề xuất 5: Giảm latency**

C = 32s/step (gấp 2.4× A 13s). Cải thiện:
- **Prompt caching**: cache system prompt MCP (3KB) ở server Anthropic → cache_read 75K token
- **Giảm verbosity tool result**: hiện `get_threat_summary` trả full JSON; rút gọn còn fields cần thiết
- **Giảm max_turns nếu cần**: hiện 8, thực tế LLM dùng ~4 → set 5-6 đủ

### 6.2 Khắc phục Setup A và B

**Setup A** (đã tốt với FiniteState, nhưng có thể yếu với red khác):
- Test thêm 3 red variant (AggressiveFSM, StealthyFSM, ImpactFSM) để verify
- A có thể yếu nếu red không có impact ceiling rõ → A's "Sleep strategy" sẽ thất bại

**Setup B** (yếu nhất, cần ít cải thiện vì không phải đóng góp chính):
- B là baseline cô lập MCP — không cần thắng A. B chỉ cần verify MCP hoạt động.
- B's vai trò: cho Setup C có gốc so sánh (B → C: +595 = đóng góp riêng RoE)

### 6.3 Khắc phục hạn chế chung (cả 3 setup)

**Hạn chế chung 1: CommVectorGenerator fallback EMPTY**

Comm vector luôn rỗng → không kích hoạt được L1 (ảo giác bit). Fix:
- Debug `CommVectorGenerator.create_comm_message()` API signature
- Test với synthetic comm vector có signal admin để verify L1 hiện hữu

**Hạn chế chung 2: n=1**

1 episode không có σ → variance cao (Setup B run khác có thể đạt -70 hoặc -125 ở step 50). Cần:
- 4 episode khác cùng config (seed 1-4) cho A × FiniteState
- Tương tự cho B × FiniteState và C × FiniteState
- Tổng: 12 ep nữa (~3 × 4h = ~12h cho 3 setup × 4 seed)

**Hạn chế chung 3: 1 red variant**

Chưa biết hành vi với AggressiveFSM / StealthyFSM / ImpactFSM. Mỗi red có thể tạo pattern reward khác:
- AggressiveFSM: scan nhanh → có thể bị detect sớm → blue có cơ hội Restore
- StealthyFSM: scan chậm → blue khó detect → Sleep strategy của A có thể yếu
- ImpactFSM: ưu tiên impact → reward âm rất nhanh
- DegradeServiceFSM: làm green services suy giảm dần

---

## 7. Bảng tóm tắt — Tại sao A/B/C được điểm như vậy

| Khía cạnh | Setup A (-660) | Setup B (-2110) | Setup C (-1515) |
|---|---|---|---|
| Chiến lược chính | Passive Sleep | Active DeployDecoy spam | Active Analyse (RoE redirect) |
| % step không phạt | **85.4%** | 49.6% | 65.4% |
| Destructive action | **5 đúng level** | 0 | 0 |
| Restore | 3 (cắt admin host) | 0 | 0 (RoE deny 1) |
| Mất reward chính ở | Phase 0 (-445) | Phase 1+2 (-1500) | Phase 1+2 (-905) |
| Bị phạt vì | Sleep khi red tiến công | DeployDecoy spam + không cắt threat | Analyse spam + không cắt threat (như B nhưng ít hơn) |
| Lý do thắng/thua | Sleep + 5 Restore đúng → win | Active sai hướng → lose | RoE chặn spam → win B, nhưng vẫn không Restore → lose A |

---

## 8. Kết luận

### 8.1 Câu hỏi gốc đã được trả lời

**Q: Điểm được tính ra sao?**
A: Penalty cho mỗi step khi green users không dùng được dịch vụ. 3 nguồn: red impact, blue Restore downtime, blue Block traffic. Max step reward = 0.

**Q: Tại sao A tốt nhất?**
A: 85.4% step reward=0 (Sleep áp đảo) + 5 destructive đúng level → tổng phạt thấp.

**Q: Tại sao B tệ nhất?**
A: 99.8% action nhưng KHÔNG có destructive → threat tích lũy → mất Phase 1+2 (-1500).

**Q: C bị trừ ở đâu?**
A: -905 ở Phase 1+2 do không Restore (RoE deny 1 Restore duy nhất + LLM C không retry Restore). -610 ở Phase 0 do Analyse không cắt threat ngay từ đầu.

### 8.2 Hướng khắc phục ưu tiên

| Ưu tiên | Đề xuất | Tác động kỳ vọng |
|---|---|---|
| 1 (cao) | Thêm rule SUGGEST Restore khi host admin | Cho phép C khắc phục vấn đề chính (0 Restore) |
| 2 (cao) | Sửa prompt MCP nhấn mạnh Restore | LLM C "dám" gọi Restore khi cần |
| 3 (cao) | Cho phép `propose_sleep` trong MCP | C có thể Sleep như A khi không có threat → giảm chi phí ngầm |
| 4 (trung) | Wire 8 rule v2 | RoE đầy đủ hơn |
| 5 (trung) | Chạy n=5 cho 3 setup × FiniteState | Có σ, biết variance thật |
| 6 (thấp) | Giảm latency C qua prompt caching | Cải thiện wall time |
| 7 (thấp) | Test 3 red variant khác | Verify A có thực sự thắng được với red khác không |

### 8.3 Câu hỏi cho thầy/hội đồng

1. Có nên thêm rule SUGGEST trong RoE (chứ không chỉ DENY) không? Có làm "luật chơi" thay đổi cốt yếu?
2. Cho phép `propose_sleep` trong MCP có làm Setup C trở thành "A với MCP" hay không? Có còn ablation hợp lệ?
3. n=1 có chấp nhận được cho báo cáo Phase 0 / Feasibility không, hay BUỘC phải n=5+?

---

*Phân tích dựa hoàn toàn vào file `joint_reward_*.json` và `detailed_*.jsonl` của 3 episode A/B/C × FiniteState × 1 ep. Hướng khắc phục dựa trên patterns định lượng quan sát được.*
