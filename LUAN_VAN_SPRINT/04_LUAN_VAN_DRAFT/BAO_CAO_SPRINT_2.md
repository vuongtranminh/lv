# BÁO CÁO SPRINT 2 — Fix 5 vấn đề + Re-run Setup C

> **Phạm vi Sprint 2**: Fix 5 vấn đề pending từ Sprint 1 (D1 hostname, D2 RoE suggest, D3 prompt user-level + ngưỡng Analyse, tool propose_sleep/remove, wire 8 rule v2) + re-run Setup C × FiniteState × 1 ep để verify đồng thời các fix.

> **Thời gian thực tế**: 1 ngày code fix + 4h re-run.

> **Cam kết trung thực**: báo cáo này TRƯỚC HẾT trình bày sự thật phát hiện qua log — không che giấu các nghịch lý hay diễn giải "ép" theo kỳ vọng.

---

## 1. Mục tiêu Sprint 2 (theo BAO_CAO_LOI_SPRINT_1.md đề xuất)

1. **Fix D1** Hostname hallucination (`available_hostnames` field) — đã làm cuối Sprint 1
2. **Fix D2** RoE chủ động SUGGEST (thêm `recommended_action`)
3. **Fix D3** Prompt user-level + ngưỡng Analyse ≤ 2 lần
4. **Thêm tool `propose_sleep`** và `propose_remove`
5. **Wire 8 rule v2** thay 3 rule v1
6. Re-run Setup C × FiniteState × 1 ep

Mục tiêu kỳ vọng: Setup C reward đạt mức -500 đến -700 (cải thiện 800+ so với -1515 ban đầu).

---

## 2. Kết quả định lượng — Setup C Sprint 2

### 2.1 Tổng quan (vs Sprint 1)

| Setup | Reward | Wall time | Events JSONL | Δ vs A |
|---|---|---|---|---|
| **A** (baseline TH3) | -660 | 6562s (1h49) | 3602 | baseline |
| **C Sprint 1** (pre-fix) | -1515 | 15936s (4h26) | 9774 | -855 |
| **C Sprint 2** (post-fix) | **-585** | 14350s (3h59) | 8980 | **+75** 🎉 |

→ **C Sprint 2 VƯỢT baseline A +75 reward** (lần đầu trong luận văn).
→ Cải thiện so với C Sprint 1: **+930 reward** (-1515 → -585).

### 2.2 Đường cong reward — 10 mốc step

| Step | A | C v1 | C v2 | Δ(v2−A) | Δ(v2−v1) |
|---|---|---|---|---|---|
| 50 | -105 | -95 | -110 | -5 | -15 |
| 100 | -230 | -190 | -180 | +50 | +10 |
| 150 | -415 | -480 | **-195** | **+220** | **+285** |
| 200 | -460 | -675 | -250 | +210 | +425 |
| 250 | -485 | -815 | -285 | +200 | +530 |
| 300 | -490 | -905 | -330 | +160 | +575 |
| 350 | -510 | -975 | -450 | +60 | +525 |
| 400 | -570 | -1120 | -505 | +65 | +615 |
| 450 | -615 | -1305 | -565 | +50 | +740 |
| **500** | **-660** | **-1515** | **-585** | **+75** | **+930** |

### 2.3 Reward theo Mission Phase

| Phase | A reward (avg/step) | C v1 reward | C v2 reward | Δ v2 vs A |
|---|---|---|---|---|
| **0 (Planning)** | -445 (-2.65) | -610 | **-220 (-1.31)** | **+225** ⭐ |
| **1 (MissionA)** | -65 (-0.39) | -350 | -205 (-1.23) | **-140** |
| **2 (MissionB)** | -150 (-0.91) | -555 | **-160 (-0.97)** | **-10** |
| Tổng | -660 | -1515 | -585 | +75 |

→ Cải thiện chính ở **Phase 0** (Planning) — C v2 giảm penalty -225 so với A.
→ Phase 1: C v2 vẫn kém A -140 (A có IOC admin nên Restore cắt threat từ Phase 0 → ít penalty Phase 1)
→ Phase 2: gần ngang nhau.

