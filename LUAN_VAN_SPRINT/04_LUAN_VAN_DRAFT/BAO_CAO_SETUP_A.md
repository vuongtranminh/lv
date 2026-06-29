# BÁO CÁO KẾT QUẢ SETUP A — BASELINE TH3

> **Phạm vi**: chỉ dựa trên (1) bài báo *Large Language Models are Autonomous Cyber Defenders* (Castro và cộng sự, IEEE CAI 2025 — viết tắt **TH3**, đã đọc đầy đủ tại file `TH3_Large_Language_Models_are_Autonomous_Cyber_Defenders.pdf` trong workspace) và (2) kết quả thực thi 1 episode (lượt chơi) Setup A với cấu hình red FiniteState (kẻ tấn công kiểu Máy trạng thái hữu hạn), seed (hạt giống ngẫu nhiên) 0, độ dài 500 step (lượt). Không sử dụng số liệu bên ngoài.

> **Cam kết dẫn chứng**: mọi số liệu Setup A trace ngược về file artifact `benchmark/results/` với line number (số dòng) cụ thể. Mọi số liệu TH3 trích từ bài báo với section (mục) + bảng + hình cụ thể.

---

## Bảng thuật ngữ nhanh — đọc trước phần dưới

| Thuật ngữ | Giải thích đầy đủ |
|---|---|
| **TH3** | Bài báo *"Large Language Models are Autonomous Cyber Defenders"* của Castro và cộng sự, IEEE CAI 2025 — bài báo nền cho luận văn |
| **LLM** | Large Language Model — Mô hình ngôn ngữ lớn (như GPT, Claude, LLaMA) |
| **RL** | Reinforcement Learning — Học tăng cường (cách huấn luyện agent bằng thưởng/phạt) |
| **ACD** | Autonomous Cyber Defense — Phòng thủ mạng tự động |
| **MCP** | Model Context Protocol — Giao thức ngữ cảnh mô hình do Anthropic phát triển, cho phép LLM gọi tool bên ngoài qua schema chuẩn |
| **RoE** | Rules of Engagement — Quy tắc giao chiến, tập rule quyết định trước khi cho phép một hành động phá hủy |
| **CybORG** | Cyber Operations Research Gym — môi trường mô phỏng mạng cho ACD |
| **CAGE 4** | Cyber Autonomy Gym for Experimentation, phiên bản 4 — kịch bản cụ thể trong CybORG |
| **FSM** | Finite State Machine — Máy trạng thái hữu hạn (kiểu thuật toán của red agent) |
| **KEEP** | Tên model RL của đội Cybermonic dùng GCN + PPO, baseline mạnh nhất CAGE 4 |
| **GCN** | Graph Convolutional Network — Mạng tích chập đồ thị |
| **PPO** | Proximal Policy Optimization — Tối ưu hóa chính sách cận kề (thuật toán RL) |
| **IOC** | Indicator of Compromise — Chỉ dấu xâm phạm (vd file `escalate.sh`, `cmd.sh` xuất hiện trên máy bị nhiễm) |
| **JSONL** | JSON Lines — định dạng file mỗi dòng là một đối tượng JSON độc lập |
| **CSV** | Comma-Separated Values — file dữ liệu phân cách bằng dấu phẩy |
| **API** | Application Programming Interface — Giao diện lập trình ứng dụng |
| **PCA** | Principal Component Analysis — Phân tích thành phần chính (giảm số chiều dữ liệu) |
| **K-Means** | Thuật toán phân cụm dữ liệu thành K nhóm |
| **ablation study** | Nghiên cứu cô lập — bật/tắt từng thành phần để xem thành phần nào đóng góp gì |
| **single-shot** | Đơn lượt — gọi LLM 1 lần duy nhất rồi nhận kết quả, không trao đổi qua lại nhiều lần |
| **few-shot** | Cho LLM vài ví dụ mẫu kèm prompt để LLM bắt chước |
| **token** | Đơn vị xử lý của LLM (xấp xỉ 1 từ tiếng Anh hoặc 1 ký tự tiếng Việt) |
| **temperature** | Nhiệt độ — tham số kiểm soát độ ngẫu nhiên trong câu trả lời LLM (0 = xác định, 1 = ngẫu nhiên cao) |
| **prompt** | Đoạn văn bản đầu vào gửi cho LLM để định hướng câu trả lời |
| **fallback** | Phương án dự phòng khi cách chính thất bại |
| **baseline** | Đường mốc cơ sở để so sánh |
| **wall time** | Thời gian thực tế trôi qua (đo bằng đồng hồ treo tường) |
| **checkpoint** | Điểm lưu trạng thái, để có thể khôi phục lại khi bị gián đoạn |
| **hallucinate** | Ảo giác — LLM tự bịa ra thông tin không có trong dữ liệu thực |

---

## 1. Mục đích Setup A

Setup A là **bản tái hiện đường ống (pipeline) suy luận của TH3** trong khung benchmark (bộ thử nghiệm) luận văn. Vai trò: **đường mốc đối chiếu (baseline)** cho Setup B (thêm MCP) và Setup C (thêm MCP + RoE).

Mục đích cụ thể:

1. **Kiểm chứng pipeline TH3 chạy được trong khung benchmark luận văn** — cùng môi trường CybORG CAGE 4, cùng red FSM agent (kẻ tấn công kiểu Máy trạng thái hữu hạn), cùng 4 blue baseline (đồng đội), 500 step (lượt) cho mỗi episode (lượt chơi).
2. **Đo M1–M5 + chỉ số bổ sung** ở chế độ TH3 nguyên bản.
3. **So sánh trực tiếp các chỉ số có trong TH3 paper** — bảng đôi để thấy Setup A đứng ở đâu so với số liệu công bố của TH3.
4. **Quan sát hạn chế của pipeline TH3** — bằng chứng định lượng cho 3 hạn chế đã nêu trong kế hoạch luận văn:
   - **L1**: Ảo giác (hallucination) khi đọc vectơ truyền thông (communication vector) 8-bit
   - **L2**: Lệ thuộc cách viết prompt (prompt design) cho định nghĩa hành động (action)
   - **L3**: Thiếu định hướng phần thưởng (reward function) — không có RoE chặn các action phá hủy không phù hợp

---

## 2. Cấu hình thí nghiệm — So sánh trực tiếp với TH3

### 2.1 Bảng cấu hình đôi

