# CHƯƠNG 2 — CƠ SỞ LÝ THUYẾT

## 2.1 Bài toán quyết định Markov có quan sát một phần (POMDP)

### 2.1.1 Định nghĩa

Bài toán Quyết định Markov có Quan sát Một phần (Partially Observable Markov Decision Process — POMDP) là một mô hình toán học mô tả quá trình ra quyết định khi tác nhân không quan sát được trạng thái thật của môi trường mà chỉ quan sát qua một dấu hiệu gián tiếp. Một POMDP được định nghĩa bởi bộ bảy phần tử:

$$
\text{POMDP} = (S, A, T, R, \Omega, O, \gamma)
$$

trong đó:
- $S$ — tập trạng thái (state) của môi trường
- $A$ — tập hành động (action)
- $T(s, a, s')$ — hàm chuyển trạng thái (transition function)
- $R(s, a)$ — hàm phần thưởng (reward function)
- $\Omega$ — tập quan sát (observation)
- $O(s', a, o)$ — hàm quan sát (observation function)
- $\gamma$ — hệ số chiết khấu (discount factor)

### 2.1.2 Áp dụng vào Phòng thủ Mạng Tự động

Trong bối cảnh ACD, các thành phần được ánh xạ như sau:
- **State** ($S$): trạng thái mạng — danh sách máy chủ, tiến trình, kết nối, mức độ xâm phạm.
- **Action** ($A$): hành động phòng thủ — Analyse, Restore, DeployDecoy, BlockTrafficZone, v.v.
- **Observation** ($\Omega$): tác nhân chỉ thấy được một phần trạng thái — chỉ subnet được phân công + thông điệp từ đồng đội.
- **Reward** ($R$): phần thưởng dựa trên tính khả dụng dịch vụ (availability) và tổn thất do xâm phạm.

Tính quan sát một phần (partial observability) là đặc trưng quan trọng của ACD: kẻ tấn công luôn cố che giấu hoạt động, và một tác nhân phòng thủ không bao giờ có thông tin đầy đủ về toàn bộ mạng tại một thời điểm.

## 2.2 Bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1]

### 2.2.1 Nội dung chính

Bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1] đưa ra một góc nhìn lý thuyết cho việc tự động hóa phản ứng an ninh mạng. Trọng tâm của bài báo là phân tích các điều kiện cần thiết để con người có thể tin tưởng (trust) giao quyền ra quyết định cho các tác nhân AI trong môi trường an ninh mạng có rủi ro cao.

### 2.2.2 Nguyên lý Human-on-the-loop

Bài báo nhấn mạnh nguyên lý **human-on-the-loop**: con người không tham gia trực tiếp vào mọi quyết định của tác nhân (như trong human-in-the-loop), nhưng phải có khả năng giám sát, can thiệp và điều chỉnh hành vi của tác nhân khi cần. Đây là sự khác biệt then chốt với mô hình hoàn toàn tự động (fully autonomous), nơi AI ra quyết định độc lập mà không có cơ chế kiểm soát từ con người.

### 2.2.3 Tuân thủ các đánh đổi rủi ro do con người thiết lập

Bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1] đề xuất rằng các tác nhân AI trong ACD phải hành xử **trong khuôn khổ các đánh đổi rủi ro** mà con người đã định sẵn — ví dụ: không được phép thực hiện hành động phá hủy dịch vụ trừ khi chắc chắn rằng dịch vụ đã bị xâm phạm ở mức cao. Đây là nền tảng lý luận cho khái niệm **Rules of Engagement (RoE)** trong đề tài này.

### 2.2.4 Vai trò trong đề tài

Bài báo [1] cung cấp **cơ sở lý luận** cho phần thiết kế của đề tài: tại sao cần áp đặt rào chắn deterministic lên hành vi của tác nhân LLM, và tại sao cơ chế phản hồi (feedback) khi vi phạm rào chắn phải có thể được con người hiểu được (bằng ngôn ngữ tự nhiên, không phải reward số).

## 2.3 Mô hình Ngôn ngữ Lớn và LLM Agent

### 2.3.1 Mô hình Ngôn ngữ Lớn (LLM)

**Mô hình Ngôn ngữ Lớn (Large Language Model — LLM)** là một loại mạng nơ-ron sâu (deep neural network) có kích thước rất lớn (thường từ vài tỷ đến hàng trăm tỷ tham số), được huấn luyện trên một lượng dữ liệu văn bản khổng lồ. Các LLM hiện đại như GPT, Claude, Llama, DeepSeek đều dựa trên kiến trúc **Transformer** với cơ chế **Self-Attention** cho phép xử lý chuỗi văn bản dài và nắm bắt các phụ thuộc xa.

