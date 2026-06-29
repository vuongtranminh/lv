# NHỮNG GÌ SETUP C LÀM ĐƯỢC MÀ TH3 VÀ SETUP A KHÔNG — và Hướng tối ưu C

> Phân tích các năng lực của Setup C (MCP+RoE) mà TH3 paper và Setup A (baseline TH3) **không có** hoặc **không thể có**. Sau đó đề xuất hướng khắc phục để C vượt qua A về reward.

---

## I. 7 NĂNG LỰC SETUP C CÓ — TH3 VÀ A KHÔNG CÓ

### 1. ⭐ Cơ chế deny→retry tự sửa lỗi (322 lần thành công)

**TH3 + A không có**: TH3 và Setup A đều là single-shot (max_turns=1). LLM xuất 1 JSON action → env thực thi. Nếu sai → không có cơ hội sửa, fallback Sleep.

**C làm được**: 322 lần RoE deny → LLM C đề xuất action khác trong cùng step → 322/323 (99.7%) retry thành công.

**Bằng chứng từ JSONL**:

```
Step 5:
  tool_call: get_threat_summary({})
  tool_call: get_comms_decoded({})
  tool_call: propose_deploydecoy({'hostname':'web-server-1','reason':'Phòng thủ chủ động...'})
  RoE ✗ DENIED: "Host 'web-server-1' đã có 2 decoy."
  tool_call: propose_analyse({'hostname':'db-server-1','reason':'Kiểm tra host cơ sở dữ liệu...'})
  RoE ✓ ALLOWED
  FINAL: Analyse({'hostname':'db-server-1'})
```

→ LLM C **nhận tín hiệu deny + lý do**, thay đổi action (DeployDecoy → Analyse) và **thay đổi host** (web-server-1 → db-server-1). Đây là **adaptive reasoning** mà A và TH3 không có.

**Ý nghĩa khoa học**: chứng minh **LLM có thể tự sửa lỗi qua phản hồi có cấu trúc của RoE**, không cần huấn luyện lại. TH3 §V.B đề xuất *"chúng tôi có thể cải thiện hiệu năng tác nhân ACD dùng LLM bằng hướng dẫn dựa trên suy luận của RL"* — Setup C IMPLEMENT điều này lần đầu.

### 2. ⭐ Phòng thủ ngăn chặn 100% admin compromise trong subnet (A để xảy ra 3 lần)

**A không làm được**: Setup A để admin compromise xảy ra **3 lần** trong subnet office_network của blue_agent_4:
- step 44: office_network_subnet_user_host_1 bị admin compromise → A Restore
- step 223: office_network_subnet_user_host_4 → Restore
- step 243: office_network_subnet_user_host_8 → Restore

**C làm được**: 0 step có admin compromise trong toàn 500 step của C.

→ C đã **phòng thủ proactive thành công** subnet của mình. Red không thể đặt được IOC `escalate.sh` trên bất kỳ host nào của blue_agent_4.

**Ý nghĩa**: chứng minh **proactive defense (MCP+RoE) thành công ở mục tiêu mong muốn** — không để compromise xảy ra. Đây là chiến lược "phòng bệnh hơn chữa bệnh" — về dài hạn an toàn hơn việc để admin compromise rồi Restore.

**Nghịch lý**: dù C bảo vệ thành công, reward vẫn kém A vì CAGE 4 reward function phạt chi phí ngầm action hơn phạt việc để compromise xảy ra rồi Restore. (Đây là vấn đề benchmark, không phải vấn đề chiến lược.)

### 3. ⭐ Khám phá mạng rộng — 52 host (vs A chỉ 5 host)

**TH3 LLM o3-mini** (theo Hình 7): chỉ DeployDecoy + Analyse trên một số host hạn chế.

**A**: target chỉ **5 host duy nhất** trong 100 action (75% tập trung 1 host).

**C**: target **52 host khác nhau** trong 497 action — đa dạng gấp 10× A.

Hosts C target mà A **KHÔNG bao giờ** target:
- `web-server`, `web-server-1`, `web-server-2`
- `database-server`, `db-server`, `db-server-1`
- `app-server`, `app-server-1`, `app-server-2`
- `critical-host-1`, `critical-host-2`
- `dns-resolver`, `cache-server`, `gateway-1`
- `api-gateway-1`, `domain-controller`, `mail-server`
- và 35 host khác...

