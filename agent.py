#!/usr/bin/env python3
"""The Citadel Agent — local AI command interpreter.

Layer 2 of The Citadel stack. Runs on the deck's NPU
(or CPU on test platform). Handles:
- System commands via local LLM
- Firewall status via wall_status.json
- VPN tunnel management
- Home brain queries over WireGuard
"""

import json
import subprocess
import requests
import sys
from pathlib import Path

# Local LLM (deck brain — small, fast, command interpreter)
LOCAL_OLLAMA = "http://localhost:11434/api/generate"
LOCAL_MODEL = "qwen2.5:0.5b"

# Home LLM (home brain — big, powerful, over VPN)
HOME_OLLAMA = "http://10.0.0.1:11434/api/generate"
HOME_MODEL = "gemma3:12b"

VPN_INTERFACE = "home-vpn"
WALL_STATUS = Path.home() / "cyberdeck" / "wall_status.json"

# Fast-path keywords (skip LLM entirely)
WALL_KEYWORDS = {"wall", "firewall", "knocking", "security", "blocked", "threats", "attacks"}
TUNNEL_UP_KEYWORDS = {"tunnel up", "tunnel home", "vpn up", "connect home"}
TUNNEL_DOWN_KEYWORDS = {"tunnel down", "vpn down", "disconnect"}
TUNNEL_STATUS_KEYWORDS = {"tunnel status", "vpn status", "tunnel"}
HOME_KEYWORDS = {"ask home", "home brain", "think hard", "ask big"}

SYSTEM_PROMPT = """You are The Citadel Agent, a command interpreter for a sovereign Linux deck.

Your job: receive short user input and decide what to do.

You MUST respond with ONLY valid JSON, no other text. Response format:
{"action": "execute", "command": "shell command here", "narration": "what I'm doing"}
{"action": "answer", "narration": "direct answer"}

Examples:
User: "status"
{"action": "execute", "command": "uptime && free -h && df -h /", "narration": "Checking system status"}

User: "what time is it"
{"action": "execute", "command": "date", "narration": "Checking clock"}

RULES:
- Respond with ONLY JSON. No markdown.
- One JSON object per response.
- Keep commands safe. Never rm -rf, never format disks.
- Never use sudo unless checking logs with journalctl.
- Keep narrations under 10 words."""


def match_keywords(text, keyword_set):
    """Check if text matches any keyword phrase."""
    lower = text.lower().strip()
    for kw in keyword_set:
        if kw in lower:
            return True
    return False


def check_wall_keywords(text):
    words = set(text.lower().split())
    return bool(words & WALL_KEYWORDS)


def read_wall_status():
    """Read wall_status.json and return human summary."""
    try:
        data = json.loads(WALL_STATUS.read_text())
        state = data.get("state", "UNKNOWN")
        blocks = data.get("blocks_in_window", 0)
        window = data.get("window_seconds", 60)
        sources = data.get("top_sources", [])
        updated = data.get("updated", "unknown")
        icons = {"IDLE": "🟢", "BLOCKED": "🟡",
                 "WATCHING": "🟠", "STORM": "🔴"}
        icon = icons.get(state, "⚪")
        lines = [f"{icon} Wall: {state}"]
        lines.append(f"  {blocks} blocks in last {window}s")
        if sources:
            for s in sources:
                ports = ", ".join(str(p) for p in s.get("ports", []))
                lines.append(f"  {s['src']}: {s['count']}x on port {ports}")
        else:
            lines.append("  No threats detected")
        lines.append(f"  Last update: {updated}")
        return "\n".join(lines)
    except FileNotFoundError:
        return "⚪ Wall: OFFLINE — wall_watcher not running"
    except Exception as e:
        return f"⚪ Wall: ERROR — {e}"