LLM thể hiện khả năng **học không cần huấn luyện thêm (zero-shot / few-shot learning)** — có thể giải quyết các nhiệm vụ mới chỉ thông qua mô tả bằng ngôn ngữ tự nhiên trong prompt, mà không cần huấn luyện lại trên dữ liệu chuyên biệt.

### 2.3.2 LLM Agent

**LLM Agent** là tác nhân AI sử dụng LLM làm thành phần ra quyết định trung tâm. Khác với LLM thuần túy (chỉ trả lời prompt), LLM Agent có thêm khả năng:

- **Gọi công cụ (tool calling / function calling)** — yêu cầu các hàm ngoài LLM để thu thập thông tin hoặc thực thi hành động.
- **Vòng lặp suy luận (reasoning loop)** — LLM có thể gọi tool nhiều lần trong một quyết định, đọc kết quả, rồi tiếp tục suy luận.
- **Bộ nhớ ngữ cảnh (context memory)** — lưu lịch sử quyết định để tham chiếu trong các bước sau.

LLM Agent là nền tảng kỹ thuật cho hướng tiếp cận của đề tài này.

### 2.3.3 So sánh LLM Agent với tác nhân Học tăng cường (RL)

| Khía cạnh | LLM Agent | RL Agent |
|---|---|---|
| Huấn luyện | Pre-trained, không cần huấn luyện thêm | Cần huấn luyện chuyên biệt cho mỗi bài toán |
| Tính giải thích | Cao — reasoning bằng ngôn ngữ tự nhiên | Thấp — chính sách dạng mạng nơ-ron đen |
| Tính chuyển giao | Cao — cùng model dùng nhiều môi trường | Thấp — chính sách bị "đóng đinh" vào môi trường huấn luyện |
| Tốc độ suy luận | Chậm hơn (vài giây đến vài chục giây/quyết định) | Nhanh (mili giây/quyết định) |
| Định hướng tối ưu | Qua prompt — không có hàm thưởng trực tiếp | Qua reward function |
| Yêu cầu dữ liệu | Không cần (đã pre-trained) | Cần dữ liệu lớn để hội tụ |

## 2.4 Môi trường mô phỏng CybORG CAGE 4

### 2.4.1 Tổng quan

**CybORG** là một thư viện mô phỏng (gym) dành cho việc phát triển các tác nhân an ninh mạng tự động, do nhóm nghiên cứu của Bộ Quốc phòng Úc và Chương trình Hợp tác Kỹ thuật TTCP phát triển. CybORG cung cấp một bệ thử nghiệm (testbed) tái tạo một mạng máy tính mô phỏng, nơi các tác nhân tương tác với môi trường và học cách phòng thủ trước những kẻ tấn công.

**CAGE Challenge** là cuộc thi thường niên do TTCP tổ chức nhằm thúc đẩy trình độ tân tiến nhất (state-of-the-art) trong ACD. **CAGE Challenge 4** là phiên bản mới nhất với độ phức tạp cao nhất.

### 2.4.2 Kiến trúc CybORG CAGE 4

CybORG CAGE 4 mô phỏng một kịch bản Học tăng cường đa tác nhân (Multi-Agent Reinforcement Learning — MARL) với một đội tác nhân phòng thủ (blue agent) bảo vệ một mạng khỏi những kẻ địch (red agent) trong khi duy trì tính khả dụng dịch vụ cho người dùng hợp pháp (green agent).

Mạng được chia thành các vùng (zone):

- **Hai mạng triển khai (deployed networks A và B)**, mỗi mạng chứa các vùng bị hạn chế (restricted) và vùng vận hành (operational).
- **Một mạng trụ sở (headquarters)** với vùng truy cập công cộng, vùng quản trị và vùng văn phòng.
- **Một mạng nhà thầu (contractor network)** nơi red agent khởi đầu.

### 2.4.3 Các tác nhân và hành động

CybORG CAGE 4 có ba loại tác nhân:

| Loại | Số lượng | Hành động chính |
|---|---|---|
| Blue agent (phòng thủ) | 5 | Monitor, Analyse, DeployDecoy, Remove, Restore, AllowTrafficZone, BlockTrafficZone |
| Red agent (tấn công) | 1 | Discover, Exploit, PrivilegeEscalate, DegradeService, Impact, Withdraw |
| Green agent (người dùng hợp pháp) | nhiều | LocalWork, AccessService |

