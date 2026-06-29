"""Paper-style prompt + parser (kiểu TH3 baseline).

Dùng cho Mode A (mcp_enabled=False, roe_enabled=False): nhồi toàn bộ
observation + raw 8-bit vào prompt, single shot, LLM trả về JSON action,
parse bằng regex như TH3 §III.B.

Reference: llms-are-acd-main/CybORG/Agents/LLMAgents/llm_policy.py:extract_action()
"""

import re


# ─── System prompt kiểu TH3 ──────────────────────────────────────────────────

PAPER_SYSTEM_PROMPT = """Bạn là một chuyên gia an ninh mạng cấp cao (blue agent) bảo vệ một subnet trong hệ thống doanh nghiệp đa mạng. Mục tiêu: phát hiện kẻ tấn công, ngăn chặn xâm phạm, và duy trì tính khả dụng dịch vụ.

# CÁC HÀNH ĐỘNG KHẢ DỤNG

Chọn MỘT hành động và trả lời bằng JSON: {"action": "<TênHànhĐộng host:<host> hoặc subnet:<zone>>", "reason": "..."}

Hành động:
- Sleep: không làm gì trong lượt này (thụ động)
- Monitor: quét thụ động các host (tự động chạy mỗi lượt — không cần gọi rõ)
- Analyse host:<hostname>: điều tra sâu một host để tìm hoạt động độc hại (không phá hủy)
- Remove host:<hostname>: chấm dứt các tiến trình user-level đáng ngờ trên một host
- Restore host:<hostname>: wipe và restore một host về trạng thái sạch (phá hủy — downtime tạm thời)
- DeployDecoy host:<hostname>: triển khai honeypot trên một host
- BlockTrafficZone subnet:<zone>: chặn toàn bộ traffic inbound từ một subnet (phá hủy — ảnh hưởng availability)
- AllowTrafficZone subnet:<zone>: cho phép lại traffic từ subnet đã bị chặn trước đó

# QUY TẮC MÔI TRƯỜNG (CybORG CAGE 4)

Bạn hoạt động trong CybORG CAGE 4 đa tác nhân. Nhiệm vụ diễn ra qua 3 pha: Planning, MissionA, MissionB. Mỗi pha áp dụng chính sách mạng khác nhau.

# ĐỊNH DẠNG VECTƠ TRUYỀN THÔNG (TỰ DECODE)

Mỗi 4 blue agent KHÁC phát đi một vectơ nhị phân 8-bit mỗi lượt:
- Bit 0-4: bit j được đặt = 1 nếu sender phát hiện hoạt động độc hại xuất phát từ subnet của agent j. Vị trí bit của chính sender luôn = 0.
- Bit 5-6: mức độ compromise BÊN TRONG subnet CỦA sender:
  - 00 = none
  - 01 = remote scan / exploit detected
  - 10 = user-level compromise (host có IOC cmd.sh / cmd.exe)
  - 11 = admin-level compromise (host có IOC escalate.sh / escalate.exe)
- Bit 7: 1 nếu sender đang bận thực thi action, 0 nếu rảnh.

Bạn phải tự decode các vectơ này bằng cách xem xét từng bit.

# HƯỚNG DẪN SUY LUẬN

- Điều tra trước khi phá hủy. Nếu không chắc về mức compromise, Analyse trước.
- Chỉ Restore khi admin-level compromise đã được xác nhận trên host.
- BlockTrafficZone là phương án cuối cùng — ảnh hưởng đến người dùng hợp pháp.
- Một đồng đội báo cáo admin compromise trong subnet CỦA BẠN là tín hiệu cần hành động: Analyse để xác nhận, sau đó Restore.

# ĐỊNH DẠNG OUTPUT

Trả lời chỉ bằng JSON hợp lệ. Ví dụ: {"action": "Analyse host:host_a", "reason": "điều tra IOC"}"""


