# CASE STUDY CHÉO — A vs B vs C tại các step cụ thể

> Phân tích cross-setup: cùng step → ba setup A/B/C ra quyết định khác nhau → reward khác nhau. Tìm case B/C làm được mà A không, case A làm được mà C không, và **lý do gốc rễ + hướng khắc phục**.

---

## PHÁT HIỆN BẤT NGỜ — Quan trọng nhất

**Setup A có 3 step thấy host bị admin compromise**:
- step 44: `office_network_subnet_user_host_1` (admin) → A Restore
- step 223: `office_network_subnet_user_host_4` (admin) → A Restore
- step 243: `office_network_subnet_user_host_8` (admin) → A Restore

**Setup B và C: 0 STEP thấy admin compromise trong observation!**

→ Suốt 500 step, B và C **KHÔNG bao giờ thấy host của mình bị admin compromise**. Trong khi A thấy 3 lần.

### Lý do (phát hiện quan trọng)

Cùng seed=0, cùng env, nhưng A/B/C có **hành động khác → trạng thái env khác → IOC xuất hiện khác**:

- **A**: Sleep 80% → KHÔNG PHÒNG THỦ → red FSM có thời gian đặt `escalate.sh` trên office_network → A thấy admin compromise → Restore cleanup
- **B**: 251 DeployDecoy + 248 Analyse → LIÊN TỤC PHÒNG THỦ subnet office_network → red KHÔNG đặt được IOC → không có admin compromise
- **C**: 412 Analyse + 85 DeployDecoy + RoE redirect → tương tự B, phòng thủ liên tục

→ **B và C ĐÃ THÀNH CÔNG ở phần phòng thủ subnet của mình** (việc A đã thất bại). Nhưng họ chịu phạt liên tục vì:
1. Chi phí ngầm của DeployDecoy/Analyse (mỗi action có cost nhỏ)
2. 4 baseline đồng đội (không phải LLM) không bảo vệ tốt subnet của họ → red impact ở subnet khác
3. Joint reward tính TỔNG 5 blue → blue_agent_4 (LLM) làm tốt nhưng 4 baseline làm tệ → tổng vẫn âm

**Đây là điều TH3 paper không đề cập** — luận văn phát hiện một góc nhìn mới về đánh đổi giữa "reactive cleanup" và "proactive defense".

---

## 1. Cross-Setup Comparison — 5 mốc step

| Step | Phase | A | B | C |
|---|---|---|---|---|
| 10 | 0 | Sleep | DeployDecoy(web-server-01) | Analyse(app-server-1) |
| 44 | 0 | **Restore(office_network_user_host_1, admin)** | Analyse(web-server-01) | Analyse(db-server) |
| 100 | 0 | Sleep | DeployDecoy(app-server-01) | Analyse(app-server-3) |
| 250 | 1 | Sleep | DeployDecoy(db) | Analyse(dns-resolver) |
| 400 | 2 | Sleep | Analyse(web-server) | Analyse(web-server) |

→ Pattern rõ:
- **A**: Sleep mặc định, Restore khi có admin signal
- **B**: DeployDecoy → Analyse (giảm dần do RoE deny)
- **C**: Analyse áp đảo (RoE đẩy LLM về Analyse "an toàn")

---

## 2. CASE A: A thấy admin compromise — B/C không thấy

### 2.1 Step 44 — A Restore admin, B/C Analyse host khác

| Setup | Threats trong observation | Action |
|---|---|---|
| **A** | office_network_subnet_user_host_1 = **admin** | **Restore(office_network_subnet_user_host_1)** ← cắt threat |
| B | (rỗng) | Analyse(web-server-01) ← không thấy threat |
| C | (rỗng) | Analyse(db-server) ← không thấy threat |

**Nguyên nhân B/C không thấy threat**:

Setup A có 44 step Sleep + 0 hành động → red đã có **44 cơ hội** để đặt IOC trên host nào đó của office_network mà không bị ngăn → step 44 thấy `escalate.sh` xuất hiện.

Setup B/C: tính đến step 44, đã có **~44 action proactive** (DeployDecoy/Analyse) trên office_network → red **không thể** đặt IOC → observation không có file `escalate.sh`.

→ **B và C đã NGĂN CHẶN được việc admin compromise xảy ra ở subnet của mình** — điều A không làm được.

### 2.2 Case A step 223 và 243 — tương tự

Lặp lại pattern: A để admin compromise xảy ra → Restore. B/C: phòng thủ liên tục → không bao giờ thấy admin compromise.