CybORG CAGE 4 diễn ra qua **3 pha**: Planning (Lập kế hoạch), MissionA (Nhiệm vụ A), MissionB (Nhiệm vụ B). Mỗi pha có các ràng buộc truyền thông khác nhau giữa các vùng mạng — các vùng vận hành cụ thể trở nên bị cô lập (isolated) trong các nhiệm vụ đang hoạt động.

### 2.4.4 Hàm phần thưởng

Hàm thưởng (reward function) cho các blue agent được thiết kế để nhận hình phạt (penalty) nếu các green agent không thể dùng tài nguyên. Điều này có thể xảy ra do:
- Các hành động phòng thủ phá hủy (Restore, BlockTrafficZone) gây gián đoạn tạm thời.
- Các red agent gây tác động (impact) lên hệ thống.

Phần thưởng đánh giá là **joint reward** — tổng phần thưởng tích lũy của cả đội 5 blue agent qua một episode 500 step.

## 2.5 Bài báo *Large Language Models are Autonomous Cyber Defenders* [2]

### 2.5.1 Tổng quan

Bài báo *Large Language Models are Autonomous Cyber Defenders* [2] là nghiên cứu **tiên phong** áp dụng LLM làm tác nhân phòng thủ trong môi trường CybORG CAGE 4 đa tác nhân. Đây cũng là **bài báo nền tảng thực nghiệm chính** của đề tài này.

### 2.5.2 Kiến trúc Khung Bộ điều hợp LLM

Bài báo phát triển một khung bộ điều hợp (adapter framework) để tích hợp LLM vào CybORG. Khung này:

- Hỗ trợ các mô hình online: OpenAI (GPT-4o-mini, o1-mini, o3-mini), DeepSeek-V3 qua OpenRouter
- Hỗ trợ các mô hình offline: LLaMA, TinyLLaMA qua HuggingFace
- Cho phép cấu hình cấu trúc đội tác nhân: toàn bộ blue agent là LLM, toàn bộ là RL, hoặc kết hợp (1 LLM + 4 RL)

### 2.5.3 Định dạng quan sát và phản hồi

Mỗi step, LLM nhận một thông điệp `user` chứa quan sát đã định dạng:

| Trường | Giá trị |
|---|---|
| Agent | `blue_agent_<idx>` |
| MissionPhase | Planning / MissionA / MissionB |
| LastAction | hành động đã thực hiện ở step trước |
| LastActionStatus | TRUE / FALSE / UNKNOWN / IN_PROGRESS |
| CommunicationVectors | danh sách 4 vectơ 8-bit từ 4 blue agent khác |
| SuspiciousActivityDetected | danh sách hoạt động đáng ngờ ở mức host |

LLM phản hồi bằng JSON: `{"action": "<ActionName host:<host>>", "reason": "..."}`.

### 2.5.4 Giao thức truyền thông 8-bit

Bài báo [2] đề xuất một giao thức truyền thông giữa các blue agent qua vectơ 8 bit. Mỗi blue agent broadcast một vectơ mỗi lượt:

- **Bit 0-4**: bit $j$ được đặt = 1 nếu sender phát hiện hoạt động độc hại từ subnet của agent $j$. Bit ở vị trí của chính sender luôn = 0.
- **Bit 5-6**: mức compromise trong subnet của sender (00=none, 01=remote scan/exploit, 10=user-level, 11=admin-level).
- **Bit 7**: 1 nếu sender đang bận thực thi action, 0 nếu rảnh.

LLM phải tự decode các vectơ này để hiểu tình hình của đồng đội.

### 2.5.5 Thiết kế Prompt

Bài báo [2] khảo sát ba chiến lược prompt:

1. **Instructional Prompting**: chỉ mô tả nhiệm vụ và định dạng câu trả lời.
2. **Few-Shot Prompting**: thêm các ví dụ câu trả lời mẫu.
3. **Role Prompting**: gán cho LLM vai trò "chuyên gia an ninh mạng đang phòng thủ một mạng".

Kết quả: kết hợp **Role + Few-Shot** cho phần thưởng cao nhất.

### 2.5.6 Kết quả thực nghiệm

#### Phần thưởng (Reward)