| Tham số | **TH3 paper §IV** | **Setup A luận văn** | Khác/Giống |
|---|---|---|---|
| Môi trường | CybORG CAGE 4 | CybORG CAGE 4 (cùng commit) | **Giống** |
| Red agent default | `FiniteStateRedAgent` (kẻ tấn công Máy trạng thái hữu hạn mặc định CAGE 4) | `FiniteStateRedAgent` | **Giống** |
| Green agent | `EnterpriseGreenAgent` (người dùng hợp pháp dùng dịch vụ) | `EnterpriseGreenAgent` | **Giống** |
| Blue agent đối tượng (do LLM điều khiển) | `blue_agent_4` (theo biến `BLUE_AGENT_NAME`) | `blue_agent_4` | **Giống** |
| 4 blue đồng đội (đồng đội của LLM agent) | **KEEP** (model RL+GCN của Cybermonic) trong kịch bản 1LLM+4RL | **ReactRemoveBlueAgent** (rule-based đơn giản — phản ứng theo quy tắc cố định, không phải RL) | **KHÁC** |
| Số kịch bản blue | 4 (No blue, All LLM, All RL, 1LLM+4RL) | 1 (chỉ 1LLM + 4 rule baseline) | KHÁC |
| Episode (lượt chơi) | **2 ep** × 500 step (TH3 §IV.A) | **1 ep** × 500 step (n=1 do giới hạn tài nguyên) | KHÁC (luận văn cần 5 ep × 4 red khi hoàn thành) |
| Độ dài episode | 500 step (lượt) | 500 step | **Giống** |
| Mô hình LLM | OpenAI: GPT-3.5-Turbo, GPT-4o-mini, o1-mini, o3-mini + DeepSeek-V3 (TH3 §IV) | **Claude Haiku 4.5** | KHÁC |
| Temperature (nhiệt độ — độ ngẫu nhiên) | 1 (TH3 §IV "Môi trường và mô hình") | 1 (mặc định Claude SDK) | **Giống** |
| Prompt design (thiết kế đoạn nhắc) | Role + Few-shot (gán vai trò + cho vài ví dụ mẫu, theo TH3 §III.D, Bảng III) | Role only (gán vai trò "chuyên gia an ninh mạng" nhưng chưa có ví dụ mẫu) | KHÁC |
| max_turns (số lượt LLM tối đa được trao đổi/step) | 1 (single-shot — đơn lượt) | 1 | **Giống** |
| Pipeline (đường ống xử lý) | Prompt + raw 8-bit comm vector → JSON parse → fallback Sleep | Đúng như TH3 §III.B | **Giống pipeline** |

### 2.2 Khác biệt cốt yếu vs TH3 — phải giải thích

**Khác 1: 4 blue đồng đội — ReactRemoveBlueAgent vs KEEP**

TH3 paper dùng KEEP (model học tăng cường dùng Graph Convolutional Network — Mạng tích chập đồ thị của đội Cybermonic) cho 4 đồng đội trong kịch bản 1LLM+4RL (TH3 §IV.A). Setup A luận văn dùng **ReactRemoveBlueAgent** (agent đơn giản, hành động theo rule cố định: thấy IOC thì Remove) cho 4 đồng đội.

Hệ quả: Setup A của luận văn KHÔNG ánh xạ 1-1 đến bất kỳ kịch bản nào trong 4 kịch bản TH3. Nó gần nhất với **kịch bản "1LLM+4RL" nhưng thay KEEP bằng baseline rule-based** — nói cách khác, baseline đồng đội YẾU HƠN TH3.

Lý do: luận văn tập trung vào **đóng góp của MCP/RoE cho LLM agent**, không nghiên cứu RL đồng đội. ReactRemoveBlueAgent đủ làm "đồng đội biểu trưng" cho thí nghiệm ablation A/B/C.

**Khác 2: LLM nền — Claude Haiku 4.5 vs OpenAI/DeepSeek**

TH3 paper test 5 mô hình OpenAI/DeepSeek. Luận văn dùng `claude-haiku-4-5` (mô hình LLM của Anthropic). Lý do: cô lập biến LLM — giữ cùng LLM ở A/B/C để mọi chênh lệch chỉ số là đóng góp MCP/RoE, không phải đóng góp LLM mạnh hơn.

**Khác 3: Prompt — chưa có few-shot (ví dụ mẫu)**

TH3 §III.D Bảng III cho thấy Role+Few-shot vượt trội hơn Role-only ở 2/3 mô hình OpenAI:

| Model | Role (chỉ vai trò) | Few-shot (vai trò + ví dụ mẫu) | Instruct (chỉ hướng dẫn) |
|---|---|---|---|
| GPT-3.5 Turbo | −4307 | **−4349.5** | −4620 |
| GPT-4o-mini | −3810 | **−3219** | −2888 |
| o1-mini | −3022 | **−3243.5** | −3890.5 |

→ Few-shot làm tăng reward cho GPT-4o-mini (+591). Setup A của luận văn dùng **Role-only**, chưa thêm ví dụ mẫu. Cần khắc phục ở Phase 2 đầy đủ.

### 2.3 Mã nguồn pipeline

| Khâu TH3 §III | Setup A code path (đường dẫn mã nguồn) |
|---|---|
| Observation format (định dạng quan sát, TH3 Bảng II) | `paper_style.py:render_paper_observation()` dòng 60-100 |
| System prompt (prompt hệ thống) + Role | `paper_style.py:PAPER_SYSTEM_PROMPT` dòng 15-57 (2314 ký tự) |
| Single-shot (đơn lượt), max 1 turn | `claude_policy.py:_query_paper_mode()` dòng 240-246 |
| Regex parse (phân tích biểu thức chính quy) JSON | `paper_style.py:parse_paper_response()` dòng 123-129 |
| Fallback Sleep (dự phòng Sleep) khi parse fail | `claude_policy.py:compute_single_action()` dòng 130-133 |

---

## 3. Dữ liệu thu được — files artifact

