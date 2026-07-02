"""Setup A driver — dùng nguyên bản TH3 prompt (acd2025/base.yml), single-shot JSON.

Load YAML, extract trường `content`, dùng làm system prompt. LLM output JSON theo
instruction có sẵn trong TH3 prompt: {"action": "...", "reason": "..."}. Parse
bằng regex.
"""

import re
import yaml
from pathlib import Path


TH3_BASE_YML = Path(__file__).parent / "prompts" / "acd2025" / "base.yml"


def load_th3_base_prompt() -> str:
    """Load acd2025/base.yml và extract system prompt content (byte-identical với TH3)."""
    with open(TH3_BASE_YML, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return doc["prompts"][0]["content"]


def render_paper_observation(obs: dict, agent_name: str, last_action: str) -> str:
    """Format observation theo `# OBSERVATION STRUCTURE` trong TH3 base.yml.

    Structure:
        Mission Phase: <phase>
        Last Action: <action>
        Last Action Status: <status>

        Communication Vectors:
        Commvector Blue Agent 0 Message: <value>
        ...

        Suspicious Activity Detected:
        - <hostname>: <activity>
    """
    lines = []
    lines.append("# OBSERVATION")
    lines.append(f"Mission Phase: {obs.get('phase', 'unknown')}")
    lines.append(f"Last Action: {last_action}")
    lines.append(f"Last Action Status: {obs.get('success', 'UNKNOWN')}")
    lines.append("")
    lines.append("Communication Vectors:")

    # 4 blue agent khác (không phải mình)
    my_idx = int(agent_name[-1])
    other_indices = [i for i in range(5) if i != my_idx]
    for sender_idx, bits in zip(other_indices, obs.get("message", []) or []):
        binary = [1 if b else 0 for b in bits]
        lines.append(f"Commvector Blue Agent {sender_idx} Message: {binary}")
    lines.append("")

    # Suspicious Activity
    activities = []
    for key, value in obs.items():
        if key in ("phase", "success", "action", "message"):
            continue
        if not isinstance(value, dict):
            continue
        # Trích IOC nếu có
        files = value.get("Files", []) or []
        procs = value.get("Processes", []) or []
        info = value.get("System info", {}) or {}
        host = info.get("Hostname", key)

        marks = []
        for f in files:
            name = f.get("File Name", "") if isinstance(f, dict) else ""
            if "escalate" in name.lower():
                marks.append("CRITICAL")
            elif "cmd" in name.lower():
                marks.append("ALERT")
            elif name:
                marks.append("INFO")
        for p in procs:
            n = p.get("Process Name", "") if isinstance(p, dict) else ""
            if "malicious" in n.lower() or "reverseshell" in n.lower():
                marks.append("ALERT")
        if marks:
            level = "CRITICAL" if "CRITICAL" in marks else (
                "ALERT" if "ALERT" in marks else (
                    "WARNING" if "WARNING" in marks else "INFO"))
            activities.append(f"- {host}: {level}")

    if activities:
        lines.append("Suspicious Activity Detected:")
        lines.extend(activities)
    else:
        lines.append("Suspicious Activity Detected: None")

    return "\n".join(lines)


def parse_paper_response(response_text: str) -> tuple:
    """Parse TH3 JSON response.

    Returns: (action_type, params_dict, reason) hoặc None nếu parse fail.
    """
    if not response_text:
        return None

    lower = response_text.lower()

    action_match = re.search(r'"action"\s*:\s*"([^"]+)"', lower)
    if not action_match:
        return None
    action_str = action_match.group(1).strip()

    reason_match = re.search(r'"reason"\s*:\s*"([^"]+)"', response_text)
    reason = reason_match.group(1).strip() if reason_match else ""

    parts = action_str.split()
    if not parts:
        return None
    action_token = parts[0].lower()

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

    params = {}
    host_match = re.search(r"host:\s*([\w_\-]+)", action_str, re.IGNORECASE)
    if host_match:
        params["hostname"] = host_match.group(1)
    subnet_match = re.search(r"subnet:\s*([\w_\-]+)", action_str, re.IGNORECASE)
    if subnet_match:
        params["target_zone"] = subnet_match.group(1)

    return (action_type, params, reason)