| Setup | µ (trung bình) | σ (độ lệch chuẩn) |
|---|---:|---:|
| All RL (KEEP) | −493 | 95,9 |
| All LLM (GPT-4o-mini) | −2.547,2 | 498,8 |
| 1 LLM + 4 RL (o3-mini) | (cao nhất trong các LLM) | — |

→ Tác nhân RL **vượt trội** tác nhân LLM trên CybORG CAGE 4 theo hàm phần thưởng.

#### Thời gian

LLM chậm hơn RL khoảng **104,1 lần** (sau khi loại bỏ pha huấn luyện RL).

#### Phân tích reasoning bằng K-Means

Bài báo [2] áp dụng phương pháp phân cụm K-Means + PCA trên các cặp (action, reasoning_text) lấy từ một episode 500 step. Kết quả: 4 cluster với đặc trưng rõ ràng (proactive defense, phản ứng cảnh báo, xử lý thất bại, giám sát decoy).

### 2.5.7 Ba hạn chế then chốt mà bài báo chỉ ra

Bài báo [2] §V (Discussion) trình bày ba hạn chế chính của tác nhân LLM trong môi trường ACD — đây chính là động lực của đề tài này:

#### Hạn chế 1 — Ảo giác đọc vectơ truyền thông

> *"Các tác nhân LLM dễ bị ảo giác, bao gồm việc đọc sai các quan sát vectơ truyền thông, các mức xâm phạm, và các sự kiện an ninh."* — TH3 [2] §V

#### Hạn chế 2 — Lệ thuộc vào cách viết prompt cho định nghĩa action

> *"Khi chúng tôi không định nghĩa hành động Remove trong các thí nghiệm, LLM giả định rằng nó ngắt kết nối máy chủ thay vì xóa các tiến trình độc hại."* — TH3 [2] §V.A

#### Hạn chế 3 — Thiếu định hướng phần thưởng

> *"Định nghĩa của chúng tôi về Restore và BlockTrafficZone có thể đã khiến LLM tránh chúng để bảo toàn tính khả dụng. [...] Để đánh giá năng lực suy luận vốn có của LLM cho ACD, prompt của chúng tôi không bao gồm một chiến lược với các quy tắc quyết định hành động tường minh, cũng không có hướng dẫn riêng theo tình huống."* — TH3 [2] §V

## 2.6 Model Context Protocol (MCP)

### 2.6.1 Định nghĩa

**Model Context Protocol (MCP)** là một giao thức được giới thiệu bởi Anthropic vào năm 2024, cho phép các LLM gọi các công cụ bên ngoài (external tools) theo một định dạng có cấu trúc và chuẩn hóa. MCP khác với cơ chế function calling truyền thống ở ba điểm:

1. **Schema cứng (rigid schema)**: mỗi tool có khai báo input/output cứng theo định dạng JSON Schema. LLM không thể "sáng tạo" gọi tool không tồn tại hoặc với tham số sai kiểu.
2. **Server có thể chạy nội bộ (in-process MCP server)** hoặc tách rời (subprocess) — linh hoạt triển khai.
3. **Allow-list rõ ràng**: chỉ những tool được đăng ký mới được LLM truy cập, các hành động ngoài danh sách không được phép.

### 2.6.2 Cấu trúc một MCP tool

```python
@tool(
    name="get_threat_summary",
    description="Lấy thông tin về các threat cấp host trong subnet của agent này",
    input_schema={}
)
async def get_threat_summary(args):
    # logic
    return {"content": [{"type": "text", "text": "..."}]}
```

Mỗi tool có ba thành phần:
- **Name**: tên duy nhất để LLM gọi
- **Description**: mô tả ngôn ngữ tự nhiên — LLM đọc để hiểu khi nào nên gọi
- **Input schema**: định nghĩa các tham số đầu vào (tên, kiểu, mô tả)

### 2.6.3 Vai trò trong đề tài

Đề tài sử dụng MCP để:

1. **Đóng gói tất cả hành động khả dụng thành tool** — thay vì để LLM tự sáng tạo action qua text response như trong bài báo [2], LLM phải gọi một trong các tool được khai báo trước.
2. **Cung cấp dữ liệu đã được decode** — thay vì nhồi vectơ 8-bit thô vào prompt, MCP tool trả về JSON đã decode → LLM không có cơ hội ảo giác về bit.

## 2.7 Khái niệm Rules of Engagement (RoE)

### 2.7.1 Định nghĩa

