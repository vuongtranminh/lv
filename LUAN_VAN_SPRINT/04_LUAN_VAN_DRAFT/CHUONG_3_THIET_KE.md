# CHƯƠNG 3 — THIẾT KẾ HỆ THỐNG ĐỀ XUẤT

## 3.1 Kiến trúc tổng thể

### 3.1.1 Sơ đồ tổng quan

Kiến trúc đề xuất tích hợp 4 thành phần chính vào vòng lặp quyết định mỗi step của blue agent:

```
   CybORG observation (raw, có vectơ 8-bit thô)
            │
            ▼
   ┌────────────────────────┐
   │ Decoder Pre-parse      │ ← decode bit → JSON
   │ (state_extractor.py)   │   giải quyết Hạn chế 1
   └────────────────────────┘
            │ structured state (JSON)
            ▼
   ┌────────────────────────┐
   │ StepContext            │ ← shared state singleton
   │ (context.py)           │
   └────────────────────────┘
            │
            ▼
   ┌─── In-process MCP Server (defender_tools) ────────────┐
   │                                                         │
   │  Observation tools (read-only):                         │
   │    • get_threat_summary()                               │
   │    • get_comms_decoded()                                │
   │                                                         │
   │  Action proposal tools (Allow-list, qua RoE):           │
   │    • propose_analyse(hostname, reason)                  │
   │    • propose_restore(hostname, reason)                  │
   │    • propose_deploy_decoy(hostname, reason)             │
   │    • propose_block_traffic(target_zone, reason)         │
   │                                                         │
   │  → giải quyết Hạn chế 2 (phần ngữ nghĩa action)         │
   └─────────────────────────────────────────────────────────┘
            │ tool calls
            ▼
   ┌────────────────────────────────┐
   │ Claude Haiku 4.5               │ ← LLM Agent
   │ (qua claude-agent-sdk)         │
   └────────────────────────────────┘
            │ propose_* tool calls
            ▼
   ┌────────────────────────┐
   │ RoE Policy Engine      │ ← rule deterministic
   │ (policy_engine.py)     │   giải quyết Hạn chế 2 (phần ràng buộc)
   └────────────────────────┘
            │ allow/deny verdict
            ▼
   ┌────────────────────────┐
   │ LLM ↔ RoE Feedback     │ ← thay thế hàm phần thưởng
   │ Loop                   │   giải quyết Hạn chế 3
   └────────────────────────┘
            │
            ▼
   ┌────────────────────────┐
   │ Audit Log (CSV)        │ ← reproducibility
   │ (audit.py)             │
   └────────────────────────┘
            │
            ▼
   CybORG Action (Restore / Analyse / DeployDecoy / BlockTrafficZone)
```

### 3.1.2 Bảng đối chiếu giải quyết 3 hạn chế

| Hạn chế trong [2] | Thành phần giải quyết | Cơ chế |
|---|---|---|
| Ảo giác đọc vectơ truyền thông | Decoder Pre-parse | Decode bit deterministic trước khi LLM thấy |
| Lệ thuộc prompt cho định nghĩa action (ngữ nghĩa) | MCP Tool Allow-list | Schema cứng, không thể tự sáng tạo action |
| Lệ thuộc prompt (ràng buộc hành vi) | RoE Rule Engine | Logic Python deterministic, không qua LLM |
| Thiếu định hướng phần thưởng | LLM ↔ RoE Feedback Loop | Allow/deny + reason + suggested thay reward |

## 3.2 Decoder Pre-parse — Giải quyết Hạn chế 1

### 3.2.1 Định dạng vectơ truyền thông 8-bit (theo TH3 [2])

CybORG CAGE 4 yêu cầu các blue agent broadcast một vectơ nhị phân 8 bit mỗi lượt. Cấu trúc:

| Vị trí bit | Số bit | Ý nghĩa | Giá trị |
|---|---|---|---|
| 0-4 | 5 | Sender phát hiện malice từ subnet agent $j$ (bit $j$ = 1) | 0/1 cho mỗi agent (bit của chính sender = 0) |
| 5-6 | 2 | Mức compromise trong subnet sender | 00=none, 01=remote_exploit, 10=user, 11=admin |
| 7 | 1 | Sender đang bận thực thi action | 0=free, 1=busy |

### 3.2.2 Thuật toán decode