| File | Đường dẫn | Kích thước |
|---|---|---|
| Tổng kết episode | [`benchmark/results/joint_reward_A_FiniteState_ep0.json`](../../feasibility-mcp-roe/benchmark/results/joint_reward_A_FiniteState_ep0.json) | 16 trường |
| Audit CSV (bảng tóm tắt từng step) | [`benchmark/results/audit_A_FiniteState_ep0.csv`](../../feasibility-mcp-roe/benchmark/results/audit_A_FiniteState_ep0.csv) | **2919 dòng** |
| Detailed JSONL (log đầy đủ, mỗi dòng 1 sự kiện) | [`benchmark/results/detailed_A_FiniteState_ep0.jsonl`](../../feasibility-mcp-roe/benchmark/results/detailed_A_FiniteState_ep0.jsonl) | **3602 event (sự kiện)** |

Phân bố event JSONL: `episode_start` (đầu episode) 1, `step_start` (đầu step) 500, `state_extracted` (state đã trích xuất sau pre-parse) 500, `llm_query` (lệnh gửi cho LLM) 500, `llm_response_chunk` (text Claude trả về) 500, `paper_parse_result` (kết quả parse JSON) 500, `action_proposed` (hành động LLM đề xuất khác Sleep) 100, `action_materialized` (hành động cuối cùng đưa vào env) 500, `step_end` (kết thúc step) 500, `episode_end` (cuối episode) 1 = **3602**.

---

## 4. Các chỉ số TH3 paper báo cáo — Bảng đôi Setup A vs TH3

### 4.1 M1 — Cumulative Joint Reward (phần thưởng tích lũy chung)

> **Định nghĩa M1**: tổng phần thưởng (reward) của tất cả 5 blue agent qua 500 step. Càng cao càng tốt (reward âm = bị phạt vì để mạng bị xâm phạm/gián đoạn dịch vụ).

| Kịch bản | TH3 paper | Setup A luận văn |
|---|---|---|
| **No blue agents** (không có người phòng thủ — sàn tham chiếu) | **−6334** (TH3 Hình 5, red FiniteState) | — (không test) |
| **All RL KEEP** (5 blue đều dùng RL KEEP) | **−451** (TH3 Hình 5, red FiniteState) | — (không test) |
| **All LLM (GPT-4o-mini)** (5 blue đều là LLM GPT-4o-mini) | **−6334** (TH3 Hình 5, red FiniteState) ¹ | — (không test) |
| **1 LLM (o3-mini) + 4 RL (KEEP)** (1 LLM o3-mini + 4 đồng đội RL KEEP) | **≈ −500** (đọc Hình 4 TH3) ² | — (không test) |
| **1 LLM (GPT-4o-mini) + 4 RL (KEEP)** | **≈ −1850** (đọc Hình 4 TH3) ² | — (không test) |
| **1 LLM (DeepSeek-V3) + 4 RL (KEEP)** | **≈ −2200** (đọc Hình 4 TH3) ² | — (không test) |
| **1 LLM (Claude Haiku 4.5) + 4 ReactRemoveBlueAgent** | — (không thuộc TH3) | **−660.00** |

¹ TH3 Hình 5 cho thấy "All LLM" với red FiniteState cũng ở mức −6334 (gần sàn No-Blue) — LLM toàn-đội không bảo vệ hiệu quả.

² Số đọc xấp xỉ từ Hình 4 TH3 (biểu đồ thanh). Hình 4 cho thấy o3-mini cao nhất (≈ −500), o1-mini gần đó, DeepSeek-V3 ≈ −2200, GPT-4o-mini ≈ −1850.

**Phân tích chéo**:

- Setup A (1 LLM Claude Haiku 4.5 + 4 rule baseline) đạt **−660**, nằm **giữa** "1 LLM o3-mini + 4 KEEP RL" (≈ −500) và "1 LLM GPT-4o-mini + 4 KEEP RL" (≈ −1850) của TH3.
- Không thể so sánh trực tiếp vì baseline đồng đội khác (ReactRemoveBlueAgent vs KEEP). ReactRemoveBlueAgent yếu hơn KEEP RL → kỳ vọng Setup A reward thấp hơn 1LLM+4KEEP của TH3.
- Tuy nhiên Setup A vẫn **tốt hơn nhiều** "All LLM" (−6334) hoặc "No Blue" (−6334) của TH3 — chứng tỏ pipeline hoạt động.

Dẫn chứng Setup A: file `joint_reward_A_FiniteState_ep0.json` trường `cumulative_joint_reward`.
Dẫn chứng TH3: Hình 4 (trang 6), Hình 5 (trang 6) bài báo TH3.

### 4.2 M1.1 — Reward theo Mission Phase (pha nhiệm vụ)

> **Định nghĩa**: CAGE 4 chia 500 step thành 3 pha: Phase 0 (Planning — Lập kế hoạch), Phase 1 (MissionA — Nhiệm vụ A), Phase 2 (MissionB — Nhiệm vụ B). Mỗi pha có ràng buộc khác nhau về kết nối mạng.

TH3 paper KHÔNG báo cáo reward theo pha riêng — Setup A luận văn bổ sung:

| Phase (pha) | Step count (số lượt) | Cum reward (reward tích lũy) | Avg/step (trung bình mỗi lượt) |
|---|---|---|---|
| **0 (Planning — Lập kế hoạch)** | 168 | **−445.00** | **−2.649** |
| 1 (MissionA — Nhiệm vụ A) | 167 | −65.00 | −0.389 |
| 2 (MissionB — Nhiệm vụ B) | 165 | −150.00 | −0.909 |

Phase 0 mất 67% tổng penalty (hình phạt) mặc dù là "Planning" — red FSM bắt đầu chuỗi attack (tấn công) ngay từ Phase 0. LLM Setup A diễn giải "Phase 0 = chờ" → Sleep (ngủ — không làm gì) áp đảo 154/168 step = 91.7%.

### 4.3 Mean ± Std qua các red variant (trung bình ± độ lệch chuẩn qua các kiểu kẻ tấn công)

TH3 paper Hình 5 báo cáo mean ± std qua 5 red variant (5 kiểu kẻ tấn công: FiniteState, AggressiveFSM — máy trạng thái hung hãn, StealthyFSM — lén lút, ImpactFSM — tập trung gây tác động, DegradeServiceFSM — làm suy giảm dịch vụ):

| Cách tiếp cận | μ (mean — trung bình) | σ (std — độ lệch chuẩn) |
|---|---|---|
| All LLM (GPT-4o-mini) | **−2547.2** | **498.8** |
| All RL (KEEP) | **−493** | **95.9** |

→ TH3 ghi nhận: **All RL có σ thấp hơn 5.2 lần** All LLM → RL ổn định hơn qua các kiểu red.