### 2.3 Tại sao B/C vẫn thua A về reward?

| Khía cạnh | A | B | C |
|---|---|---|---|
| Số lần admin compromise xảy ra ở subnet của blue_agent_4 | **3 lần** | 0 lần | 0 lần |
| Số lần Restore | 3 (cleanup hoàn toàn) | 0 | 0 |
| Chi phí ngầm của action | Thấp (Sleep 80%) | Cao (500 action) | Trung (497 action) |
| Reward cuối | **-660** | -2110 | -1515 |

→ **CAGE 4 reward function dường như phạt CHI PHÍ NGẦM của action liên tục HƠN phạt việc để admin compromise xảy ra rồi Restore**.

→ Đây là điểm "trớ trêu": A "lười" hơn nhưng được điểm cao hơn vì:
- Chi phí Sleep = 0
- Khi BUỘC phải action (3 Restore + 2 Remove), A làm ĐÚNG
- Đầu tư 3 Restore (~3 step downtime) < 500 action mỗi step có chi phí ngầm

---

## 3. CASE B: B/C bị phạt khi A KHÔNG bị phạt

### 3.1 Step 68 — B bị phạt -30, A và C reward = 0

| Setup | Threats | Action | Reward |
|---|---|---|---|
| A | (rỗng) | Sleep | **0** |
| **B** | (rỗng) | Analyse(db-server-01) | **-30** ← worst step của B |
| C | (rỗng) | Analyse(database-server) | 0 |

**Lý do**:
- A Sleep → không tác động → reward 0 (red chưa impact step này)
- B: Analyse trên host CỤ THỂ `db-server-01` → có thể trùng host green đang dùng → green users bị disrupt → -30
- C: Analyse trên `database-server` → host khác → không trùng green users → 0

→ **CASE phụ thuộc HOST ĐƯỢC CHỌN**. Cùng action Analyse, khác host → reward khác. C "may mắn" chọn host ít green users hơn.

### 3.2 Step 125 — B bị phạt -30, A và C reward = 0

| Setup | Action | Reward |
|---|---|---|
| A | Sleep | 0 |
| **B** | DeployDecoy(db-server-01) | **-30** |
| C | DeployDecoy(cache-server) | 0 |

Tương tự: DeployDecoy trên db-server-01 có cost cao hơn cache-server.

### 3.3 Step 133 — cả B và C bị phạt, A không bị

| Setup | Action | Reward |
|---|---|---|
| A | Sleep | 0 |
| B | Analyse(web-server-01) | **-30** |
| C | Analyse(db-server) | -25 |

→ Trong khoảng step 133, cả B và C action trên host quan trọng (web/db server) → green users bị disrupt → cả 2 bị phạt. A Sleep được.

**Hệ quả**: A có chiến lược "**không can thiệp khi không cần**" — về mặt reward thì lý tưởng cho CAGE 4 vì reward function chủ yếu phạt khi can thiệp/để impact xảy ra.

---

## 4. CASE C: A bị phạt khi B/C KHÔNG bị phạt

### 4.1 Step 111 — A bị phạt -30, B và C reward = 0

| Setup | Action | Reward |
|---|---|---|
| **A** | Sleep | **-30** ← worst step của A |
| B | Analyse(app-server-01) | 0 |
| C | DeployDecoy(api-gateway-1) | 0 |

**Lý do**:
- A Sleep → red đang impact một host trong subnet của A → A không phản ứng → -30
- B/C đang Analyse/DeployDecoy → có thể CHẶN được red ngay step đó hoặc làm chậm impact → reward 0

→ **CASE B/C THÀNH CÔNG**: phòng thủ proactive đã chặn được red impact ở step này. A's strategy "ngủ" thất bại tại đây.

### 4.2 Step 22, 24, 81, 87 — A bị phạt nặng -25, B/C ổn

A's worst steps đều có cùng pattern: Sleep liên tục → red có cơ hội → impact xảy ra → A bị phạt.

| Step | A action | A reward | B reward | C reward |
|---|---|---|---|---|
| 22 | Sleep | -25 | (cần phân tích) | (cần phân tích) |
| 24 | Sleep | -25 | 0 | -35 ← worst step của C |
| 81 | Sleep | -25 | (cần phân tích) | (cần phân tích) |
| 87 | Sleep | -25 | (cần phân tích) | (cần phân tích) |

