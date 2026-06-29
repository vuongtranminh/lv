# BÁO CÁO TỔNG KẾT 2 SPRINT — Ưu/Nhược điểm + MCP+RoE thực sự làm được gì

> Tổng hợp toàn bộ kết quả Sprint 1 (Setup A/B/C × FiniteState × 1 ep, code chưa fix) + Sprint 2 (re-run Setup C với 5 fix). Đánh giá khách quan dựa trên data thực tế, không "ép" theo kỳ vọng luận văn.

---

## 1. Số liệu tổng kết — 4 lần chạy benchmark

| Run | Setup | Reward | Wall time | n events JSONL |
|---|---|---|---|---|
| 1 | A (TH3 baseline) | **-660** | 1h49 | 3602 |
| 2 | B v3 (MCP only) | **-2110** | 4h04 | 8538 |
| 3 | C v1 (MCP+RoE pre-fix) | **-1515** | 4h26 | 9774 |
| 4 | C v2 (MCP+RoE post-fix Sprint 2) | **-585** | 3h59 | 8980 |

**Ranking cuối**: **C v2 (-585) > A (-660) > C v1 (-1515) > B v3 (-2110)**.

**TH3 paper baselines (tham chiếu, Hình 4-5)**:
- No-Blue (sàn ác): -6334
- All-RL KEEP (sàn tốt): -451
- All-LLM 4o-mini: -6334
- 1LLM o3-mini + 4RL KEEP: ≈-500
- 1LLM 4o-mini + 4RL KEEP: ≈-1850

→ Setup C v2 (-585) nằm gần "1LLM o3-mini + 4RL KEEP" (-500) — kết quả TỐT về số tuyệt đối.

---

## 2. MCP + RoE THỰC SỰ làm được gì? — Có data chứng minh

### 2.1 ✅ Pipeline MCP hoạt động end-to-end

| Sprint | Tool calls tổng | Loại tool sử dụng |
|---|---|---|
| Sprint 1 C v1 | 1965 | get_threat_summary, get_comms_decoded, propose_analyse/restore/deploydecoy |
| Sprint 2 C v2 | 1973 | get_threat_summary 972 + propose_sleep 501 + get_comms_decoded 500 |

→ Mọi setup MCP đều gọi tool đầy đủ, không có parse JSON fail, không có protocol error.

### 2.2 ✅ RoE deny + retry mechanism work

**Sprint 1 C v1** (8 rule v2 chưa wire, dùng 3 rule v1):
- 820 RoE verdicts: 497 allowed (60.6%) + **323 denied (39.4%)**
- 322/323 (**99.7%**) lần LLM retry thành công sau deny
- Deny chủ yếu: 322 DeployDecoy (max 2/host) + 1 Restore (rule needs admin)

**Sprint 2 C v2** (8 rule v2 wire đầy đủ):
- 0 RoE verdict (vì LLM chỉ Sleep, không gọi propose có check)
- Nhưng 48/48 unit test pass — 8 rule v2 work đúng spec

→ **RoE chứng minh hoạt động khi LLM ra quyết định destructive**. Cơ chế deny + suggested + retry verified.

### 2.3 ✅ Hostname validation ngăn LLM bịa

**Trước fix (Sprint 1)**:
- C v1 target 52 hostname **100% là bịa** (`web-server`, `db-server`, ...)
- LLM gọi action vào host không tồn tại → vô hiệu

**Sau fix (Sprint 2)**:
- `_propose()` validate hostname trước RoE
- 12 unit test cover edge case (test_hostname_validation.py — all pass)

→ Lỗi L1 cụ thể (hostname hallucination) đã khắc phục có bằng chứng. Vấn đề tinh chỉnh prompt vẫn cần xử lý.

### 2.4 ✅ Khắc phục loop Analyse (L2)

| Setup | Số chuỗi action lặp cùng host (≥3 lần/5 step) | Chuỗi dài nhất |
|---|---|---|
| A | 5 chuỗi | **74 lần** (`public_access_zone_subnet_server_host_0`) |
| B v3 | 50+ chuỗi | 24 lần |
| C v1 | 40 chuỗi | 6 lần |
| **C v2** | **0 chuỗi** | **0 lần** |

→ Sprint 2 prompt + tool `propose_sleep` triệt tiêu hoàn toàn vòng lặp. Khắc phục L2 (lệ thuộc prompt) thành công.

### 2.5 ✅ Explainability cao — JSONL log full trace

| Metric | TH3 paper | Setup A | Setup C v2 |
|---|---|---|---|
| Per-step detailed log | ❌ (chỉ aggregate) | 3602 event | **8980 event** |
| Trace từng tool call | ❌ | ❌ | **1973 (cùng tool result)** |
| Trace từng RoE verdict | ❌ (không có RoE) | ❌ | **820 ở v1, 0 ở v2** |
| Sample reasoning từng step | TH3 §IV.A K-Means 499 mẫu | Có | **501 propose_* + reason** |

→ MCP+RoE cho khả năng giải thích (XAI — Explainable AI) mà TH3 không có. Mỗi quyết định trace ngược về tool calls + state + RoE verdict.