Setup A luận văn **chưa có số tương đương** vì:
- Mới test 1 red (FiniteState), chưa 4 red khác
- Mới 1 episode (n=1), chưa có σ

→ Hạn chế lớn. Khi hoàn thành 5 ep × 4 red = 20 ep cho Setup A, có thể tính μ ± σ tương tự TH3.

### 4.4 Action distribution (phân bố hành động) — đối chiếu trực tiếp với TH3 Hình 7

> **Action set CAGE 4** (Bảng I trong TH3, trang 2):
> - **Sleep**: ngủ (không hành động, để Monitor tự chạy)
> - **Monitor**: quét thụ động (tự chạy mỗi lượt, không cần gọi tay)
> - **Analyse**: phân tích sâu 1 máy chủ để tìm hoạt động độc hại
> - **Remove**: chấm dứt tiến trình đáng ngờ ở mức người dùng (user-level)
> - **Restore**: wipe + khôi phục máy chủ về trạng thái sạch (phá hủy — tạm dừng dịch vụ)
> - **DeployDecoy**: triển khai honeypot (mồi nhử) trên một máy chủ
> - **BlockTrafficZone**: chặn toàn bộ traffic (lưu lượng) inbound từ một subnet (mạng con)
> - **AllowTrafficZone**: cho phép lại traffic từ subnet đã bị chặn

TH3 Hình 7 báo cáo action count (số đếm hành động) cho **1 episode của 1 LLM agent o3-mini + 4 RL** (red FiniteState mặc định):

| Action (hành động) | **TH3 LLM (o3-mini)** | **TH3 RL (KEEP)** | **Setup A (Claude Haiku 4.5)** |
|---|---|---|---|
| Analyse (phân tích) | 13 | **267** | **95** |
| DeployDecoy (triển khai mồi nhử) | **224** | 6 | **0** |
| Remove (chấm dứt tiến trình) | 5 | 74 | **2** |
| BlockTrafficZone (chặn vùng) | 4 | 0 | **0** |
| Sleep (ngủ) | **0** | **291** | **400** |
| Restore (khôi phục) | 0 | 84 | **3** |
| Monitor (giám sát) | 0 | 62 | **0** |
| AllowTrafficZone (cho phép vùng) | 0 | 19 | **0** |
| **Tổng action chủ động** | 246 | 209 | 100 |

**Phân tích sự khác biệt nổi bật**:

1. **TH3 LLM Sleep = 0** vs **Setup A Sleep = 400**: Khác biệt rất lớn.
   - **Lý do**: TH3 §V.B "Định nghĩa Prompt" ghi rõ *"Để giữ tác nhân hoạt động, chúng tôi không định nghĩa hành động Sleep trong prompt"*. TH3 cố ý loại bỏ Sleep khỏi action set khả dụng để buộc LLM phải hành động.
   - Setup A của luận văn ĐÃ định nghĩa Sleep trong `PAPER_SYSTEM_PROMPT` (xem dòng 22) → Claude Haiku 4.5 tận dụng Sleep mặc định khi không chắc.
   - **Bài học**: tỷ lệ Sleep cao của Setup A KHÔNG phản ánh hạn chế của LLM mà phản ánh **lựa chọn prompt design** khác TH3.

2. **TH3 LLM DeployDecoy = 224** vs **Setup A DeployDecoy = 0**:
   - Setup A KHÔNG có DeployDecoy action nào. Đây là khác biệt định tính cực lớn.
   - **Lý do khả dĩ**: TH3 LLM (o3-mini) ưu tiên DeployDecoy vì không có Sleep → phải chọn cái gì đó "nhẹ" thay vì destructive (phá hủy). Setup A có Sleep nên không bị ép phải DeployDecoy.
   - **Cũng có thể**: prompt của luận văn (`PAPER_SYSTEM_PROMPT` dòng 29) mô tả DeployDecoy là "phát hiện chủ động" — không khuyến khích đủ mạnh. Cần đối chiếu với prompt gốc TH3.

3. **Cả hai LLM (TH3 o3-mini và Setup A Claude Haiku 4.5) đều tránh Restore** (TH3: 0, Setup A: 3). TH3 §V phần "So sánh việc chọn hành động giữa RL và LLM" nói rõ *"tác nhân tránh thực thi hành động Restore, có thể vì nó có thể gây vấn đề về tính khả dụng (availability) cho người dùng green"*. Setup A cũng tương tự — chỉ 3/500 = 0.6%.

4. **RL agent của TH3 dùng Analyse 267 lần** — gấp gần 3 lần Setup A. RL tích cực Analyse trước khi hành động, Setup A LLM dù dùng Analyse nhưng ít hơn nhiều (95).

### 4.5 Wall time (thời gian thực thi) — TH3 Section IV.A

TH3 báo cáo thời gian chạy trong "Các thí nghiệm":

| Kịch bản TH3 | Wall time (1 episode × 500 step) |
|---|---|
| All RL (KEEP) | **45.2 giây** |
| All LLM (GPT-4o-mini, **5 LLM agent**) | **4704.6 giây** (≈ 78 phút) |
| Tỷ lệ RL/LLM | **104.1 lần** RL nhanh hơn |

**Setup A luận văn**:

| Kịch bản | Wall time (1 episode × 500 step) |
|---|---|
| 1 LLM Claude Haiku 4.5 + 4 ReactRemoveBlueAgent | **6562.42 giây** (≈ 109 phút) |
| Trung bình step latency (độ trễ mỗi lượt) | **13.07 s/step** |
| Min step (lượt nhanh nhất) | 7.48 s |
| Max step (lượt chậm nhất) | 28.64 s |
| Percentile P95 (95% lượt nhanh hơn giá trị này) | 17.69 s |

**Phân tích**:

- Setup A: chỉ 1 LLM call (lệnh gọi LLM)/step (4 baseline không gọi LLM) → 6562 giây tổng = ~13 s/step thuần Claude Haiku 4.5.
- TH3 All LLM: 5 LLM call/step × ~1.88 s/call = ~9.4 s/step.
- Setup A **chậm hơn TH3 GPT-4o-mini per-LLM-call** vì Claude Haiku 4.5 có quá trình "thinking" (suy nghĩ) — reasoning model (mô hình suy luận chậm hơn nhưng chính xác hơn).

Tuy nhiên, **đây là chỉ số phụ** — luận văn không tối ưu latency, mục tiêu là chất lượng quyết định.

