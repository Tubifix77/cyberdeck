#!/usr/bin/env python3
"""Waybar custom module for The Wall.
Reads wall_status.json, outputs Waybar JSON format.

Waybar config entry:
"custom/wall": {
    "exec": "~/cyberdeck/waybar_wall.py",
    "return-type": "json",
    "interval": 5
}
"""

import json
import sys
from pathlib import Path

WALL_STATUS = Path.home() / "cyberdeck" / "wall_status.json"

ICONS = {"IDLE": "🟢", "BLOCKED": "🟡", "WATCHING": "🟠", "STORM": "🔴"}
CLASSES = {"IDLE": "idle", "BLOCKED": "blocked", "WATCHING": "watching", "STORM": "storm"}

try:
    data = json.loads(WALL_STATUS.read_text())
    state = data.get("state", "UNKNOWN")
    blocks = data.get("blocks_in_window", 0)
    sources = data.get("top_sources", [])
    icon = ICONS.get(state, "⚪")
    text = f"{icon} {state}"
    if blocks > 0:
        text += f" ({blocks})"

    tooltip = f"Wall: {state}\n{blocks} blocks in last 60s"
    if sources:
        for s in sources:
            ports = ", ".join(str(p) for p in s.get("ports", []))
            tooltip += f"\n{s['src']}: {s['count']}x port {ports}"

    output = {
        "text": text,
        "tooltip": tooltip,
        "class": CLASSES.get(state, "unknown"),
    }
except Exception:
    output = {"text": "⚪ OFFLINE", "tooltip": "Wall watcher not running", "class": "offline"}

print(json.dumps(output))