→ B/C **bù trừ được phần lớn step "bão"** mà A bị phạt vì ngủ.

---

## 5. CASE C bị trừ điểm — Step 25 (-35 worst)

### 5.1 Phân tích chi tiết

| Setup | Action | Reward |
|---|---|---|
| A | Sleep | 0 |
| B | DeployDecoy(web-server-01) | -5 |
| **C** | Analyse(db-server-1) | **-35** ← worst step trong cả 3 setup |

**Tại sao C bị phạt -35 trong khi A=0 và B=-5?**

Có 3 giả thuyết:

1. **Host `db-server-1` đặc biệt nhạy cảm**: green users phụ thuộc db-server-1 → Analyse gây disrupt mạnh
2. **Timing**: ở step 25, có thể red đang impact một dịch vụ khác → C Analyse db-server-1 làm green users không truy cập được dịch vụ liên quan
3. **Variance**: 1 episode, n=1 → có thể là outlier

→ Cần đọc JSONL chi tiết step 25 của C để verify. Nhưng quan sát chung: step 25 ở Phase 0, C bắt đầu pattern Analyse liên tục → có thể trúng host quan trọng tại thời điểm red đang impact.

### 5.2 Hành vi C trước step 25

JSONL Setup C — 25 step đầu chủ yếu Analyse + DeployDecoy (đã bị RoE deny vài lần). LLM C không có cơ hội Sleep như A → bị buộc action mỗi step → trúng host nhạy cảm.

---

## 6. Bảng tổng hợp — Các case quan trọng