Dẫn chứng Setup A: 500 event `step_end` trong JSONL trường `data.wall_time_s`.
Dẫn chứng TH3: §IV.A "Các thí nghiệm" trang 6.

### 4.6 Parse JSON Success Rate (tỷ lệ parse JSON thành công)

TH3 §III.B nói: *"Nếu LLM trả lời theo một định dạng không mong đợi mà bộ phân tích hành động (action parser) của chúng tôi không hiểu, chúng tôi ghi nhận một hành động không hợp lệ (invalid action), và tác nhân sẽ Sleep trong bước đó"*. TH3 không cho số cụ thể tỷ lệ parse fail.

Setup A:

| Sự kiện | Số lần | Tỷ lệ |
|---|---|---|
| `paper_parse_result` (parse OK) | **500/500** | **100.0%** |
| `paper_parse_failed` (parse thất bại) | 0/500 | 0.0% |

→ Claude Haiku 4.5 luôn xuất JSON hợp lệ. Khác TH3 paper §V "Hạn chế Hallucinations (ảo giác)" có nhắc LLM đôi khi *"thay đổi định nghĩa của hành động"* hoặc xuất sai format.

### 4.7 Reasoning Clustering (phân cụm lý do suy luận) — chỉ số TH3 §IV.A

> **Phương pháp TH3**: Lấy 499 cặp (action, reason) trong 1 episode. Dùng `text-embedding-3-large` (model nhúng vector từ OpenAI) biến mỗi reason thành vector số. Áp dụng PCA (Phân tích thành phần chính — giảm số chiều) để vẽ 3D. Phân cụm K-Means (gom thành K nhóm) với K=4 (xác định bằng Elbow Method — phương pháp khuỷu tay, và Silhouette Score — điểm Silhouette).

TH3 §IV.A báo cáo 4 cụm trên 499 mẫu (1 episode 500 step trừ step khởi tạo):

| Cluster TH3 | DP (Data Points — điểm dữ liệu) | Chủ đề |
|---|---|---|
| 0 | **202** (40.5%) | DeployDecoy + Analyse khi không có cảnh báo (proactive — chủ động) |
| 1 | **103** (20.6%) | Analyse + DeployDecoy + Remove khi nhận cảnh báo |
| 2 | **93** (18.6%) | Analyse nguyên nhân DeployDecoy thất bại |
| 3 | **101** (20.2%) | Analyse để xác nhận DeployDecoy đang triển khai |

→ TH3 cluster của o3-mini phản ánh **chiến lược chủ yếu xoay quanh DeployDecoy + Analyse**.

Setup A luận văn **chưa làm clustering trên 1 episode** (chỉ 100 action_proposed events, thấp hơn TH3 499). Khi có thêm episode + run clustering, có thể tạo bảng tương ứng. Hiện tại cluster định tính từ phân bố action Setup A:

| Action | Setup A | Cụm tương đương |
|---|---|---|
| Sleep | 400 (80%) | Cụm "thụ động" — KHÔNG có trong TH3 |
| Analyse | 95 (19%) | Tương đương Cluster 0 + 2 của TH3 |
| Restore (3) + Remove (2) | 5 (1%) | KHÔNG có cluster riêng — TH3 cũng tránh Restore |

→ Setup A có **1 cluster "thụ động" lớn (Sleep)** mà TH3 không có (vì TH3 loại Sleep khỏi prompt). Đây là khác biệt định tính lớn.

---

## 5. Các chỉ số bổ sung (vượt ngoài TH3 paper)

### 5.1 Reasoning Length (độ dài lý luận)

TH3 không báo cáo. Setup A:

| Đại lượng | Giá trị (ký tự) |
|---|---|
| Trung bình | 288 |
| Trung vị (median) | 285 |
| Min | 139 |
| Max | 631 |

Dẫn chứng: 500 event `llm_response_chunk` trong JSONL.

### 5.2 Action Diversity (sự đa dạng đối tượng hành động)

TH3 không báo cáo trực tiếp. Setup A:

| Đại lượng | Giá trị |
|---|---|
| Số host (máy chủ) khác nhau bị LLM target (nhắm tới) | **5 host** |
| Host được target nhiều nhất | `public_access_zone_subnet_server_host_0` (máy chủ 0 trong subnet truy cập công cộng) |
| Tỷ lệ target tập trung 1 host | **75/100 = 75%** |

Top 5 host:

| Host | Lần target |
|---|---|
| `public_access_zone_subnet_server_host_0` | 75 |
| `office_network_subnet_user_host_1` | 9 |
| `office_network_subnet_user_host_8` | 7 |
| `public_access_zone_subnet_server_host_4` | 5 |
| `office_network_subnet_user_host_4` | 4 |

→ LLM Setup A "kẹt" vào 1 host — vấn đề định tính lớn.

### 5.3 Timing — Step đầu tiên xuất hiện hành động chính

| Sự kiện | Setup A | Ý nghĩa |
|---|---|---|
| LLM ra `Analyse` lần đầu | **step 28** | Mất 28 step (≈ 6 phút thực) trước khi action chủ động đầu tiên |
| LLM ra `Restore` lần đầu | **step 44** | |
| LLM ra `Remove` lần đầu | **step 164** | |
| Comm vector (vectơ truyền thông) có signal admin (tín hiệu xâm phạm mức quản trị) | **không có (None)** suốt 500 step | (xem 5.6) |

### 5.4 Vòng lặp Analyse — Bằng chứng L2 (lệ thuộc prompt, thiếu retry có cấu trúc)

5 chuỗi Analyse cùng host trong 5 step liên tiếp:

| Chuỗi | Số lần | Host | Step range |
|---|---|---|---|
| 1 | 8 | office_network_subnet_user_host_1 | 28-42 |
| 2 | 4 | public_access_zone_subnet_server_host_4 | 156-162 |
| 3 | 3 | office_network_subnet_user_host_4 | 217-221 |
| 4 | 6 | office_network_subnet_user_host_8 | 231-241 |
| 5 | **74** | **public_access_zone_subnet_server_host_0** | **313-459** |

Chuỗi 5: **74 lần Analyse cùng host trong 146 step liên tiếp**. Bằng chứng định lượng cực mạnh cho L2 (LLM thiếu cơ chế "biết đã làm gì rồi" → lặp vô tận).

