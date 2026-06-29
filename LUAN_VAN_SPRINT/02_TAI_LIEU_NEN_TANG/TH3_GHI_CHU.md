# Ghi chú: TH3 — Large Language Models are Autonomous Cyber Defenders

**Tác giả**: S. R. Castro, R. Campbell, N. Lau, O. Villalobos, J. Duan, A. A. Cárdenas
**Affiliation**: University of California, Santa Cruz
**Venue**: IEEE CAI 2025 — Adaptive Cyber Defense Workshop
**arXiv**: 2505.04843
**Mã nguồn**: https://github.com/r4wd3r/llms-are-acd (đã clone về `llms-are-acd-main/`)

## Tóm tắt

Bài báo TH3 là nghiên cứu **tiên phong** áp dụng LLM làm tác nhân phòng thủ (blue agent) trong môi trường CybORG CAGE 4 đa tác nhân. Tác giả tích hợp LLM (GPT-4o-mini, o1-mini, o3-mini, DeepSeek-V3) vào framework qua một bộ điều hợp (adapter) tùy chỉnh, đề xuất giao thức truyền thông 8-bit giữa các blue agent, và đánh giá trên các chiến lược red agent đa dạng. Kết quả cho thấy LLM có thể truyền thông và suy luận an ninh tương đương đội người vận hành, nhưng có ba hạn chế chính: ảo giác đọc vectơ truyền thông, lệ thuộc cách viết prompt, và thiếu định hướng từ hàm thưởng.

## Kiến trúc chính trong bài

### 1. Khung Bộ điều hợp LLM (LLM Adapter Framework)
- Wrap quanh CybORG để LLM nhận observation
- 1 LLM-driven agent + 4 RL-driven agent KEEP
- Custom policies cho cả red và blue
- Hỗ trợ online (OpenAI, DeepSeek qua OpenRouter) và offline (HuggingFace)

### 2. Định dạng quan sát cho LLM
Mỗi step, LLM nhận text:
- Agent (tên)
- MissionPhase
- LastAction + LastActionStatus
- CommunicationVectors (4 vectơ 8-bit từ 4 blue agent khác)
- SuspiciousActivityDetected (list)

### 3. Giao thức truyền thông 8-bit (đề xuất của bài)
- **Bit 0-4**: agent i set bit j=1 nếu phát hiện hoạt động độc hại từ subnet của agent j
- **Bit 5-6**: mức compromise trong subnet của sender (00=none, 01=remote, 10=user, 11=admin)
- **Bit 7**: sender busy (1) hay free (0)

### 4. Thiết kế Prompt
- Strategy: Role Prompting (gán vai trò "chuyên gia an ninh mạng") + Few-Shot
- Không nêu rõ hàm thưởng — chỉ context thực tế
- Temperature = 1
- Single system/user message mỗi step để tiết kiệm token

### 5. Kịch bản thí nghiệm
- **No blue agent**: baseline tệ nhất
- **All LLM**: 5 blue đều LLM
- **All RL**: 5 blue đều KEEP — best reward
- **1 LLM + 4 RL**: scenario chính của bài

### 6. Red agent variants
- AggressiveFSMAgent
- StealthyFSMAgent
- ImpactFSMAgent
- DegradeServiceFSMAgent

## Kết quả chính

### Phần thưởng (Reward)
- **All RL (KEEP)**: µ = −493, σ = 95,9 (tốt nhất)
- **All LLM (GPT-4o-mini)**: µ = −2.547,2, σ = 498,8
- **1 LLM + 4 RL**: o3-mini cho reward cao nhất, GPT-4o-mini cân bằng nhất giữa thời gian và reward

### Thời gian
- LLM chậm hơn RL ~104,1 lần (sau khi loại bỏ huấn luyện RL)

### Phân tích suy luận (Clustering bằng K-Means)
- 4 cluster reasoning:
  - **Cluster 0** (202 DP): proactive — DeployDecoy + Analyse khi không có cảnh báo
  - **Cluster 1** (103 DP): phản ứng cảnh báo — Analyse + DeployDecoy + Remove
  - **Cluster 2** (93 DP): xử lý thất bại — Analyse khi action trước fail
  - **Cluster 3** (101 DP): giám sát decoy đang diễn ra

### So sánh RL vs LLM (action distribution)
- **RL (KEEP)**: thụ động — chủ yếu Monitor, Sleep, Remove
- **LLM**: chủ động đánh lừa — DeployDecoy nhiều, tránh Restore

## 3 hạn chế LLM Agent (bài chỉ rõ)

### Hạn chế 1 — Ảo giác đọc vectơ 8-bit
LLM gán nhầm agent (vd nghĩ là agent 4 nhưng thực ra agent 3), đọc nhầm compromise level. **§V Discussion**.

### Hạn chế 2 — Lệ thuộc prompt
Định nghĩa action sai chữ → chiến lược khác hẳn. Vd: không define `Remove` → LLM tự diễn giải = "ngắt kết nối máy chủ" thay vì "xóa tiến trình độc hại". **§V.A**.

### Hạn chế 3 — Thiếu hàm thưởng
LLM không thấy reward function → không tối ưu. Bias các action an toàn (Analyse, DeployDecoy) thay vì Restore. Còn lý do: định nghĩa Restore/BlockTrafficZone trong prompt khiến LLM tránh chúng vì sợ ảnh hưởng availability. **§V.A**.

## Khía cạnh em sẽ kế thừa và mở rộng

| Bài TH3 | Đề tài em |
|---|---|
| Wrap LLM vào CybORG bằng custom adapter | Tích hợp qua MCP + Claude Agent SDK |
| Định dạng obs là text (kèm raw 8-bit) | Pre-decode bit → JSON qua MCP tool |
| Action là text response → parse | Action là MCP tool call có schema cứng |
| Không có rào chắn — LLM tự do | RoE allow-list + rate-limit rule |
| Thiếu reward direction | RoE feedback (allow/deny + reason) thay reward |
| Cluster reasoning bằng K-Means | Kế thừa phương pháp này cho Chương 5 |

## Trích dẫn cụ thể em sẽ dùng

- §III.C — định dạng vectơ truyền thông 8-bit
- §IV.B — thực nghiệm ảnh hưởng của định nghĩa action
- §IV.E — phương pháp clustering reasoning bằng K-Means + PCA
- §V — phần Discussion về 3 hạn chế

## Câu hỏi còn để mở

[Liệt kê khi đọc thấy chỗ chưa rõ]