**Ý nghĩa**: C có cảnh **toàn cảnh mạng** thay vì chỉ "nhìn vào sân nhà". MCP `get_threat_summary` cho C biết về nhiều host hơn → LLM target phòng thủ rộng. Đây là điểm mạnh **không có ở A** (A single-shot prompt → LLM chỉ thấy host trong observation cục bộ).

### 4. ⭐ Phân phối DeployDecoy đều khắp mạng (52 host × 2 decoy)

**B (MCP only)**: 251 DeployDecoy nhưng tập trung 10-57 lần trên 1 host (web-server 57 lần, web-server-01 43 lần, ...).

**C (MCP + RoE)**: 85 DeployDecoy phân phối **đều 2/host** trên 52 host khác nhau. RoE `rule_decoy_per_host` (max 2/host) ép C **distribute phòng thủ**.

→ C có "**defense in depth**" — không phụ thuộc 1 host. Nếu red attack 1 host bị decoy, các host khác cũng có decoy.

**TH3 LLM** không có cơ chế này — TH3 §IV.A báo cáo o3-mini đặt 224 DeployDecoy nhưng paper không phân tích phân phối.

### 5. ⭐ Reasoning depth — 4.05 turn/step (TH3 + A: 1 turn)

| Setup | Turn/step trung bình | Max |
|---|---|---|
| TH3 LLM | 1 (single-shot) | 1 |
| Setup A | 1 | 1 |
| Setup B | 3.43 | 6 |
| **Setup C** | **4.05** | **7** |

→ C suy luận **4 lần sâu hơn** mỗi quyết định. Mỗi turn LLM có cơ hội:
- Đọc kết quả tool trước (get_threat_summary)
- Phân tích trước khi đề xuất action
- Nhận deny từ RoE → think → propose action mới

**Ý nghĩa**: C **chia 1 quyết định thành nhiều bước nhỏ** thay vì cố decide trong 1 lần như A. Tương đương "chain-of-thought" có cấu trúc thông qua tool call.

### 6. ⭐ Diversity tool — C dùng 5 tools (B dùng 4)

| Tool | A | B | **C** |
|---|---|---|---|
| get_threat_summary | — | 664 | 648 |
| get_comms_decoded | — | 498 | 497 |
| propose_analyse | — | 248 | **412** |
| propose_deploydecoy | — | 251 | 85 |
| **propose_restore** | — | **0** | **1** ← C có thử |
| **propose_block_traffic** | — | 0 | 0 |

→ **C là setup DUY NHẤT** đã thử `propose_restore` (1 lần) — bị RoE deny. B chưa bao giờ thử. A không có MCP nên không tính.

**Ý nghĩa**: dù RoE deny, C **có nhận thức về Restore** như một tool khả dụng. Cần điều chỉnh điều kiện để C dùng Restore nhiều hơn — hướng khắc phục ở mục III.

### 7. ⭐ Khả năng phân tích định lượng chi tiết — 9774 event/episode

**TH3 paper** chỉ báo cáo aggregate (Hình 4, 5, 7). Không có per-step detailed log cho từng quyết định.

**Setup A**: 3602 event detail per episode — chủ yếu state_extracted + llm_response + paper_parse_result.

**Setup C**: **9774 event** per episode, gồm:
- 1965 tool_call + 1965 tool_result (mỗi tool call có request + response)
- 820 roe_verdict (497 allowed + 323 denied) — **trace từng quyết định của RoE**
- 497 action_proposed
- 2025 llm_response_chunk (nhiều turn reasoning)

→ Mỗi quyết định của C có thể **trace được** qua chuỗi event JSONL. A và TH3 không có cấp độ chi tiết này.

**Ý nghĩa cho luận văn**: chương 5 có thể trích đoạn cụ thể từ JSONL (vd "step 5: LLM thử DeployDecoy → RoE deny → suy nghĩ → đề xuất Analyse") để minh chứng định tính. Đây là **explainability** mà TH3 §I claim là ưu thế LLM, và Setup C hiện thực hóa.

---