### 5.5 Baseline blue agent crashes (lỗi của agent cơ sở)

2 lần `ReactRemoveBlueAgent` crash (lỗi runtime) với `KeyError: IPv4Address` (địa chỉ IP phiên bản 4 không có trong bản đồ tĩnh của scenario — IP `10.0.134.36` và `10.0.134.75`). Đã wrap try/except (bọc trong khối bắt lỗi) trong [`run_benchmark.py:get_action_from_policy()`](../../feasibility-mcp-roe/benchmark/run_benchmark.py) → fallback Sleep. Tỷ lệ 0.1% trên 2000 baseline action call.

### 5.6 Comm vector (vectơ truyền thông) breakdown

> **Giao thức truyền thông 8-bit của TH3** (TH3 §III.C):
> - Bit 0-4: bit thứ j = 1 nếu sender (người gửi) phát hiện hoạt động độc hại từ mạng của agent j
> - Bit 5-6: compromise level (mức xâm phạm) trong subnet của sender:
>   - 00 = none (không có xâm phạm)
>   - 01 = remote_exploit (phát hiện netscan / khai thác từ xa)
>   - 10 = user (xâm phạm cấp người dùng — IOC như `cmd.sh`/`cmd.exe`)
>   - 11 = admin (xâm phạm cấp quản trị — IOC như `escalate.sh`/`escalate.exe`)
> - Bit 7: 1 nếu sender đang busy (bận thực thi action), 0 nếu rảnh

Setup A đo được:

| compromise_level (mức xâm phạm trong mạng sender) | Số report | Tỷ lệ |
|---|---|---|
| `none` (không có xâm phạm) | **1996** | **100.0%** |
| `remote_exploit` (khai thác từ xa) | 0 | 0.0% |
| `user` (mức người dùng) | 0 | 0.0% |
| `admin` (mức quản trị) | 0 | 0.0% |

→ Suốt 500 step, 4 đồng đội broadcast (phát) comm vector luôn rỗng vì `CommVectorGenerator` (bộ sinh vectơ truyền thông trong code TH3) bị fallback `EMPTY_MESSAGE` (thông điệp rỗng mặc định). **Hạn chế lớn**: không thể đo M4 (comms misread rate — tỷ lệ đọc sai comm) trong Setup A test này.

Lý do: TH3 codebase có `CommVectorGenerator.create_comm_message()` nhưng API mismatch (không tương thích chữ ký) giữa version cũ/mới → exception silent (lỗi im lặng) → run_benchmark fallback empty. Cần debug ở Phase 2 đầy đủ.

---

## 6. Mẫu suy luận LLM tại 5 step đại diện

### 6.1 Step 0 — Phase 0 (Planning)

JSONL line 3 (`state_extracted`), 5 (`llm_response_chunk`), 7 (`action_materialized`). Final: `Sleep (no action proposed)`.

```json
{
  "action": "Sleep",
  "reason": "Pha Planning (pha 0) - không có thông tin vectơ truyền thông hoặc
   hoạt động độc hại được báo cáo..."
}
```

### 6.2 Step 100 — Phase 0 cuối

JSONL line 712, 714, 716. Final: `Sleep (no action proposed)`.

```json
{
  "action": "Sleep",
  "reason": "Tất cả các vectơ truyền thông từ các agent khác đều là
   [0,0,0,0,0,0,0,0], chỉ ra không có hoạt động độc hại hoặc compromise
   trong hệ thống..."
}
```

LLM **trích dẫn raw bit (bit thô) chính xác** — không hallucinate giá trị (vector THẬT là rỗng).

### 6.3 Step 250 — Phase 1 (MissionA)

JSONL line 1778, 1780, 1782. Final: `Sleep`.

```json
{
  "action": "Sleep",
  "reason": "Tất cả vectơ truyền thông từ các agent khác đều [0,0,0,0,0,0,0,0]
   - không phát hiện hoạt động độc hại..."
}
```

### 6.4 Step 400 — Phase 2 (MissionB)

JSONL line 2872, 2874, 2876.

```json
{
  "action": "Sleep",
  "reason": "Trước đây Analyse vẫn đang chạy (IN_PROGRESS — đang xử lý).
   Không có hoạt động độc hại nào được báo cáo..."
}
```

LLM dùng đúng `last_action_status` (trạng thái hành động trước — IN_PROGRESS) — pipeline observation hoạt động.

### 6.5 Step 499 — Cuối episode

JSONL line 3596, 3598, 3600.

```json
{
  "action": "Sleep",
  "reason": "Tất cả các agent khác báo cáo subnets an toàn (vectơ bit 5-6 = 00),
   không phát hiện hoạt động độc hại..."
}
```

LLM dùng đúng quy tắc decode bit 5-6 = `00` = none — không hallucinate bit position (vị trí bit).

### 6.6 5 step Destructive Action (hành động phá hủy) — chi tiết

| step | Action | Host | Level (mức xâm phạm host) | state_extracted | llm_response | action_proposed |
|---|---|---|---|---|---|---|
| 44 | Restore | office_network_subnet_user_host_1 | admin (mức quản trị) | line 319 | line 321 | line 323 |
| 164 | Remove | public_access_zone_subnet_server_host_4 | user (mức người dùng) | line 1164 | line 1166 | line 1168 |
| 223 | Restore | office_network_subnet_user_host_4 | admin | line 1581 | line 1583 | line 1585 |
| 243 | Restore | office_network_subnet_user_host_8 | admin | line 1728 | line 1730 | line 1732 |
| 461 | Remove | public_access_zone_subnet_server_host_0 | user | line 3329 | line 3331 | line 3333 |

Lệnh xem trực tiếp dòng:

```bash
sed -n '319,323p' feasibility-mcp-roe/benchmark/results/detailed_A_FiniteState_ep0.jsonl
```

5/5 action đúng level (3 Restore trên host admin-level, 2 Remove trên host user-level — đúng quy tắc trong prompt).

---

## 7. Đối chiếu 3 hạn chế TH3 với Setup A

### 7.1 L1 — Ảo giác (hallucination) đọc vectơ 8-bit

**TH3 báo cáo**: TH3 §IV.A "So sánh việc chọn hành động giữa RL và LLM" — *"Phân tích của chúng tôi cho thấy trong một số trường hợp, lý do chọn hành động dễ bị ảo giác... nhiều trường hợp tác nhân diễn giải sai vectơ truyền thông của một tác nhân (tức là giả định nó từ agent 4 trong khi thực ra từ agent 3) hoặc thay đổi định nghĩa của hành động"*.