---

## 3. PHÁT HIỆN BẤT NGỜ — C Sprint 2 dùng 100% Sleep

### 3.1 Action distribution — C v2 chỉ Sleep

| Action | Setup A | C Sprint 1 | **C Sprint 2** |
|---|---|---|---|
| Analyse | 95 | 412 | **0** |
| DeployDecoy | 0 | 85 | **0** |
| Remove | 2 | 0 | **0** |
| Restore | 3 | 0 | **0** |
| Sleep | 400 (proposed=None) | 3 | **500** ⭐ |
| **Tổng action chủ động** | 100 | 497 | **0** |

→ **Setup C Sprint 2 hoàn toàn không có hành động chủ động nào** trong 500 step. LLM gọi `propose_sleep` **501 lần** (498 thuần Sleep + 3 step có thể có nhiều tool call).

### 3.2 Tool calls C v2

| Tool | C v1 | **C v2** |
|---|---|---|
| `get_threat_summary` | 648 | **972** (1.94/step) |
| `get_comms_decoded` | 497 | **500** (1.0/step) |
| `propose_analyse` | 412 | **0** |
| `propose_deploydecoy` | 407 | **0** |
| `propose_restore` | 1 | **0** |
| `propose_sleep` | (chưa có) | **501** |

### 3.3 RoE verdicts — C v2 KHÔNG có verdict nào!

| | C v1 | **C v2** |
|---|---|---|
| Tổng `roe_verdict` events | 820 | **0** |

→ Vì C v2 chỉ gọi `propose_sleep` (luôn approved, bypass RoE). Không gọi propose có hostname nào → không có RoE check.

### 3.4 Vì sao LLM C v2 chỉ chọn Sleep?

Sample 5 lý do LLM C v2 đưa ra (từ JSONL):

```
Step 0:   "Không thể lấy threat summary hiện tại. Chờ để hệ thống phục hồi
           và quay lại điều tra."
Step 1:   "Toàn mạng sạch, các đồng đội báo none compromise. Chờ tín hiệu mới."
Step 2:   "Mạng sạch: tất cả đồng đội báo 'none' compromise, không có tín
           hiệu độc hại."
Step 200: "Tất cả đồng đội báo none compromise. Mạng sạch, không hành động
           cần thiết."
Step 400: "Tất cả blue agent báo none compromise, mạng sạch, không threat
           phát hiện"
```

**Nguyên nhân gốc rễ** (3 yếu tố cộng dồn):

1. **`recommended_action` mới đề xuất Sleep 98%**: trong 972 lần gọi `get_threat_summary`, 954 lần trả `recommended_action = (Sleep, low)`. Chỉ 18 lần đề xuất DeployDecoy. **0 lần đề xuất Restore/Remove** vì observation không có IOC admin/user.

2. **Observation thực sự "sạch" trong env C v2**:
   - **0 step có admin IOC** (escalate.sh) trong raw observation
   - **0 step có user IOC** (cmd.sh) trong raw observation
   - Comm vector từ 4 đồng đội luôn `none` (4×500 = 2000 reports all none)
   - → Mạng "sạch" theo nghĩa observation của blue_agent_4 không thấy threat nào

3. **Prompt mới khuyến khích Sleep mạnh hơn**: section "Khi mạng sạch" trong `prompt.md` viết *"Ưu tiên propose_sleep để giảm chi phí. KHÔNG ép phải hành động."* — LLM tin và làm theo.

### 3.5 So sánh với Setup A để hiểu

- **Setup A** (cùng seed, cùng red): observation **CÓ** 3 step admin IOC + 92 step user IOC
- **Setup C v2** (cùng seed, cùng red): observation **KHÔNG có IOC nào**