def tunnel_status():
    """Check VPN tunnel status."""
    try:
        r = subprocess.run(
            ["ip", "link", "show", VPN_INTERFACE],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and "UP" in r.stdout:
            try:
                requests.get("http://10.0.0.1:11434/", timeout=3)
                return "🟢 Tunnel: UP — home brain reachable"
            except Exception:
                return "🟡 Tunnel: UP — home brain unreachable"
        else:
            return "🔴 Tunnel: DOWN"
    except Exception:
        return "⚪ Tunnel: UNKNOWN"


def tunnel_up():
    """Bring up the VPN tunnel."""
    r = subprocess.run(
        ["sudo", "wg-quick", "up", VPN_INTERFACE],
        capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        return "🟢 Tunnel activated"
    elif "already exists" in r.stderr:
        return "🟢 Tunnel already up"
    return f"🔴 Tunnel failed: {r.stderr.strip()}"


def tunnel_down():
    """Bring down the VPN tunnel."""
    r = subprocess.run(
        ["sudo", "wg-quick", "down", VPN_INTERFACE],
        capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        return "🔴 Tunnel deactivated"
    return f"⚪ Tunnel error: {r.stderr.strip()}"


def ask_home_brain(question):
    """Send a question to the home brain (gemma3:12b over VPN)."""
    try:
        r = requests.post(HOME_OLLAMA, json={
            "model": HOME_MODEL,
            "prompt": question,
            "stream": False,
            "options": {"num_predict": 500}
        }, timeout=120)
        r.raise_for_status()
        return r.json().get("response", "No response from home brain")
    except requests.ConnectionError:
        return "🔴 Cannot reach home brain — is the tunnel up?"
    except requests.Timeout:
        return "🟡 Home brain timed out — try a simpler question"
    except Exception as e:
        return f"⚪ Home brain error: {e}"


def ask_llm(user_input):
    """Send input to local Ollama and get JSON response."""
    try:
        r = requests.post(LOCAL_OLLAMA, json={
            "model": LOCAL_MODEL,
            "prompt": user_input,
            "system": SYSTEM_PROMPT, "stream": False,
            "options": {"temperature": 0.1, "num_predict": 150}
        }, timeout=60)
        r.raise_for_status()
        raw = r.json().get("response", "").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"action": "answer",
                "narration": f"LLM parse error: {raw[:200]}"}
    except requests.RequestException as e:
        return {"action": "answer",
                "narration": f"Cannot reach Ollama: {e}"}


def run_command(cmd):
    """Execute a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=15)
        output = result.stdout.strip()
        if result.stderr.strip():
            output += "\n" + result.stderr.strip()
        if not output:
            output = f"[exit code {result.returncode}]"
        return output
    except subprocess.TimeoutExpired:
        return "[command timed out after 15s]"
    except Exception as e:
        return f"[error: {e}]"


def main():
    print("=== THE CITADEL ===")
    print("Agent ready. Type commands or 'quit' to exit.")
    print("  'ask home <question>' to query the home brain\n")

    while True:
        try:
            user_input = input("deck> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nShutting down.")
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Shutting down.")
            break

        # Fast paths (no LLM needed)
        if check_wall_keywords(user_input):
            print("  [Checking the wall]")
            print(f"  {read_wall_status()}\n")
            continue

        if match_keywords(user_input, TUNNEL_UP_KEYWORDS):
            print("  [Activating tunnel]")
            print(f"  {tunnel_up()}\n")
            continue

        if match_keywords(user_input, TUNNEL_DOWN_KEYWORDS):
            print("  [Deactivating tunnel]")
            print(f"  {tunnel_down()}\n")
            continue

        if match_keywords(user_input, TUNNEL_STATUS_KEYWORDS):
            print("  [Checking tunnel]")
            print(f"  {tunnel_status()}\n")
            continue

        if match_keywords(user_input, HOME_KEYWORDS):
            # Strip the keyword prefix to get the question
            question = user_input
            for kw in HOME_KEYWORDS:
                if question.lower().startswith(kw):
                    question = question[len(kw):].strip()
                    break
            if not question:
                question = user_input
            print(f"  [Asking home brain: {question[:60]}...]")
            response = ask_home_brain(question)
            print(f"  {response}\n")
            continue

        # Everything else goes to the local LLM
        decision = ask_llm(user_input)
        action = decision.get("action", "answer")
        narration = decision.get("narration", "")

        if action == "execute":
            cmd = decision.get("command", "")
            print(f"  [{narration}]")
            print(f"  $ {cmd}")
            output = run_command(cmd)
            print(f"  {output}\n")
        else:
            print(f"  {narration}\n")


if __name__ == "__main__":
    main()