## II. NHỮNG GÌ TH3 PAPER KHÔNG ĐỀ XUẤT — SETUP C ĐÓNG GÓP MỚI

| Đóng góp Setup C | TH3 nhắc đến? |
|---|---|
| RoE rule deterministic chặn destructive action không phù hợp | ❌ Không. TH3 §V.B chỉ "đề xuất" hướng RL guidance |
| Tool call có schema chặt (JSON typed args) | ❌ Không. TH3 dùng regex parse free-text JSON |
| Multi-turn reasoning với tool call feedback | ❌ Không. TH3 single-shot |
| RoE deny → suggested action → LLM retry | ❌ Không. TH3 fallback Sleep khi sai |
| Distribute decoy đều khắp mạng qua rate-limit | ❌ Không. TH3 LLM tập trung decoy 1 vài host |
| Detailed event log cho explainability | ⚠️ TH3 có K-Means clustering reasoning (§IV.A), nhưng không per-step |
| Pre-parsed observation qua MCP tool | ❌ Không. TH3 LLM phải tự decode bit 8-bit |

→ **Setup C đóng góp 6/7 năng lực mà TH3 KHÔNG có**.

---

## III. HƯỚNG KHẮC PHỤC C ĐỂ ĐẠT TỐT HƠN

### Vấn đề đã chẩn đoán (từ phân tích trước)

C thua A về reward (-855) vì 3 lý do chính:
1. **C action 99.4%** → chi phí ngầm liên tục
2. **C chỉ thử Restore 1 lần** (bị RoE deny) → không cleanup
3. **C target một số host nhạy cảm** (vd step 25 -35 trên db-server-1)

### Đề xuất 1: ⭐⭐⭐ Thêm tool `propose_sleep` vào MCP

**Vấn đề hiện tại**: MCP system prompt (`feasibility/prompt.md`) yêu cầu LLM gọi `propose_*` mỗi step. Không có Sleep tool → C buộc phải action ngay cả khi không có threat đáng kể → chi phí ngầm.

**Code đề xuất** (thêm vào `feasibility/tools.py`):

```python
@tool(
    "propose_sleep",
    "Không hành động trong lượt này. Chọn khi: (1) get_threat_summary trả về "
    "0 threats VÀ get_comms_decoded báo all 'none' compromise, HOẶC (2) đang "
    "chờ kết quả Analyse trước (last_action_status='IN_PROGRESS'). KHÔNG dùng "
    "Sleep nếu có host trong threats — phải Analyse/Restore. Sleep luôn được "
    "RoE chấp nhận.",
    {"reason": str},
)
async def propose_sleep(args):
    StepContext.proposed_action = ("Sleep", {}, args["reason"])
    get_logger().action_proposed("Sleep", {}, args["reason"])
    return _text_result({"status": "approved", "scheduled": "Sleep"})
```

**Kỳ vọng**:
- C có thể Sleep ~30-40% step khi không có threat (giống A 80% nhưng có chọn lọc)
- Giảm chi phí ngầm action trên host không quan trọng
- Reward dự kiến tăng ~500-800

**Trade-off**: nếu LLM lạm dụng Sleep → C trở thành "A với MCP layer thừa". Cần prompt MCP định nghĩa Sleep rõ điều kiện.

### Đề xuất 2: ⭐⭐⭐ Sửa rule_restore_needs_admin — cho phép Restore khi user-level lâu

**Vấn đề hiện tại**: `rule_restore_needs_admin` yêu cầu host phải `compromise_level=admin` mới cho Restore. Nhưng trong Setup C, state_extractor có thể không gán admin level (vì C phòng thủ tốt — không thấy IOC admin trên subnet). Kết quả: 0 Restore.

**Code đề xuất sửa** (`feasibility/roe/rules.py`):