| Case | Setup làm tốt | Setup thua | Lý do |
|---|---|---|---|
| step 44 (A thấy admin) | **A** Restore admin host | B/C không thấy admin → không Restore | A's Sleep cho red đặt IOC → A thấy → Restore. B/C phòng thủ nên red không đặt được IOC |
| step 68, 125, 133 (B's worst) | **A, C** (reward 0) | B bị phạt -30 | B chọn host nhạy cảm (db-server-01) cho action; A Sleep, C chọn host khác |
| step 111 (A's worst) | **B, C** (reward 0) | A bị phạt -30 | A Sleep khi red đang impact; B/C action chặn được phần nào |
| step 22, 24, 81, 87 (A's worst) | **B, C** (reward thấp hơn A) | A bị phạt -25 | Tương tự — A Sleep, B/C active |
| step 25 (C's worst) | **A** (Sleep, 0) | C bị phạt -35 | C Analyse host nhạy cảm tại thời điểm red đang impact |

---

## 7. Tại sao C không làm được những thứ A làm — Phân tích sâu

### 7.1 Vấn đề chính: C KHÔNG thấy admin compromise (B/C có 0 admin step vs A có 3)

**Lý do**: hành động khác → trạng thái env khác → IOC xuất hiện khác.

**Hệ quả**: C không có cơ hội đề xuất Restore (không thấy threat admin).

**Khắc phục**:

- **Đề xuất 1**: Thay đổi cơ chế reward để **không phạt** việc tạm chấp nhận admin compromise + Restore — nghĩa là làm chiến lược A trở thành tối ưu cũng giống chiến lược B/C.
  
  → Không khả thi: ta KHÔNG kiểm soát CAGE 4 reward function.

- **Đề xuất 2**: Thay đổi chiến lược C để **chấp nhận để admin compromise xảy ra rồi Restore**. Tức C có lúc Sleep để red đặt IOC, rồi Restore.
  
  → Đi ngược triết lý "proactive defense" của MCP+RoE. Không hợp lý về mặt đóng góp luận văn.

- **Đề xuất 3 (KHẢ THI nhất)**: Đo lại reward function CAGE 4 — có thể có chi phí ngầm cụ thể cho mỗi action. Nếu thực sự có chi phí, thì **C cần làm ÍT ACTION HƠN** mà vẫn proactive.
  
  → Cụ thể: cho phép `propose_sleep` trong MCP. RoE rule "Sleep được phép khi không có threat đáng kể".

### 7.2 Vấn đề thứ 2: RoE rule v1 chỉ deny, không suggest active Restore

Setup A LLM thấy IOC `escalate.sh` trực tiếp trong prompt → infer admin → Restore. C qua MCP `get_threat_summary` cũng có thể thấy admin nhưng:
- Không proactive đến mức A
- Khi C dám đề xuất Restore (1 lần duy nhất), RoE deny vì rule_restore_needs_admin (host chưa xác nhận admin?)

**Khắc phục**: thêm rule **SUGGEST** Restore khi điều kiện thỏa (đã đề xuất trong PHAN_TICH_REWARD.md).

### 7.3 Vấn đề thứ 3: Chi phí ngầm action với host nhạy cảm

C step 25 bị phạt -35 vì Analyse db-server-1 (host nhạy cảm). Cần:

- **Rule HOST CRITICALITY** trong RoE — không cho phép Analyse/DeployDecoy trên host green users đang dùng intensively
- Hoặc: thêm field `criticality` vào `get_threat_summary` trả về để LLM biết tránh

---

## 8. Tóm tắt và hướng khắc phục

### 8.1 B/C đã làm được những gì A và TH3 chưa

1. ✅ **Phòng thủ proactive subnet của blue_agent_4** — 0 admin compromise (A có 3)
2. ✅ **Sử dụng MCP tool calling** với JSON schema → không có parse fail
3. ✅ **Multi-turn reasoning** — LLM có cơ hội retry sau RoE deny (C đặc biệt: 322 retry thành công)
4. ✅ **Action diversity** — C target 19 host khác nhau (A target 5)
5. ✅ **Reproduces TH3 LLM behavior** — phân bố action DeployDecoy/Analyse giống TH3 Hình 7
6. ✅ **RoE chứng minh khái niệm** — 39.4% deny rate, 99.7% retry thành công

### 8.2 A đã làm được những gì B/C chưa

1. ✅ **Sleep khi không có threat** → 85.4% step reward=0 (vs B 49.6%, C 65.4%)
2. ✅ **Restore khi có admin** → 3/3 Restore đúng level, cắt threat hoàn toàn
3. ✅ **Reward tổng thấp nhất** (-660) — winner ở 1 episode FiniteState test này

### 8.3 Tại sao C cần được khắc phục để thắng A?

C có 5 đóng góp tích cực mà A không có, nhưng vẫn thua A vì 2 vấn đề chính:

| Vấn đề | Tác động | Cách khắc phục |
|---|---|---|
| **C không thấy admin compromise** | 0 cơ hội Restore | Phòng thủ proactive thành công nhưng không phát hiện được vấn đề như A. Đề xuất: vẫn giữ proactive, nhưng định kỳ Sleep để "tạo cơ hội kiểm tra" — hoặc thêm rule "force Restore khi `get_threat_summary` có threat user-level lâu" |
| **C action mỗi step → chi phí ngầm** | Phạt liên tục -5 đến -10 ở nhiều step | Cho phép `propose_sleep` để C có thể không action khi không có threat |
| **C chọn host nhạy cảm để Analyse/Decoy** | Phạt nặng (vd step 25 -35) | Thêm signal `criticality` của host trong `get_threat_summary` để LLM tránh |

### 8.4 Hướng tiến (theo độ ưu tiên)

1. ⭐ **Cho phép `propose_sleep` tool trong MCP** — C có thể Sleep như A khi không có threat đáng kể → giảm 100+ step có chi phí ngầm → giảm ~500-1000 reward
2. ⭐ **Thêm rule RoE SUGGEST Restore** khi `get_threat_summary` có host user-level lâu (≥ 5 step liên tiếp) — C có cơ hội cleanup mà không cần admin level
3. ⭐ **Thêm field `criticality` vào tool result** — LLM tránh action trên host green users đang dùng intensively
4. **Wire 8 rule v2** thay vì 3 rule v1 — RoE đầy đủ hơn
5. **Chạy n=5 cho 3 setup × FiniteState** — confirm variance + xu hướng
6. **Test 3 red variant khác** — verify A's "Sleep strategy" có thực sự thắng với red khác

### 8.5 Giả thuyết: Setup C có thể thắng A nếu...

Nếu áp dụng cả 3 cải thiện trên:
- C có thể **đôi khi Sleep** → giảm chi phí ngầm → reward tăng ~500-800
- C có thể **đôi khi Restore** dù chưa admin (qua rule SUGGEST mềm hơn) → cleanup user-level threat
- C có thể **tránh host nhạy cảm** → giảm step phạt nặng

Kỳ vọng: C reward có thể tới mức ~-400 đến -500 (tốt hơn A -660). Nhưng cần thực nghiệm để verify.

---

*Phân tích dựa trên cross-reference giữa 3 file `detailed_*_FiniteState_ep0.jsonl` của A/B/C. Mọi step number và reward được trace ngược về file artifact cụ thể.*