→ Cùng seed nhưng đường evolution env khác nhau do hành động 5 blue agent khác nhau:
- Setup A: LLM Sleep 80% → red tự do tấn công subnet office_network của blue_agent_4 → IOC xuất hiện
- Setup C v2: 4 baseline blue đồng đội hoạt động "khác" do red tấn công các subnet khác → IOC không xuất hiện trong subnet của blue_agent_4

→ **Kết quả "C v2 vượt A" KHÔNG phải vì C v2 phòng thủ tốt hơn** — mà vì:
- Trong condition của C v2: red không compromise subnet office_network → 0 IOC → Sleep là chiến lược tối ưu
- A bị compromise 3 host → phải Restore (mất chi phí Restore downtime) → reward thấp hơn -75

→ **C v2 đạt -585 = "Sleep strategy may mắn"**, không phải "MCP+RoE thắng nhờ phòng thủ chủ động".

---

## 4. Phân tích Sprint 2 fixes — cái nào work?

### 4.1 ✅ D1 (hostname hallucination) — Đã verify gián tiếp

C v2 không gọi propose_* có hostname → không có cơ hội bịa hostname. Validation logic trong `_propose()` không kích hoạt vì không có propose_analyse/restore/remove/deploy.

→ Không phản ánh fix D1 hoạt động THẾ NÀO với thực tế. Cần test riêng với observation có IOC thật.

### 4.2 ⚠️ D2 (RoE recommended_action) — Work nhưng dẫn đến side effect

| Recommended action | Số lần |
|---|---|
| (Sleep, low) | 954 (98%) |
| (DeployDecoy, low) | 18 (2%) |
| (Restore, critical) | **0** |
| (Remove, high) | **0** |

→ RoE recommend Sleep áp đảo vì `recommend_next_action()` ưu tiên Sleep khi mạng sạch (priority 3 trong logic).

→ **LLM TIN recommended_action quá nhiều**. Đáng lẽ priority "low" chỉ là gợi ý, LLM có quyền tự quyết. Nhưng LLM 100% làm theo.

**Vấn đề**: prompt design cần điều chỉnh — `recommended_action` không nên là "lệnh", mà là "gợi ý". Hiện LLM mất tính chủ động.

### 4.3 ✅ D3 (Loop Analyse user-level) — Khắc phục triệt để

| Chuỗi action lặp cùng host (≥ 3 lần / 5 step) | C v1 | **C v2** |
|---|---|---|
| Số chuỗi | 40 | **0** |
| Chuỗi dài nhất | 6 lần | **0** |

→ **Loại bỏ hoàn toàn vòng lặp Analyse**. Vì LLM không gọi Analyse nào. (Vẫn không verify được nếu LLM phải Analyse trong môi trường có IOC, có lặp không.)

### 4.4 ✅ Tool propose_sleep — Hoạt động đầy đủ

- 501 tool calls, 100% approved (bypass RoE đúng spec)
- 500 step có final action `Sleep({})`
- LLM tận dụng để giảm chi phí ngầm

### 4.5 ✅ Wire 8 rule v2 — Verify gián tiếp qua tests

48/48 unit test pass. Nhưng C v2 không gọi propose có hostname nào → không thực sự test rule v2 trong production. Cần test với observation có IOC.

### 4.6 ✅ Latency cải thiện

| | C v1 | **C v2** |
|---|---|---|
| Mean latency | 31.83 s/step | **28.66 s/step** (-10%) |
| P95 | 39.07 s | 34.94 s |
| Wall time | 4h26 | **3h59** |

→ Giảm 10% latency. Nguyên nhân: propose_sleep nhanh hơn propose_analyse/decoy (không qua RoE validate).

---

## 5. Đánh giá tổng hợp Sprint 2

### 5.1 Thành công

| Tiêu chí | Trạng thái |
|---|---|
| 5 fix code Sprint 2 + 12 test mới pass | ✅ 48/48 pass |
| Setup C reward cải thiện | ✅ -1515 → -585 (+930) |
| Setup C vượt A baseline TH3 | ✅ Lần đầu: +75 reward |
| Loop Analyse được khắc phục | ✅ 40 chuỗi → 0 chuỗi |
| Latency giảm | ✅ -10% |
| Wall time giảm | ✅ 4h26 → 3h59 |

