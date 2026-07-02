"""Regenerate .md files từ base.yml (single source of truth).

Chạy khi:
- TH3 update `acd2025/base.yml` (chưa xảy ra, nhưng phòng khi)
- setup_c_override.py thay đổi

Usage:
    python feasibility/prompts/regenerate_md.py
"""

import sys
import yaml
from pathlib import Path

# Cho phép import feasibility từ project root
PROJ = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJ))

from feasibility.setup_c_override import build_setup_c_prompt


BASE_YML = Path(__file__).parent / "acd2025" / "base.yml"
BASE_MD = Path(__file__).parent / "acd2025" / "base.md"
SETUP_C_FINAL_MD = Path(__file__).parent / "setup_c_final.md"


def main():
    with open(BASE_YML, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    content = doc["prompts"][0]["content"]

    # Setup A prompt (byte-identical TH3 content)
    BASE_MD.write_text(content, encoding="utf-8")
    print(f"✓ Wrote {BASE_MD.name} ({len(content)} chars, {content.count(chr(10))} lines)")

    # Setup C prompt (2 chỗ thay thế)
    c_prompt = build_setup_c_prompt(content)
    SETUP_C_FINAL_MD.write_text(c_prompt, encoding="utf-8")
    print(f"✓ Wrote {SETUP_C_FINAL_MD.name} ({len(c_prompt)} chars, {c_prompt.count(chr(10))} lines)")

    print(f"\nDelta Setup C vs A: +{len(c_prompt) - len(content)} chars, "
          f"+{c_prompt.count(chr(10)) - content.count(chr(10))} lines")


if __name__ == "__main__":
    main()