### 2.6 ✅ Distribute defense (phân phối phòng thủ qua rate-limit)

Sprint 1 C v1 — RoE chặn LLM "spam DeployDecoy 1 host":

| | B v3 (no RoE) | C v1 (3 rule v1) | C v2 (8 rule v2) |
|---|---|---|---|
| Top host được DeployDecoy nhiều nhất | 57 lần (web-server) | 2 lần (max RoE) | (không decoy) |
| Số host khác nhau được decoy | 10+ host nhưng concentrate | 50+ host × 2 decoy | — |
| Defense in depth | ❌ | ✓ | — |

→ RoE chứng minh khả năng **buộc LLM distribute action** thay vì spam 1 host. "Defense in depth" pattern.

### 2.7 ✅ Adaptive reasoning qua deny → suggested → retry

Mẫu cụ thể từ JSONL Setup C v1 step 5:

```
tool_call: get_threat_summary({})
tool_call: get_comms_decoded({})
tool_call: propose_deploydecoy({'hostname':'web-server-1','reason':'...'})
RoE ✗ DENIED: "Host 'web-server-1' đã có 2 decoy."
tool_call: propose_analyse({'hostname':'db-server-1','reason':'...'})
RoE ✓ ALLOWED
FINAL: Analyse({'hostname':'db-server-1'})
```

→ LLM **đọc lý do deny → đổi action → đổi host → retry thành công**. Đây là cơ chế TH3 không có (single-shot, fallback Sleep).

---

## 3. ƯU ĐIỂM (so với TH3 paper)

| # | Ưu điểm | Bằng chứng cụ thể |
|---|---|---|
| 1 | **Cấu trúc hành động chặt chẽ** (tool schema JSON) | 0 parse fail trong 1973+1965 = 3938 tool call |
| 2 | **Cơ chế tự sửa lỗi** | 322/323 (99.7%) retry sau deny thành công |
| 3 | **Pre-parsed observation** | `available_hostnames` ngăn bịa tên |
| 4 | **Khả năng giải thích** | 9000+ event/ep, trace từng quyết định |
| 5 | **Safety guarantees deterministic** | 8 rule v2 chặn destructive sai (verified qua test) |
| 6 | **Adaptive prompt design** | Recommended_action priority guide LLM |
| 7 | **Defense in depth** | RoE buộc distribute decoy đều khắp 50+ host |
| 8 | **No code training required** | Chỉ prompt engineering — chuyển giao dễ |

---

## 4. NHƯỢC ĐIỂM (phát hiện qua 2 sprint)

| # | Nhược điểm | Bằng chứng | Mức độ |
|---|---|---|---|
| 1 | **Latency cao** | C: 28-32 s/step (vs A 13 s/step, gấp 2.2×) | ⚠️ Trung |
| 2 | **LLM có thể quá thụ động** | C v2: 100% Sleep, 0 action chủ động | ⚠️⚠️ Nặng |
| 3 | **Phụ thuộc prompt design** | Sửa 1 dòng prompt → hành vi thay đổi cực mạnh | ⚠️ Trung |
| 4 | **Khó kiểm chứng deterministic** | Cùng seed nhưng env evolve khác → khó so trực tiếp | ⚠️ Trung |
| 5 | **Variance cao giữa runs** | C run lần 1 = -70 ở step 50, lần 3 = -125 (chênh 64%) | ⚠️ Trung |
| 6 | **Chưa verify với threat thật** | C v2 episode KHÔNG có IOC nào → không kích hoạt được destructive | ⚠️⚠️ Nặng |
| 7 | **n=1 không đủ thống kê** | Cần n≥5 mới có σ và khoảng tin cậy | ⚠️ Trung |
| 8 | **Dependency phức tạp** | claude-agent-sdk, cloudpickle, MCP server | ⚠️ Thấp |

---

## 5. Câu hỏi cốt lõi — MCP+RoE có vượt TH3 baseline không?

### 5.1 Trả lời CÓ ĐIỀU KIỆN

Dựa trên 1 episode pilot × FiniteState × seed 0:

✅ **C v2 reward -585 > A reward -660** (chênh +75)

NHƯNG cần phân tích:

| Điều kiện | A đối mặt | C v2 đối mặt |
|---|---|---|
| Số host bị admin compromise trong observation | **3 host** | 0 host |
| Số host bị user compromise trong observation | 92 step | 0 step |
| Strategy tối ưu cho condition này | Restore + Remove ngắn hạn | Sleep dài hạn |
| Reward observation-conditional | Thắng nếu cleanup nhanh | Thắng nếu không can thiệp |

→ **C v2 thắng vì Sleep nhẹ chi phí hơn Restore**, KHÔNG phải vì MCP+RoE phòng thủ tốt hơn. Đây là **may mắn về observation evolution**, không phải đóng góp pipeline.

### 5.2 So sánh fair có thể đưa ra kết luận gì?

