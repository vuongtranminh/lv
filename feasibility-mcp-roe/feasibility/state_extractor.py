"""Decode raw CybORG observation into a structured JSON state.

This is the deterministic pre-parser that addresses Limitation 1 (comms-vector
hallucination). The LLM never sees the 8-bit binary array; it queries the
decoded JSON via the `get_comms_decoded` tool.

Comms-vector protocol (from TH3 paper, §III.C):
- Bits 0-4: sender sets bit j=1 if it detects malice originating in agent j's network
- Bits 5-6: compromise level inside the sender's own subnet
            00=none, 01=remote-exploit/scan, 10=user-level, 11=admin-level
- Bit 7:    sender is busy (awaiting action completion)
"""

COMPROMISE_LEVELS = ["none", "remote_exploit", "user", "admin"]

IOC_USER = {"cmd.sh", "cmd.exe"}
IOC_ADMIN = {"escalate.sh", "escalate.exe"}


def decode_commvector(bits, from_agent_idx: int, my_agent_idx: int) -> dict:
    """Decode an 8-bit comm vector from `from_agent_idx`."""
    reports = []
    for j in range(5):
        if j == from_agent_idx:
            continue
        if bits[j] == 1:
            reports.append(f"blue_agent_{j}")

    level_idx = (bits[5] << 1) | bits[6]

    return {
        "from": f"blue_agent_{from_agent_idx}",
        "reports_malicious_in_other_networks": reports,
        "compromise_level_in_sender_net": COMPROMISE_LEVELS[level_idx],
        "sender_busy": bool(bits[7]),
    }


def extract_threats(observation: dict) -> list:
    """Walk per-host observation entries, extract IOC files and suspicious
    processes. Compromise level inferred from file IOCs (CAGE 4 conventions).
    """
    threats = []
    for key, value in observation.items():
        if key in ("success", "action", "phase", "message"):
            continue
        if not isinstance(value, dict):
            continue

        hostname = value.get("System info", {}).get("Hostname", str(key))
        host = {
            "hostname": hostname,
            "compromise_level": "none",
            "iocs": [],
            "suspicious_processes": 0,
            "connections": [],
        }

        for proc in value.get("Processes", []):
            if "PID" in proc and "username" not in proc:
                host["suspicious_processes"] += 1
            for conn in proc.get("Connections", []):
                if "remote_address" in conn:
                    host["connections"].append(str(conn["remote_address"]))

        for f in value.get("Files", []):
            name = f.get("File Name")
            if name in IOC_ADMIN:
                host["compromise_level"] = "admin"
                host["iocs"].append(name)
            elif name in IOC_USER:
                if host["compromise_level"] != "admin":
                    host["compromise_level"] = "user"
                host["iocs"].append(name)

        if host["iocs"] or host["suspicious_processes"] > 0:
            threats.append(host)

    return threats


def extract_all_hostnames(observation: dict) -> list:
    """Trả về danh sách TẤT CẢ hostname có trong observation.

    Khác `extract_threats` (chỉ trả host có IOC). Mục đích: cung cấp cho LLM
    danh sách hostname HỢP LỆ để khi gọi propose_* không bịa tên (vd
    'web-server' thay vì 'office_network_subnet_user_host_1').
    """
    hostnames = []
    for key, value in (observation or {}).items():
        if key in ("success", "action", "phase", "message"):
            continue
        if not isinstance(value, dict):
            continue
        hostname = value.get("System info", {}).get("Hostname", str(key))
        if hostname not in hostnames:
            hostnames.append(hostname)
    return hostnames


def extract_state(observation, agent_name: str, last_action: str) -> dict:
    """Top-level: CybORG raw observation → structured JSON state."""
    if observation is None:
        return {
            "agent_name": agent_name,
            "mission_phase": "unknown",
            "last_action": last_action,
            "last_action_status": "unknown",
            "comms": [],
            "threats": [],
            "all_hostnames": [],
        }

    my_idx = int(agent_name[-1])
    other_indices = [i for i in range(5) if i != my_idx]

    commvectors = observation.get("message", []) or []
    comms = []
    for sender_idx, raw_bits in zip(other_indices, commvectors):
        bits = [1 if x else 0 for x in raw_bits]
        comms.append(decode_commvector(bits, sender_idx, my_idx))

    return {
        "agent_name": agent_name,
        "mission_phase": observation.get("phase", "unknown"),
        "last_action": last_action,
        "last_action_status": observation.get("success", "unknown"),
        "comms": comms,
        "threats": extract_threats(observation),
        "all_hostnames": extract_all_hostnames(observation),
    }