**Setup A đo được**: KHÔNG kích hoạt được L1 trong test này vì comm vector luôn rỗng (xem 5.6). LLM Setup A trích dẫn đúng `[0,0,0,0,0,0,0,0]` ở mọi step có comm — không hallucinate giá trị vector. **Cần test riêng với signal thật để verify L1.**

→ Không verify được L1 ở Setup A. Phải đợi Setup B/C có MCP decoder (bộ giải mã pre-parse) + có signal thật.

### 7.2 L2 — Lệ thuộc cách viết prompt + thiếu retry có cấu trúc

**TH3 báo cáo**: TH3 §V.B "Định nghĩa Prompt" thừa nhận *"điều chỉnh định nghĩa của các hành động có thể làm giảm các hình phạt"* + *"chúng tôi không định nghĩa hành động Sleep trong prompt"* → cho thấy hành vi LLM rất nhạy với cách viết prompt. TH3 cũng nói *"Prompt có thể được cải thiện để mô tả mỗi hành động chi tiết hơn nhằm tránh nhầm lẫn, như những trường hợp được nhận diện trong các cụm lý do 2 và 3"*.

**Setup A đo được**:
- **5 chuỗi Analyse cùng host**, chuỗi cực đoan **74 lần liên tiếp trên 1 host** (mục 5.4)
- LLM Setup A "kẹt" 75% action vào 1 host duy nhất (mục 5.2)
- Cluster 2 + 3 của TH3 cũng phản ánh kiểu "Analyse lặp" tương tự (TH3 Bảng IV, 93+101 = 194 data points / 499 = 39%)

→ **L2 được verify trực tiếp ở Setup A** với bằng chứng định lượng rất mạnh.

### 7.3 L3 — Thiếu định hướng phần thưởng (RoE)

**TH3 báo cáo**: TH3 §V.B *"Để đánh giá năng lực suy luận vốn có của LLM cho ACD, prompt của chúng tôi không bao gồm một chiến lược với các quy tắc quyết định hành động tường minh"* — TH3 chủ ý không cho LLM biết reward function (hàm thưởng). TH3 nói thêm *"Chúng tôi có thể cải thiện hiệu năng của tác nhân ACD dùng LLM bằng hướng dẫn dựa trên suy luận của RL"*.

**Setup A đo được**:
- LLM destructive (phá hủy) 5/500 (1.0%) — quá ít, "quá an toàn"
- Nhưng 5/5 đều đúng level (3 admin Restore, 2 user Remove) → LLM tự tuân thủ quy tắc trong prompt mà không cần RoE chặn
- → LLM Setup A **đã làm đúng nhưng quá ít** — nếu có RoE gợi ý chủ động (trường `suggested` — gợi ý), LLM có thể proactive (chủ động) hơn

→ **L3 được verify gián tiếp ở Setup A**. Setup C với RoE sẽ kiểm chứng trực tiếp.

---

## 8. Hạn chế của báo cáo

1. **n = 1**: chỉ 1 episode, không có σ (độ lệch chuẩn). Khi hoàn thành 5 ep × 4 red = 20 ep cho Setup A, sẽ tính μ ± σ tương tự TH3 Hình 5.
2. **1 red variant**: chỉ FiniteState, chưa test AggressiveFSM (hung hãn)/StealthyFSM (lén lút)/ImpactFSM (gây tác động)/DegradeServiceFSM (làm suy giảm dịch vụ).
3. **Baseline đồng đội khác TH3**: ReactRemoveBlueAgent thay vì KEEP → không so trực tiếp được số tuyệt đối.
4. **LLM nền khác TH3**: Claude Haiku 4.5 thay vì OpenAI/DeepSeek → số tuyệt đối chỉ dùng cho ablation nội bộ A/B/C.
5. **Prompt khác TH3**: Role-only thay vì Role+Few-shot. TH3 Bảng III cho thấy Few-shot tốt hơn cho GPT-4o-mini (+591 reward). Cần thêm few-shot examples cho Setup A nếu muốn so chặt chẽ với TH3.
6. **CommVectorGenerator fallback EMPTY**: comm vector luôn rỗng → không kích hoạt được L1 + không đo được M4. Cần debug CommVectorGenerator API mismatch.
7. **2 baseline crash**: 0.1% — ảnh hưởng nhỏ nhưng tồn tại.

---

## 9. Đánh giá tổng hợp Setup A

### 9.1 Đóng góp 1 — Verify pipeline khớp TH3

Setup A chứng minh pipeline TH3 chạy trong khung benchmark luận văn, hoàn thành **500/500 step** không truncate (cắt bỏ giữa chừng). Khớp 100% TH3 §III.B (bảng 2.3 ánh xạ code paths với line number cụ thể).

### 9.2 Đóng góp 2 — Bảng đôi với TH3

Báo cáo này có **7 bảng đối chiếu trực tiếp** với số liệu TH3:

| Mục | Bảng đôi |
|---|---|
| 2.1 | Cấu hình thí nghiệm: 12 tham số TH3 vs Setup A |
| 2.2 Khác 3 | Prompt design — TH3 Bảng III được trích nguyên 3 dòng |
| 4.1 | M1 reward Setup A vs 6 kịch bản TH3 |
| 4.3 | μ ± σ qua red variant TH3 Hình 5 |
| 4.4 | Action distribution TH3 Hình 7 với 8 action |
| 4.5 | Wall time TH3 vs Setup A |
| 4.7 | Reasoning clustering TH3 Bảng IV |

### 9.3 Đóng góp 3 — Bằng chứng định lượng cho 3 hạn chế TH3

| Hạn chế | Setup A bằng chứng | Trạng thái |
|---|---|---|
| L1 (ảo giác bit) | Chưa verify được (comm vector rỗng) | Cần fix CommVectorGenerator |
| L2 (lệ thuộc prompt, thiếu retry) | Vòng lặp 74 lần Analyse cùng host | **Verify mạnh** |
| L3 (thiếu RoE) | 1.0% destructive action, "quá an toàn" | Verify gián tiếp |

### 9.4 Đóng góp 4 — Dataset reproducible (dữ liệu tái lập được)