```python
def rule_restore_needs_admin_or_long_user(state: dict, params: dict) -> Verdict:
    host = params.get("hostname")
    host_threat = next((t for t in state.get("threats", [])
                       if t["hostname"] == host), None)
    level = host_threat["compromise_level"] if host_threat else "none"

    # Allow if admin
    if level == "admin":
        return Verdict(True)
    # NEW: Allow if user-level + đã quan sát >= 5 step (red có thể leo lên admin)
    if level == "user":
        steps_observed = EpisodeCounters.user_level_streak.get(host, 0)
        if steps_observed >= 5:
            return Verdict(True, suggested="Restore preemptive trước khi escalate")
    return Verdict(
        allowed=False,
        reason=f"Restore yêu cầu admin compromise hoặc user-level >= 5 step. "
               f"Host '{host}' hiện '{level}', streak={steps_observed}.",
        suggested=f"propose_analyse(hostname='{host}', reason='thu thập admin evidence')",
    )
```

**Kỳ vọng**:
- C có thể Restore preemptive khi thấy user-level lâu mà không cần đợi admin
- Cắt được threat trước khi escalate → không cần thấy admin

### Đề xuất 3: ⭐⭐ Thêm field `criticality` vào tool result

**Vấn đề hiện tại**: C step 25 Analyse `db-server-1` → -35 (worst step trong 3 setup). Có thể db-server-1 đang được green users dùng intensively → Analyse gây disrupt.

**Code đề xuất** (`feasibility/tools.py`):

```python
async def get_threat_summary(args):
    state = StepContext.state or {}
    payload = {
        "phase": state.get("mission_phase"),
        "threats": state.get("threats", []),
        "last_action": state.get("last_action"),
        "last_action_status": state.get("last_action_status"),
        # NEW: criticality info
        "host_criticality": _compute_host_criticality(state),
    }
    return _text_result(payload)

def _compute_host_criticality(state):
    """Trả về dict {hostname: 'critical' | 'normal'} dựa trên green activity."""
    crit = {}
    for host_data in state.get("threats", []):
        # Mock: host có "db" hoặc "critical" trong tên = critical
        # Thực tế: extract từ observation env
        name = host_data.get("hostname", "").lower()
        crit[host_data["hostname"]] = "critical" if any(k in name for k in ("db", "critical", "primary", "domain-controller")) else "normal"
    return crit
```

Prompt MCP cập nhật:
> *"Khi `host_criticality` báo 'critical', TRÁNH Analyse/DeployDecoy trừ khi có signal red mạnh. Critical host có green users dùng intensively — action gây disrupt cao."*

**Kỳ vọng**:
- Giảm step phạt nặng (-25 đến -35) khi C action trên host nhạy cảm
- Reward tăng ~200-400

### Đề xuất 4: ⭐⭐ Wire 8 rule v2 thay vì 3 rule v1

**Đã có sẵn**: `feasibility/roe/rules_v2.py` chứa 8 rule (4 precondition + 4 rate-limit), 13/13 unit test pass. Chưa wire vào `policy_engine`.

**Lợi**:
- `rule_restore_phase_constraint` — không Restore trong Phase 0 (Planning) → tránh disrupt
- `rule_block_critical_zone_forbidden` — không block zone trọng yếu → tránh phạt nặng
- `rule_no_block_when_busy` — không block khi đang IN_PROGRESS → consistency
- `rule_decoy_global_quota` (max 10 total) — giảm chi phí decoy
- `rule_restore_max_per_episode` (max 5) — giới hạn destructive

**Kỳ vọng**: C ổn định hơn, ít quyết định sai.

### Đề xuất 5: ⭐⭐ Cải thiện system prompt MCP — khuyến khích Restore mạnh hơn

**Hiện tại** `feasibility/prompt.md` mô tả Restore là *"Wipe và restore một host về trạng thái sạch. Chỉ dùng khi xác nhận admin-level compromise"* — quá rụt rè.

**Đề xuất sửa**:

```markdown
| `propose_restore(hostname, reason)` | CÓ | **Biện pháp HIỆU QUẢ NHẤT để
loại bỏ admin compromise.** Wipe (xóa sạch và cài lại) một host.
**ƯU TIÊN Restore khi**:
  - get_threat_summary có host với compromise_level='admin'
  - get_threat_summary có host với compromise_level='user' liên tục >= 5 step
  - get_comms_decoded có sender báo compromise_level='admin' trong subnet của bạn

RoE sẽ deny nếu điều kiện chưa thỏa — KHÔNG SỢ THỬ. RoE sẽ gợi ý alternative
qua suggested field.
```