### 5.2 Thất bại + side effect

| Vấn đề | Mức độ |
|---|---|
| **C v2 chỉ Sleep 100% — không có hành động chủ động** | ⚠️⚠️ Nghiêm trọng |
| recommended_action ép LLM theo gợi ý quá mức | ⚠️ Trung |
| Không verify được MCP+RoE thực sự work trong env có IOC | ⚠️ Trung |
| C v2 + Setup A khác observation evolution → không so sánh trực tiếp | ⚠️ Trung |

### 5.3 Câu hỏi quan trọng cho luận văn

**Q1**: Setup C v2 vượt A +75 có chứng minh MCP+RoE > TH3 không?

**A**: **KHÔNG triệt để**. Reward C v2 thấp hơn vì observation env C v2 không có IOC để phòng thủ, không phải vì MCP+RoE phòng thủ tốt hơn. Đây là sự khác biệt evolution env, không phải khác biệt chiến lược.

**Q2**: Nếu A và C v2 thấy cùng observation, kết quả sẽ ra sao?

**A**: Chưa biết. Cần test deterministic (cùng input → cùng output) bằng cách:
- Inject synthetic observation có IOC vào C v2
- Hoặc force seed reproducible cho cả A và C v2

**Q3**: Sprint 2 fixes có vô ích không?

**A**: KHÔNG. Các fix vẫn là cải tiến đúng hướng:
- D1 hostname validation ngăn LLM bịa khi đề xuất action
- D3 prompt rule ngăn Analyse loop
- propose_sleep là cần thiết (giảm chi phí khi sạch)
- Wire 8 rule v2 mạnh hơn

Nhưng **prompt design cần điều chỉnh** để LLM không quá thụ động — phải proactive một cách có chọn lọc, không chỉ Sleep mặc định.

---

## 6. Đề xuất Sprint 3

### 6.1 Sửa prompt MCP — Cân bằng proactive vs Sleep

**Vấn đề**: Sprint 2 prompt hiện làm LLM "lười" — luôn Sleep khi recommended_action = Sleep.

**Fix đề xuất** (`prompt.md`):

```markdown
## Quy tắc cân bằng Sleep vs proactive

- recommended_action với priority `low` (Sleep/DeployDecoy) là GỢI Ý.
  Bạn có quyền chọn khác nếu có lý do.
- KHÔNG NÊN Sleep liên tục quá 5 step. Sau 5 lần Sleep, BẮT BUỘC:
  - Thực hiện ít nhất 1 Analyse hoặc DeployDecoy proactive
  - Mục đích: thám hiểm trạng thái mạng, phát hiện threat sớm
- Mỗi 50 step, kiểm tra: nếu chưa từng Analyse trong 50 step gần nhất,
  PHẢI Analyse 1 host ngẫu nhiên để confirm "mạng vẫn sạch".
```

### 6.2 Test với observation có IOC inject thủ công

Để verify MCP+RoE thực sự work khi có threat thật, viết test synthetic:

```python
def test_c_setup_with_injected_admin_ioc():
    # Tạo observation có 1 host bị admin compromise
    obs = make_obs_with_ioc("host_x", "escalate.sh")
    # Chạy 10 step C v2 với observation này
    # Verify LLM C ra Restore trong 3 step đầu
```

### 6.3 Chạy thêm n=5 ep × 4 red variant

Hiện tại n=1, không có σ. Sprint 3 mục tiêu:
- 5 ep × A + 5 ep × C v2 × FiniteState (~30h chạy)
- Sau đó 4 red variant khác (~120h)
- Tổng bảng đầy đủ 5 × 4 × 3 = 60 ep

### 6.4 Verify deterministic reproducibility

C v2 với seed=0 chạy lại 1 lần nữa — reward có giống -585 không? Variance giữa 2 lần chạy cùng config bao nhiêu?