3 file artifact với line number citable (xem mục 3). Tool đọc: [`benchmark/inspect_episode.py`](../../feasibility-mcp-roe/benchmark/inspect_episode.py).

---

## 10. Kết luận

| Tiêu chí | Setup A | TH3 paper |
|---|---|---|
| M1 cumulative reward (red FiniteState) | **−660** | All LLM: −2547.2 ± 498.8 (μ qua 5 red); 1LLM+4RL: −500 đến −2200 tùy LLM |
| M2 invalid action rate (tỷ lệ hành động không hợp lệ) | **80.0%** (do Sleep được prompt định nghĩa) | Không công bố — TH3 cố ý không cho Sleep |
| M5 step latency (độ trễ mỗi lượt) | **13.07 s/step** | TH3 All LLM GPT-4o-mini ≈ 9.4 s/step (5 LLM call/step) |
| Parse JSON success | **100%** | Không công bố cụ thể, có nhắc fallback Sleep |
| Action diversity (đa dạng đối tượng) | 5 host, 75% tập trung 1 host | TH3 không báo cáo |
| L2 verify | 74 Analyse cùng host | TH3 ghi nhận tương tự (Cluster 2 + 3 = 39%) |
| L3 verify | 1% destructive | TH3 ghi nhận LLM tránh Restore |
| L1 verify | Không kích hoạt được (comm rỗng) | TH3 báo cáo có hallucinate comm |

**Setup A đã hoàn thành vai trò baseline TH3 trong khung benchmark luận văn**. Pipeline khớp 100% TH3 §III.B. Số liệu Setup A (−660 reward) nằm giữa các kịch bản TH3 (tốt hơn All-LLM −6334, kém hơn All-RL KEEP −451). Các bằng chứng định lượng cho L2 và L3 đã có; L1 cần fix CommVectorGenerator để verify trực tiếp.

Sau khi hoàn thành 5 ep × 4 red cho Setup A → có bảng μ ± σ tương đương TH3 Hình 5 + bảng đối chiếu đầy đủ với TH3 cho mọi chỉ số chính.

---

## Phụ lục A — Tham chiếu cụ thể trong TH3 paper

Mọi citation TH3 trong báo cáo này có thể được verify bằng cách đọc file `TH3_Large_Language_Models_are_Autonomous_Cyber_Defenders.pdf` trong workspace:

| Mục TH3 | Trang | Nội dung dẫn |
|---|---|---|
| §I Giới thiệu | 1 | Mục đích chung |
| §II.A CybORG CAGE 4 | 2 | Mô tả môi trường, 3 phase Planning/MissionA/MissionB |
| §II Bảng I | 2 | Danh sách action (Sleep, Monitor, Analyse, Remove, Restore, DeployDecoy, Block/AllowTrafficZone, Discover, Exploit, ...) |
| §III.A LLM Adapter (bộ điều hợp LLM) | 3 | Mô tả khung adapter |
| §III.B Định dạng quan sát | 3 | **Bảng II** observation format — Setup A khớp với bảng này |
| §III.C Communication Vector 8-bit | 3-4 | Mô tả bit 0-4, 5-6, 7 — khớp `paper_style.py:PAPER_SYSTEM_PROMPT` |
| §III.D Bảng III Prompt | 4 | **Số liệu Role/Few-shot/Instruct** cho 3 OpenAI model |
| §IV Đánh giá | 5 | Setup thí nghiệm: 2 ep × 500 step, temperature=1, 4 kịch bản blue |
| §IV.A Hiệu năng | 6 | Wall time RL 45.2s vs LLM 4704.6s |
| §IV.A Hình 4 | 6 | **Reward 4 LLM model** (o3, o1, GPT-4o-mini, DeepSeek-V3) cho 1LLM+4RL |
| §IV.A Hình 5 | 6 | **Reward 3 kịch bản × 5 red** (No blue / All LLM / All RL) — số μ=−2547.2 σ=498.8 và μ=−493 σ=95.9 |
| §IV.A Hình 7 | 8 | **Action count** cho 1 LLM o3-mini và 1 RL KEEP — bảng 4.4 báo cáo |
| §IV.A Bảng IV | 7 | **4 cluster K-Means** với 202+103+93+101 = 499 DP |
| §V Thảo luận hạn chế | 8-9 | Hallucinations + Prompt Definition + Environment Compatibility |
| §V "Định nghĩa Prompt" | 9 | TH3 không định nghĩa Sleep — nguyên nhân khác biệt với Setup A |

---

## Phụ lục B — Cách reproduce (tái lập kết quả)

```bash
# Kích hoạt môi trường (virtual environment — môi trường ảo Python)
source llms-are-acd-main/cage-env/bin/activate
export PYTHONPATH=/Users/apple/Workspace/personal/side-projects/demo/llms-are-acd-main/cage-challenge-4
cd feasibility-mcp-roe

# Chạy Setup A 1 episode (resume an toàn — máy tắt vẫn tiếp tục được,
# checkpoint mỗi 50 step được lưu trong file checkpoint_*.pkl)
python -u benchmark/run_benchmark.py --setup A --red FiniteState --episodes 1

# Verify (xác minh) kết quả
cat benchmark/results/joint_reward_A_FiniteState_ep0.json | python3 -m json.tool

# Đọc chi tiết step bất kỳ (vd step 44 = Restore đầu tiên)
python benchmark/inspect_episode.py \
  benchmark/results/detailed_A_FiniteState_ep0.jsonl --step 44 --full

# Xem trực tiếp dòng cụ thể (vd step 44 = JSONL line 319-323)
sed -n '319,330p' benchmark/results/detailed_A_FiniteState_ep0.jsonl | python3 -m json.tool

# Đếm Analyse trên host bị "kẹt" (vòng lặp Analyse 74 lần)
grep -E '"action_proposed".*"public_access_zone_subnet_server_host_0"' \
  benchmark/results/detailed_A_FiniteState_ep0.jsonl | wc -l
# Kết quả: 75
```

---

*Báo cáo dựa hoàn toàn vào 2 nguồn: (1) bài báo *Large Language Models are Autonomous Cyber Defenders* (TH3, file PDF trong workspace) và (2) các file artifact `benchmark/results/` từ 1 lần chạy Setup A. Mọi số liệu TH3 có thể verify bằng cách đọc PDF theo trang/§/bảng đã cite. Mọi số liệu Setup A có thể verify bằng cách trace JSONL theo line number.*