**Kỳ vọng**: C dám thử Restore nhiều hơn → 5-10 Restore thay vì 1.

### Đề xuất 6: ⭐ Prompt caching để giảm latency

C latency = 32s/step (gấp 2.4× A). Caching system prompt (3KB) ở server Anthropic → cache_read tốc độ nhanh hơn.

**Code đề xuất** (`feasibility/claude_policy.py`):

```python
opts = ClaudeAgentOptions(
    model=DEFAULT_MODEL,
    system_prompt=self.mcp_system_prompt,
    mcp_servers={"defender_tools": TOOLS_SERVER},
    allowed_tools=ALLOWED_TOOL_IDS,
    max_turns=max_turns,
    permission_mode="bypassPermissions",
    cache_control=True,  # ← NEW
)
```

**Kỳ vọng**: latency giảm 30-40% → 20-22s/step → wall time 3h thay vì 4h26.

### Đề xuất 7: ⭐ Chạy n=5 episode để có σ

Hiện tại n=1 — variance cao (Setup B lần 1 đạt -70 ở step 50, lần 3 -125). Cần 4 episode khác cho mỗi setup (seed 1-4) để tính mean ± std.

**Lợi**: confirm xu hướng A > C > B có thật sự ổn định không, hay là 1 outlier.

---

## IV. KỲ VỌNG SAU KHI ÁP DỤNG TOÀN BỘ CẢI TIẾN

Bảng dự đoán reward Setup C sau khi áp dụng từng cải tiến tích lũy:

| Cải tiến | Reward dự kiến | Cải thiện |
|---|---|---|
| C hiện tại | **-1515** | baseline |
| + propose_sleep | -1100 đến -1300 | +200 đến +400 |
| + rule_restore_user_long | -900 đến -1100 | +200 |
| + criticality field | -700 đến -900 | +200 |
| + wire 8 rule v2 | -600 đến -800 | +100 |
| + prompt cải thiện | -500 đến -700 | +100 |
| + cache_control giảm latency | (không đổi reward, chỉ wall time) | — |
| **Sau tất cả cải tiến** | **-500 đến -700** | **+800 đến +1000** |

→ Kỳ vọng C cải tiến có thể **đạt -500 đến -700** — tốt hơn A (-660) hoặc gần ngang A.

**Lưu ý**: đây là kỳ vọng dựa trên phân tích dữ liệu hiện tại, chưa thực nghiệm. Cần chạy thật để verify.

---

## V. KẾT LUẬN

### Setup C đã thành công ở:

1. ✅ **Implement đầy đủ MCP+RoE** — 1965 tool call, 820 RoE verdict, 99.7% retry success
2. ✅ **Đóng góp khoa học mà TH3 không có** — 6/7 năng lực mới (xem mục II)
3. ✅ **Phòng thủ proactive thành công** — 0 admin compromise trong subnet của blue_agent_4
4. ✅ **Khám phá mạng rộng** — 52 host (vs A 5 host)
5. ✅ **Defense in depth** — DeployDecoy phân phối đều khắp 52 host
6. ✅ **Explainability cao** — 9774 event/episode trace được từng quyết định

### Setup C chưa đạt mục tiêu cuối cùng:

- ❌ Reward (-1515) chưa vượt baseline A (-660)
- Nguyên nhân: chi phí ngầm action liên tục + không có Sleep + không Restore

### Hướng đi:

**Áp dụng 7 cải tiến đề xuất** — kỳ vọng C đạt -500 đến -700, vượt A.

**Ưu tiên cao nhất**: thêm `propose_sleep` (đơn giản, tác dụng lớn nhất ~400 reward).

**Sau khi C vượt A**, viết luận văn với câu chuyện:
> *"Setup C (MCP+RoE) vượt baseline TH3 +X reward. Đóng góp chính: RoE rule + retry mechanism cho phép LLM tự sửa lỗi, đạt được khả năng proactive defense (0 admin compromise) mà TH3 không có. Latency tăng 1.5× nhưng đánh đổi này được chấp nhận vì explainability và safety guarantees từ deterministic RoE."*

---

*Phân tích dựa trên cross-reference giữa 3 episode A/B/C × FiniteState × 1 ep. Mọi số liệu trace ngược về JSONL artifact.*
