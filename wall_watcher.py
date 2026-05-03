#!/usr/bin/env python3
"""The Wall — firewall log watcher for The Citadel.

Monitors UFW logs via journalctl, classifies threat state,
and writes status to a file for Waybar/agent consumption.

States: IDLE / WATCHING / BLOCKED / STORM
"""

import json
import subprocess
import time
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

STATUS_FILE = Path.home() / "cyberdeck" / "wall_status.json"
POLL_INTERVAL = 5  # seconds between checks
STORM_THRESHOLD = 10  # blocks in window = STORM
WATCHING_THRESHOLD = 3  # blocks in window = WATCHING
WINDOW_SECONDS = 60  # rolling time window

# Pattern to parse UFW BLOCK lines
UFW_PATTERN = re.compile(
    r'\[UFW (\w+)\].*?SRC=(\S+).*?DST=(\S+)'
    r'.*?PROTO=(\S+).*?DPT=(\d+)'
)


def get_recent_blocks():
    """Fetch recent UFW log entries via journalctl."""
    try:
        r = subprocess.run(
            ["sudo", "journalctl", "-k",
             "--grep=UFW", "--since",
             f"-{WINDOW_SECONDS}s",
             "--no-pager", "-o", "short-iso"],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip().split("\n") if r.stdout.strip() else []
    except Exception as e:
        print(f"journalctl error: {e}", file=sys.stderr)
        return []


def parse_block(line):
    """Parse a UFW log line into structured data."""
    m = UFW_PATTERN.search(line)
    if not m:
        return None
    return {
        "action": m.group(1),
        "src": m.group(2),
        "dst": m.group(3),
        "proto": m.group(4),
        "dpt": int(m.group(5)),
    }


def classify_state(blocks):
    """Classify threat state based on block count."""
    n = len(blocks)
    if n >= STORM_THRESHOLD:
        return "STORM"
    elif n >= WATCHING_THRESHOLD:
        return "WATCHING"
    elif n > 0:
        return "BLOCKED"
    else:
        return "IDLE"


def summarize_blocks(blocks):
    """Summarize blocked connections by source IP."""
    by_src = defaultdict(list)
    for b in blocks:
        by_src[b["src"]].append(b)
    summary = []
    for src, hits in sorted(
            by_src.items(),
            key=lambda x: -len(x[1])):
        ports = sorted(set(h["dpt"] for h in hits))
        summary.append({
            "src": src,
            "count": len(hits),
            "ports": ports[:5],
            "proto": hits[0]["proto"],
        })
    return summary[:5]  # top 5 sources


def write_status(state, blocks, summary):
    """Write status JSON for Waybar and agent."""
    status = {
        "state": state,
        "blocks_in_window": len(blocks),
        "window_seconds": WINDOW_SECONDS,
        "top_sources": summary,
        "updated": datetime.now().isoformat(timespec="seconds"),
    }
    STATUS_FILE.write_text(json.dumps(status, indent=2))
    return status


def format_display(status):
    """Format status for terminal display."""
    icons = {
        "IDLE": "🟢", "BLOCKED": "🟡",
        "WATCHING": "🟠", "STORM": "🔴"
    }
    icon = icons.get(status["state"], "⚪")
    line = f'{icon} {status["state"]}'
    line += f' | {status["blocks_in_window"]} blocks/{WINDOW_SECONDS}s'
    if status["top_sources"]:
        top = status["top_sources"][0]
        line += f' | top: {top["src"]} ({top["count"]}x)'
    return line


def main():
    print("=== THE WALL ===")
    print(f"Monitoring UFW logs every {POLL_INTERVAL}s")
    print(f"Window: {WINDOW_SECONDS}s | Storm: >={STORM_THRESHOLD} | Watching: >={WATCHING_THRESHOLD}")
    print(f"Status file: {STATUS_FILE}\n")

    prev_state = None
    while True:
        try:
            raw_lines = get_recent_blocks()
            blocks = []
            for line in raw_lines:
                parsed = parse_block(line)
                if parsed:
                    blocks.append(parsed)

            state = classify_state(blocks)
            summary = summarize_blocks(blocks)
            status = write_status(state, blocks, summary)

            display = format_display(status)
            if state != prev_state:
                print(f"[STATE CHANGE] {prev_state} -> {state}")
            print(display)
            prev_state = state

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\nWall standing down.")
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