**Rules of Engagement (RoE — Quy tắc Giao chiến)** là khái niệm xuất phát từ lĩnh vực quân sự, mô tả các quy tắc cụ thể giới hạn khi nào và bằng cách nào lực lượng được phép sử dụng vũ lực. Trong ngữ cảnh AI an ninh mạng, RoE được hiểu là **tập các quy tắc tất định (deterministic rule) ràng buộc hành vi của tác nhân AI**, đảm bảo tác nhân không vượt qua các ranh giới an toàn do con người thiết lập.

### 2.7.2 Cơ sở lý luận

Khái niệm RoE trong đề tài này được rút ra từ nguyên lý **human-on-the-loop** và **tuân thủ các đánh đổi rủi ro** do con người thiết lập, đã được trình bày trong bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1].

### 2.7.3 Đặc điểm của RoE trong đề tài

RoE trong đề tài có các đặc điểm sau:

1. **Tất định (deterministic)**: viết bằng code Python, không phụ thuộc LLM diễn giải. Cùng đầu vào → cùng đầu ra.
2. **Có lý do (with reason)**: khi RoE từ chối một hành động, hệ thống trả về lý do bằng ngôn ngữ tự nhiên để LLM đọc và tự sửa sai.
3. **Có gợi ý thay thế (with suggested alternative)**: kèm gợi ý hành động hợp lệ thay thế.
4. **Hai loại rule**:
   - **Precondition rule**: kiểm tra trạng thái trước khi cho phép (vd: Restore chỉ allow khi compromise_level = "admin").
   - **Rate-limit rule**: giới hạn số lần dùng action (vd: tối đa 1 BlockTrafficZone/zone/episode).

### 2.7.4 Khác biệt với cơ chế Reward

| Khía cạnh | Reward Function (RL) | RoE |
|---|---|---|
| Loại tín hiệu | Số (scalar reward) | Cấu trúc (allow/deny + reason + suggested) |
| Tác nhân hiểu được? | Chỉ qua huấn luyện | Trực tiếp qua ngôn ngữ tự nhiên |
| Thời điểm áp dụng | Sau khi action thực thi | Trước khi action được commit |
| Sửa đổi | Phải retrain | Sửa code rule, không cần retrain |

## 2.8 Tổng kết và Khoảng trống nghiên cứu

### 2.8.1 Khoảng trống

Bài báo *Large Language Models are Autonomous Cyber Defenders* [2] đã:
- ✓ Chứng minh tính khả thi của LLM cho ACD.
- ✓ Xây dựng khung adapter LLM cho CybORG CAGE 4.
- ✓ Đề xuất giao thức truyền thông 8-bit giữa các blue agent.
- ✗ Không khắc phục được ba hạn chế: ảo giác, lệ thuộc prompt, thiếu reward direction.

Bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1] đã:
- ✓ Đề xuất nguyên lý human-on-the-loop và RoE cho ACD.
- ✗ Không tích hợp với tác nhân LLM cụ thể.
- ✗ Không có thực nghiệm trên môi trường mô phỏng.

**Khoảng trống**: chưa có công trình tích hợp đầu cuối **MCP + RoE** cho tác nhân LLM trong môi trường CybORG CAGE 4 nhằm khắc phục ba hạn chế của bài báo *Large Language Models are Autonomous Cyber Defenders* [2] dựa trên nguyên lý của bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1]. Đây chính là khoảng trống mà đề tài này hướng đến.

### 2.8.2 Định vị đề tài

Đề tài này **kế thừa**:
- Môi trường mô phỏng CybORG CAGE 4 và mã nguồn từ bài báo *Large Language Models are Autonomous Cyber Defenders* [2].
- Các biến thể red agent có sẵn (FiniteState, AggressiveFSM, StealthyFSM, ImpactFSM).
- Tác nhân RL KEEP làm baseline cho 4 blue agent còn lại.
- Phương pháp phân cụm reasoning bằng K-Means [2] §IV.E.

Đề tài này **mở rộng** bằng cách:
- Thay thế prompt-based action interface bằng MCP Tool Allow-list (giải quyết Hạn chế 2 phần ngữ nghĩa).
- Thêm Decoder pre-parse cho vectơ truyền thông 8-bit (giải quyết Hạn chế 1).
- Áp dụng RoE Rule Engine tất định dựa trên nguyên lý của [1] (giải quyết Hạn chế 2 phần ràng buộc).
- Thiết lập LLM ↔ RoE Feedback Loop để thay thế hàm phần thưởng (giải quyết Hạn chế 3).