```python
COMPROMISE_LEVELS = ["none", "remote_exploit", "user", "admin"]

def decode_commvector(bits, from_agent_idx, my_agent_idx):
    # Bit 0-4: ai báo có malice ở mạng nào
    reports = []
    for j in range(5):
        if j == from_agent_idx:
            continue                          # bỏ qua bit của chính sender
        if bits[j] == 1:
            reports.append(f"blue_agent_{j}")

    # Bit 5-6: mức compromise (ghép 2 bit thành số 0-3)
    level_idx = (bits[5] << 1) | bits[6]

    return {
        "from": f"blue_agent_{from_agent_idx}",
        "reports_malicious_in_other_networks": reports,
        "compromise_level_in_sender_net": COMPROMISE_LEVELS[level_idx],
        "sender_busy": bool(bits[7]),
    }
```

### 3.2.3 Ví dụ minh họa

**Đầu vào**: vectơ thô `[0, 0, 0, 0, 0, 1, 1, 1]` từ `blue_agent_2`.

**Đầu ra JSON**:
```json
{
  "from": "blue_agent_2",
  "reports_malicious_in_other_networks": [],
  "compromise_level_in_sender_net": "admin",
  "sender_busy": true
}
```

→ LLM đọc trực tiếp JSON tiếng người, không phải decode bit. Không có cơ hội ảo giác về vị trí bit, mức compromise, hay sender busy.

### 3.2.4 Vai trò trong giải quyết Hạn chế 1

So sánh với bài báo [2]:

| Bài báo [2] (LLM phải tự decode) | Đề tài (đã decode trước) |
|---|---|
| `Commvector Blue Agent 2 Message: [0,0,0,0,0,1,1,1]` | `{"compromise_level_in_sender_net": "admin", "sender_busy": true}` |

**Cơ chế giải quyết**: thay vì sửa hành vi của LLM bằng prompt (đắt và không đảm bảo), decoder Python loại bỏ vấn đề ở tầng kiến trúc. LLM không bao giờ chạm bit thô, do đó không có cơ hội ảo giác về việc decode.

## 3.3 MCP Tool Allow-list — Giải quyết Hạn chế 2 (phần ngữ nghĩa)

### 3.3.1 Hai loại tool

Đề tài cung cấp 6 MCP tool, chia thành 2 loại:

#### Observation tools (read-only, luôn cho phép)

| Tool | Mô tả |
|---|---|
| `get_threat_summary()` | Trả về danh sách threats trong subnet của agent (pre-parse từ observation) |
| `get_comms_decoded()` | Trả về danh sách 4 vectơ đồng đội đã decode thành JSON |

#### Action proposal tools (qua RoE validate)

| Tool | Phá hủy? | Trạng thái RoE |
|---|---|---|
| `propose_analyse(hostname, reason)` | Không | Luôn allow |
| `propose_restore(hostname, reason)` | Có (gây downtime) | Cần admin-level compromise |
| `propose_deploy_decoy(hostname, reason)` | Không (về availability) | Tối đa 2 decoy/host/episode |
| `propose_block_traffic(target_zone, reason)` | Có (ngắt traffic) | Tối đa 1 block/zone/episode |

### 3.3.2 Schema MCP cho tool

Mỗi tool có schema cứng theo định dạng JSON Schema. Ví dụ:

```python
@tool(
    "propose_restore",
    "Wipe và restore một host về trạng thái sạch. PHÁ HỦY — tạm thời đưa "
    "host offline, ảnh hưởng đến người dùng hợp pháp. Chính sách RoE: "
    "yêu cầu xác nhận admin-level compromise trên host.",
    {"hostname": str, "reason": str},
)
async def propose_restore(args):
    return _propose("Restore", {"hostname": args["hostname"]}, args["reason"])
```

LLM phải:
- Gọi đúng tên tool (`propose_restore`).
- Cung cấp đầy đủ tham số kiểu chính xác (`hostname: str`, `reason: str`).
- Không thể tự sáng tạo tool ngoài danh sách (vd `propose_force_restore_with_admin_override`).

### 3.3.3 In-process MCP server

Tất cả tool được đăng ký vào một MCP server chạy nội bộ (in-process):

```python
TOOLS_SERVER = create_sdk_mcp_server(
    name="defender_tools",
    version="1.0.0",
    tools=[
        get_threat_summary, get_comms_decoded,
        propose_analyse, propose_restore,
        propose_deploy_decoy, propose_block_traffic,
    ],
)
```

Lợi ích của in-process:
- Không cần spawn process riêng → giảm overhead.
- Truy cập trực tiếp `StepContext` (shared state).
- Cho phép logging chi tiết I/O của tool để audit.

### 3.3.4 Vai trò trong giải quyết Hạn chế 2 (phần ngữ nghĩa)

So sánh với bài báo [2]:

| Bài báo [2] | Đề tài |
|---|---|
| LLM trả lời JSON `{"action": "Restore host:host_a", ...}` trong response text | LLM gọi function `propose_restore(hostname="host_a", reason="...")` qua MCP |
| Có thể sai cú pháp, sai tên action, sai tham số | Schema enforcement — sai sẽ không gọi được tool |
| Định nghĩa action trong prompt (vd `Remove` dễ bị diễn giải sai) | Định nghĩa action trong tool description + schema — không thể "hiểu nhầm" |

**Cơ chế giải quyết**: chuyển từ "LLM tự sáng tạo action qua text" sang "LLM chọn từ danh sách tool có sẵn". Tên action, kiểu tham số, ý nghĩa đều cứng, không phụ thuộc cách viết prompt.

## 3.4 RoE Rule Engine — Giải quyết Hạn chế 2 (phần ràng buộc)

### 3.4.1 Cấu trúc Verdict

Mỗi rule trả về một `Verdict` chứa:

```python
@dataclass
class Verdict:
    allowed: bool          # True/False
    reason: str = ""       # Lý do (chỉ có khi denied)
    suggested: str = ""    # Gợi ý action thay thế (chỉ có khi denied)
```

### 3.4.2 EpisodeCounters cho ràng buộc trạng thái

Một số rule cần theo dõi số lần dùng action xuyên step (rate limit). Đề tài dùng class `EpisodeCounters` lưu các bộ đếm này, reset đầu mỗi episode:

```python
class EpisodeCounters:
    blocks_per_zone: dict = {}      # {"restricted_zone_a": 1, ...}
    decoys_per_host: dict = {}      # {"host_a": 2, ...}

    @classmethod
    def reset(cls):
        cls.blocks_per_zone = {}
        cls.decoys_per_host = {}

    @classmethod
    def record_block(cls, zone):
        cls.blocks_per_zone[zone] = cls.blocks_per_zone.get(zone, 0) + 1

    @classmethod
    def record_decoy(cls, host):
        cls.decoys_per_host[host] = cls.decoys_per_host.get(host, 0) + 1
```

### 3.4.3 Phân loại rule

Đề tài có **8 rule** chia thành 2 loại:

#### Precondition rule (4 rule)

Kiểm tra điều kiện đối với trạng thái trước khi cho phép action.

| Rule | Action | Điều kiện cho phép |
|---|---|---|
| `rule_restore_needs_admin` | Restore | compromise_level của host = "admin" |
| `rule_restore_phase_constraint` | Restore | không Restore trong phase Planning (chưa đến nhiệm vụ) |
| `rule_block_critical_zone_forbidden` | BlockTrafficZone | không block giữa 2 vùng vận hành |
| `rule_no_block_when_busy` | BlockTrafficZone | agent không ở trạng thái busy |

#### Rate-limit rule (4 rule)

Giới hạn số lần dùng action xuyên episode.

| Rule | Action | Giới hạn |
|---|---|---|
| `rule_block_rate_limit` | BlockTrafficZone | tối đa 1 lần/zone/episode |
| `rule_decoy_per_host` | DeployDecoy | tối đa 2 lần/host/episode |
| `rule_decoy_global_quota` | DeployDecoy | tối đa 10 decoy tổng/episode |
| `rule_restore_max_per_episode` | Restore | tối đa 5 lần/episode |

### 3.4.4 Cơ chế thẩm định

Mỗi propose_* tool gọi `RoE.validate()` trước khi commit:

```python
def _propose(action_type, params, reason):
    verdict = policy_engine.validate(action_type, params, StepContext.state)

    if verdict.allowed:
        StepContext.proposed_action = (action_type, params, reason)
        policy_engine.record_action(action_type, params)
        return _text_result({"status": "approved", "scheduled": ...})

    # Deny: trả structured reason cho LLM
    StepContext.rejected_attempts.append((action_type, target, verdict.reason))
    return _text_result({
        "status": "denied",
        "reason": verdict.reason,
        "suggested": verdict.suggested,
    })
```

### 3.4.5 Ví dụ một rule cụ thể

```python
def rule_restore_needs_admin(state, params):
    """Restore là phá hủy — chỉ cho phép khi xác nhận admin-level compromise."""
    host = params.get("hostname")
    if not host:
        return Verdict(False, "Restore yêu cầu một hostname.")

    host_threat = next(
        (t for t in state.get("threats", []) if t["hostname"] == host),
        None,
    )
    level = host_threat["compromise_level"] if host_threat else "none"

    if level != "admin":
        return Verdict(
            allowed=False,
            reason=f"Restore yêu cầu xác nhận admin-level compromise; "
                   f"host '{host}' hiện đang ở mức '{level}'.",
            suggested=f"propose_analyse(hostname='{host}', "
                      f"reason='thu thập thêm bằng chứng')",
        )
    return Verdict(True)
```