def render_paper_observation(obs: dict, agent_name: str, last_action: str) -> str:
    """Format observation kiểu TH3 — text với raw 8-bit array."""
    lines = []
    lines.append("# QUAN SÁT")
    lines.append(f"Tên agent: {agent_name}")
    lines.append(f"Pha nhiệm vụ: {obs.get('phase', 'không rõ')}")
    lines.append(f"Hành động trước: {last_action}")
    lines.append(f"Trạng thái hành động trước: {obs.get('success', 'không rõ')}")
    lines.append("")
    lines.append("Vectơ truyền thông (8-bit thô, tự decode):")

    my_idx = int(agent_name[-1])
    other_indices = [i for i in range(5) if i != my_idx]
    for sender_idx, bits in zip(other_indices, obs.get("message", []) or []):
        binary = [1 if b else 0 for b in bits]
        lines.append(f"  Blue Agent {sender_idx}: {binary}")
    lines.append("")
    lines.append("Hoạt động đáng ngờ phát hiện:")

    for key, value in obs.items():
        if key in ("phase", "success", "action", "message"):
            continue
        if not isinstance(value, dict):
            continue
        hostname = value.get("System info", {}).get("Hostname", key)
        host_lines = [f"  Host: {hostname}"]
        for proc in value.get("Processes", []):
            if "PID" in proc and "username" not in proc:
                host_lines.append(f"    CẢNH BÁO: Tiến trình đáng ngờ PID={proc['PID']}")
        for f in value.get("Files", []):
            name = f.get("File Name")
            if name in ("escalate.sh", "escalate.exe"):
                host_lines.append(f"    NGUY HIỂM: IOC mức admin '{name}'")
            elif name in ("cmd.sh", "cmd.exe"):
                host_lines.append(f"    BÁO ĐỘNG: IOC mức user '{name}'")
        if len(host_lines) > 1:
            lines.extend(host_lines)

    lines.append("")
    lines.append("Chọn MỘT hành động. Trả lời chỉ bằng JSON.")
    return "\n".join(lines)


# ─── Parser — extract action từ text response của LLM ────────────────────────
# Logic tương đương llms-are-acd-main/CybORG/Agents/LLMAgents/llm_policy.py:extract_action()

VALID_ACTIONS = {
    "sleep", "monitor", "analyse", "remove", "restore",
    "deploydecoy", "blocktrafficzone", "allowtrafficzone",
}


def parse_paper_response(response_text: str) -> tuple:
    """Parse text response của LLM kiểu TH3.

    Returns: (action_type, params_dict, reason) hoặc None nếu parse fail.
    """
    if not response_text:
        return None

    lower = response_text.lower()

    # Tìm "action": "..."
    action_match = re.search(r'"action"\s*:\s*"([^"]+)"', lower)
    if not action_match:
        return None
    action_str = action_match.group(1).strip()

    # Tìm "reason": "..."
    reason_match = re.search(r'"reason"\s*:\s*"([^"]+)"', response_text)
    reason = reason_match.group(1).strip() if reason_match else ""

    # Detect action type
    parts = action_str.split()
    if not parts:
        return None
    action_token = parts[0].lower()

    # Map về CybORG action class name (chuẩn hoá viết hoa)
    action_map = {
        "sleep": "Sleep",
        "monitor": "Monitor",
        "analyse": "Analyse",
        "remove": "Remove",
        "restore": "Restore",
        "deploydecoy": "DeployDecoy",
        "blocktrafficzone": "BlockTrafficZone",
        "allowtrafficzone": "AllowTrafficZone",
    }

    if action_token not in action_map:
        return None
    action_type = action_map[action_token]

    # Parse params
    params = {}
    host_match = re.search(r"host:\s*([\w_\-]+)", action_str, re.IGNORECASE)
    if host_match:
        params["hostname"] = host_match.group(1)
    subnet_match = re.search(r"subnet:\s*([\w_\-]+)", action_str, re.IGNORECASE)
    if subnet_match:
        params["target_zone"] = subnet_match.group(1)

    return (action_type, params, reason)