---

## 7. Trạng thái dữ liệu sau Sprint 2

| File | Setup | Mục đích |
|---|---|---|
| `audit_A_FiniteState_ep0.csv` | A | Baseline Sprint 1 |
| `detailed_A_FiniteState_ep0.jsonl` | A | Log đầy đủ baseline |
| `joint_reward_A_FiniteState_ep0.json` | A | Reward A = -660 |
| `audit_B_FiniteState_ep0.csv` | B v3 | Sprint 1 MCP only |
| `detailed_B_FiniteState_ep0.jsonl` | B v3 | Log B |
| `joint_reward_B_FiniteState_ep0.json` | B | Reward B = -2110 |
| `audit_C_FiniteState_ep0_sprint1.csv` | C v1 | Sprint 1 MCP+RoE (pre-fix) |
| `detailed_C_FiniteState_ep0_sprint1.jsonl` | C v1 | Log C Sprint 1 |
| `joint_reward_C_FiniteState_ep0_sprint1.json` | C v1 | Reward C v1 = -1515 |
| `audit_C_FiniteState_ep0.csv` | C v2 | **Sprint 2 MCP+RoE (post-fix)** |
| `detailed_C_FiniteState_ep0.jsonl` | C v2 | **Log C Sprint 2** |
| `joint_reward_C_FiniteState_ep0.json` | C v2 | **Reward C v2 = -585** |

→ Có thể cross-compare A vs C v1 vs C v2 chi tiết từng step bằng `inspect_episode.py`.

---

## 8. Kết luận Sprint 2

**Thành tựu kỹ thuật**:
- 5 fix code triển khai trọn vẹn, 48/48 test pass
- C reward cải thiện 930 từ -1515 lên -585
- C vượt A baseline TH3 lần đầu (+75)
- Loop Analyse khắc phục triệt để (40 → 0 chuỗi)
- Latency giảm 10%

**Tuy nhiên** — và đây là phần quan trọng nhất để TRUNG THỰC trong luận văn:

> Sprint 2 fixes làm LLM C trở thành **"Sleep agent thuần"** — không hành động chủ động nào trong 500 step. Reward -585 cao hơn A -660 là vì **chiến lược Sleep tự nhiên có chi phí thấp hơn chiến lược Restore khi observation không có IOC**, không phải vì MCP+RoE phòng thủ tốt hơn.

> Đây không phải kết quả "MCP+RoE thắng TH3 baseline". Đây là kết quả "MCP+RoE chọn Sleep, may mắn trùng với chiến lược tối ưu cho observation evolution cụ thể này".

**Sprint 3 cần**:
1. Điều chỉnh prompt để LLM cân bằng Sleep và proactive
2. Test với synthetic IOC để verify MCP+RoE work khi có threat thật
3. Chạy n=5 cho variance
4. Verify reproducibility

**Học từ Sprint 2**:

| Bài học | Áp dụng cho |
|---|---|
| Khi LLM được cho tool "easy way out" (Sleep), nó sẽ lạm dụng | Tool design phải có cấu trúc khuyến khích, không chỉ permit |
| `recommended_action` priority="low" vẫn quá mạnh — LLM coi như lệnh | Prompt cần làm rõ priority "low" = optional |
| Cùng seed nhưng env evolve khác giữa setup → khó so trực tiếp | Cần synthetic obs hoặc fixed trajectory để control |
| Thành công về reward + thất bại về hành vi → cần đánh giá đa chiều | Không chỉ M1 reward, cần thêm action diversity, proactive rate, etc. |

---

*Báo cáo dựa hoàn toàn vào (1) JSONL artifact `detailed_C_FiniteState_ep0.jsonl` (8980 events) + `joint_reward_C_FiniteState_ep0.json`, (2) backup Sprint 1 `*_sprint1.*`, (3) Setup A baseline. Mọi số liệu trace ngược về file gốc. Báo cáo này cố ý trung thực — không che giấu các nghịch lý phát hiện qua phân tích.*