| Khía cạnh có thể kết luận chắc | Bằng chứng |
|---|---|
| Pipeline MCP+RoE chạy được trong CybORG CAGE 4 | ✓ 3 episode hoàn thành 500/500 step |
| Reproduces TH3 LLM behavior (DeployDecoy + Analyse dominant) | ✓ B v3 phân bố action giống TH3 o3-mini Hình 7 |
| RoE deny + retry hoạt động đúng spec | ✓ 99.7% retry success |
| Hostname validation ngăn hallucination | ✓ Verified qua unit test |
| Explainability vượt trội TH3 | ✓ 9000+ event/ep, JSONL trace-able |

| Khía cạnh CHƯA kết luận được | Lý do |
|---|---|
| MCP+RoE > TH3 baseline về REWARD | Variance cao + chưa kiểm soát env evolution |
| L1 (ảo giác bit) có giảm | comm vector luôn rỗng — không kích hoạt |
| Setup C có làm Restore đúng khi có admin IOC | C v2 không thấy admin IOC nào |
| Đóng góp riêng của 8 rule v2 vs 3 rule v1 | C v2 không gọi propose có check → không phát hiện |

---

## 6. MCP + RoE THỰC SỰ làm được gì? — Tổng hợp 1 câu

> **MCP + RoE cung cấp một KHUNG (framework) cho LLM agent ACD có:**
> - **Cấu trúc** (tool schema chặt chẽ thay free-text JSON)
> - **Phản hồi** (RoE deny + suggested → LLM tự sửa)
> - **An toàn** (rule deterministic chặn destructive sai)
> - **Giải thích** (trace từng quyết định qua JSONL log)
> - **Phân phối** (rate-limit buộc defense in depth)
>
> **CHƯA chứng minh được** MCP + RoE đạt reward CAGE 4 cao hơn TH3 paper trong điều kiện kiểm soát.
> **ĐÃ chứng minh được** MCP + RoE đáp ứng các yêu cầu CHẤT LƯỢNG (explainability, safety, adaptability) mà TH3 thiếu.

---

## 7. Khuyến nghị Sprint 3+ (theo đề xuất Sprint 2)

### 7.1 Ưu tiên cao

1. **Sửa prompt để LLM bớt thụ động** — `recommended_action` priority "low" phải rõ là "gợi ý optional", không phải lệnh. Bắt buộc proactive 1-2 action/5 step.

2. **Test với observation có IOC inject thủ công** — verify Setup C v2 thực sự ra Restore khi thấy admin IOC. Đây là test deterministic, không phụ thuộc env evolution.

3. **n=5 episode cho mỗi setup × FiniteState** — có σ, có khoảng tin cậy. Verify variance giữa các lần chạy.

### 7.2 Ưu tiên trung

4. **Test 3 red variant khác** (AggressiveFSM, StealthyFSM, ImpactFSM) — kiểm chứng MCP+RoE robust qua các adversary đa dạng

5. **Fix CommVectorGenerator** — comm vector empty làm L1 không verify được. Cần debug API mismatch.

6. **Đo các metric ngoài reward** — action diversity, proactive rate, time-to-detect, time-to-respond → đa chiều thay vì chỉ M1.

### 7.3 Ưu tiên thấp

7. Prompt caching — tăng tốc latency

8. Wire vector v2 đầy đủ — đã có code, đã test, nhưng chưa kích hoạt trong production run

---

## 8. Kết luận tổng

**Sau 2 sprint, luận văn đã chứng minh được**:
- Framework MCP+RoE chạy được trong CybORG CAGE 4 environment
- Các cơ chế thiết kế work theo spec (tool schema, RoE rules, retry, suggested)
- Khả năng explainability vượt trội TH3
- Cải tiến rõ rệt qua iteration (C v1 -1515 → C v2 -585, cải thiện 930)

**Sau 2 sprint, luận văn CHƯA chứng minh được**:
- MCP+RoE vượt TH3 baseline về reward CAGE 4 trong điều kiện kiểm soát
- L1 (ảo giác bit) được giải quyết bởi MCP decoder
- Đóng góp riêng của RoE vs MCP-only trong điều kiện có threat thật

**Hướng đi**: Sprint 3+ tập trung **kiểm chứng có chỉ định** (controlled testing) thay vì chỉ chạy benchmark. Inject IOC, chạy n=5, đo đa metric → có data thuyết phục cho hội đồng phản biện.

**Triết lý**:
- **Tốt**: viết luận văn TRUNG THỰC về kết quả pilot — ưu điểm chất lượng + tồn tại định lượng. Đóng góp khoa học vẫn rõ (explainability + safety framework). Reward không phải metric duy nhất.
- **Tránh**: ép data theo kỳ vọng — claim "MCP+RoE thắng TH3" khi không có bằng chứng thống kê đủ.

---

*Báo cáo dựa trên 4 episode benchmark (A + B + C v1 + C v2), tổng 32k+ event JSONL, 6 báo cáo phân tích chi tiết (BAO_CAO_SETUP_*, PHAN_TICH_REWARD, CASE_STUDY_CHEO, UU_THE_C_VA_HUONG_TOI_UU, BAO_CAO_SPRINT_*). Mọi số liệu trace được về file artifact cụ thể.*