### 3.4.6 Vai trò trong giải quyết Hạn chế 2 (phần ràng buộc)

Trong bài báo [2], hành vi của LLM bị chi phối bởi cách viết prompt — vd nếu prompt nói "Restore quan trọng nhất, dùng khi nghi ngờ", LLM sẽ Restore vô tội vạ; nếu prompt nói "Restore gây tổn hại", LLM sẽ tránh Restore quá đáng.

Đề tài giải quyết bằng cách **chuyển ràng buộc ra ngoài LLM**: RoE rule viết bằng Python, không phụ thuộc LLM diễn giải prompt. Cho dù prompt viết thế nào, Restore vẫn không thể fire khi compromise_level chưa phải admin.

## 3.5 LLM ↔ RoE Feedback Loop — Giải quyết Hạn chế 3

### 3.5.1 Cơ chế deny + reason + suggested

Khi RoE từ chối, tool result trả về cho LLM có 3 trường:

```json
{
  "status": "denied",
  "reason": "Restore yêu cầu xác nhận admin-level compromise; host 'host_a' hiện đang ở mức 'user'.",
  "suggested": "propose_analyse(hostname='host_a', reason='thu thập thêm bằng chứng')"
}
```

### 3.5.2 Vòng lặp self-correction

Sơ đồ luồng xử lý:

```
LLM đề xuất Restore host_a (compromise = user)
        │
        ▼
RoE.validate() → denied (vì user, không phải admin)
        │
        ▼
Tool trả về JSON {status: denied, reason: "...", suggested: "propose_analyse..."}
        │
        ▼
LLM đọc reason (bằng ngôn ngữ tự nhiên)
        │
        ▼
LLM suy luận: "À, mình chưa đủ admin. Phải analyse trước."
        │
        ▼
LLM gọi propose_analyse(host_a) → allowed
        │
        ▼
Final action: Analyse host_a
```

### 3.5.3 Vai trò trong giải quyết Hạn chế 3

Trong RL, tín hiệu định hướng là **reward số** — agent học sau hàng nghìn episode để liên kết action với reward. LLM không có cơ chế học từ reward; cần một tín hiệu **trực tiếp hiểu được** ngay trong cùng episode.

Đề tài thay thế reward bằng **feedback structured từ RoE**:
- **Allow** → tương đương reward dương.
- **Deny + reason** → tương đương reward âm + giải thích lý do.
- **Suggested alternative** → hướng dẫn LLM action nào nên thử thay thế.

Khác biệt then chốt với RL reward: LLM **hiểu được ngay tức thì** thông qua ngôn ngữ tự nhiên, không cần học qua nhiều episode.

## 3.6 Audit Log và Reproducibility

### 3.6.1 Cấu trúc audit log

Mỗi step ghi 1 dòng vào CSV với các cột sau:

| Cột | Kiểu | Mô tả |
|---|---|---|
| `timestamp` | ISO 8601 | Thời điểm log |
| `step` | int | Chỉ số step trong episode |
| `agent` | str | Tên blue agent |
| `phase` | str | Planning / MissionA / MissionB |
| `threats_count` | int | Số threat phát hiện |
| `comms_count` | int | Số comm vector nhận được |
| `llm_reasoning` | str | Text reasoning Claude (truncate 500 char) |
| `proposed_action` | str | Action LLM đề xuất |
| `roe_rejections` | str | Danh sách rejection (nếu có) |
| `final_action` | str | Action thực thi cuối cùng |

### 3.6.2 Mục đích sử dụng

Audit log phục vụ ba mục đích:

1. **Phân tích định lượng** — tính các metric: Invalid Action Rate, RoE Deny Rate, etc.
2. **Phân tích định tính** — clustering reasoning bằng K-Means.
3. **Debug và reproducibility** — chạy lại episode với cùng input.

### 3.6.3 Tái lập thí nghiệm

Toàn bộ thí nghiệm có thể tái lập bằng các bước:

```bash
git clone https://github.com/<username>/feasibility-mcp-roe
cd llms-are-acd-main && ./install_unified.sh
source cage-env/bin/activate
cd ../feasibility-mcp-roe && pip install -r requirements.txt
claude /login                              # 1 lần
python3 run_all_scenarios.py               # 4 kiểm thử khả thi
python3 benchmark/run_benchmark.py --all   # benchmark đầy đủ
python3 benchmark/analyze_clustering.py    # phân tích định tính
```

Tất cả seed, version, config được cố định để đảm bảo kết quả lặp lại được.
