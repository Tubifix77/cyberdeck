# Cyberdeck 2026 — Architecture Document
## Codename: "The Citadel"

> **Status:** Phases 1–3 complete (software tested). Awaiting hardware for final integration.
> **Author:** Tue Boas + Claude (Anthropic)
> **Date:** 2026-05-03

---

## 0. Origin — The 1980s Cyberdeck, Reimagined

### What the cyberdeck was

The cyberdeck originated in 1980s cyberpunk fiction — most notably William Gibson's *Neuromancer* (1984). It was a portable computer that gave its operator capabilities beyond what was available through normal channels: direct neural interface to cyberspace, the ability to bypass corporate security systems, and total independence from institutional infrastructure. The cyberdeck was not a consumer product. It was a tool of autonomy — often illegal, always personal, and entirely under the operator's control.

The core functionalities of the fictional cyberdeck were:

- **Immersive private display** — only the operator could see the interface
- **Local processing power** — the deck computed on its own, not on someone else's mainframe
- **Network penetration and defense** — the operator could see and interact with network security in real time
- **Encrypted communication** — secure channels to allies and home systems
- **Portability** — carried in a bag or built into clothing, used anywhere

### What that looks like in 2026

| 1984 Fiction | 2026 Reality |
|---|---|
| Neural interface headset | AR glasses (micro-OLED, USB-C, presents as a monitor) |
| Local processing deck | ARM SBC with dedicated AI accelerator (NPU) |
| Cyberspace visualization | Godot shader overlay responding to real firewall data |
| ICE and countermeasures | nftables firewall with real-time log monitoring |
| Encrypted comms to home base | WireGuard VPN tunnel to home server |
| Portable form factor | SBC inside a keyboard shell, battery-powered |

### How to achieve it

The cyberdeck in 2026 is a sovereign streaming client. The most powerful computer the operator owns stays at home (a desktop with a real GPU running large AI models). The deck is a small, encrypted, invisible interface to that home brain — carried anywhere, displayed through glasses only the operator can see, protected by a firewall whose state is rendered as ambient light at the edges of vision. For simple commands, the deck thinks locally on its own NPU. For real intelligence, it tunnels home.

This is not a laptop replacement. It is a specialized instrument: private, encrypted, sovereign.

---

## 1. Hardware Platform

### Compute: Orange Pi 5 Plus (16GB)
- **SoC:** Rockchip RK3588 — 4x Cortex-A76 @ 2.4GHz + 4x Cortex-A55 @ 1.8GHz
- **RAM:** 16GB LPDDR4x (soldered, not upgradeable)
- **NPU:** 6 TOPS, 3-core architecture, INT8 inference via RKLLM runtime
- **GPU:** Mali-G610 MP4 — OpenGL ES 3.2, Vulkan 1.1 (Panthor/PanVK open-source driver)
- **Display out:** USB-C with DisplayPort Alt Mode + 2x HDMI 2.1
- **Storage:** M.2 NVMe slot (Gen4), 512GB SSD
- **Network:** 2x 2.5GbE, M.2 E-key for WiFi 6 module

### Display: RayNeo Air 3s AR Glasses
- 1920x1080 per eye, 120Hz, micro-OLED
- USB-C input (standard DisplayPort) — presents as a normal external monitor to Linux
- Built-in speakers for audio output
- No special driver or software required

### NPU Capabilities and Constraints
- **Supported models:** Up to ~1.5B parameters for responsive inference
- **Benchmarked performance:**
  - Qwen2 0.5B: ~42 tokens/sec
  - TinyLlama 1.1B: 10–15 tokens/sec
  - DeepSeek R1 1.5B (distilled): ~15 tokens/sec
- **Quantization:** W8A8 only (no W4A16 on RK3588)
- **Max context:** 2048 tokens (RKLLM runtime limitation)
- **Model conversion:** Requires x86 machine. HuggingFace → RKNN format via RKNN-Toolkit2

### GPU Capabilities and Constraints
- Vulkan 1.1 conformant via PanVK (Collabora open-source driver)
- Vulkan stability in practice is mixed — OpenGL ES is the safer rendering path
- Adequate for 2D overlays, shader effects, and status dashboards
- Not suitable for heavy 3D particle systems or AAA-style effects

### Bill of Materials (May 2026, EU pricing)

| Component | Choice | Price (DKK) |
|---|---|---|
| SBC | Orange Pi 5 Plus 16GB | 960–1410 kr |
| Storage | 512GB M.2 NVMe | ~410 kr |
| AR Glasses | RayNeo Air 3s | 2300–3720 kr |
| WiFi Module | M.2 E-key WiFi 6 (AX200/AX210) | ~110 kr |
| Power Bank | 65W USB-C PD, 20000mAh | 300–600 kr |
| Keyboard | Any USB or Bluetooth keyboard | Existing or 0–1120 kr |
| **Minimum total** | SBC + SSD + Glasses + WiFi | **~4250 kr** |
| **Comfortable total** | Adding power bank, case, keyboard | **~5600 kr** |

---

## 2. Software Architecture

### Base OS
Armbian (Debian-based Linux for RK3588). Application layers are built on top.

### Architecture Overview

```
┌─────────────────────────────────────────────┐
│                THE CITADEL                   │
├─────────────────────────────────────────────┤
│  Layer 5: Interface — "The Deck"            │
│    Sway compositor, Waybar, terminal,       │
│    keyboard-driven workflow                 │
├─────────────────────────────────────────────┤
│  Layer 4: Network — "The Tunnel"            │
│    WireGuard VPN, Tailscale mesh,           │
│    IWD wireless, hardware kill switch       │
├─────────────────────────────────────────────┤
│  Layer 3: Security — "The Wall"             │
│    nftables firewall, log watcher daemon,   │
│    Godot shader overlay, Waybar widget      │
├─────────────────────────────────────────────┤
│  Layer 2: Intelligence — "The Agent"        │
│    RKLLM runtime, 0.5–1.5B model on NPU,   │
│    command interpreter, home brain relay    │
├─────────────────────────────────────────────┤
│  Layer 1: Display — "The Lens"              │
│    USB-C DP auto-detection, Sway config,    │
│    deck-mode toggle on glasses plug/unplug  │
├─────────────────────────────────────────────┤
│  Layer 0: Armbian (Debian Linux for RK3588) │
│    Panthor GPU driver, RKLLM NPU runtime,   │
│    standard Linux userspace                 │
└─────────────────────────────────────────────┘
```

---

### Layer 1: Display — "The Lens"

**Purpose:** Manage the AR glasses as the primary workspace.

The glasses present as a standard USB-C DisplayPort monitor. Linux detects them automatically.

**Components:**
- Sway compositor configuration tuned for single 1080p display (font sizes, contrast, tiling layout)
- `udev` rule to detect glasses plug/unplug events
- Shell script to toggle "deck mode" — switches workspace layout, font scaling, and color scheme when glasses connect
- Fallback to HDMI output for desk use when glasses are disconnected

**Future:** Optional head-tracking via XRLinuxDriver (converts glass gyroscope data to viewport movement). Not required for core functionality.

---

### Layer 2: Intelligence — "The Agent"

**Purpose:** A local AI command interpreter running on the NPU, with relay capability to the home brain.

**Components:**
- RKLLM runtime (v1.2+) for NPU-accelerated inference (Ollama on test platform)
- Model: Qwen2-0.5B or TinyLlama-1.1B (converted to RKNN format)
- `agent.py` — Python service accepting text input
- Keyword fast-paths for wall status, tunnel management, and home brain queries (bypass LLM for reliability)
- LLM path for general commands: natural language → JSON decision → shell execution or direct answer

**Agent capabilities (tested and working):**
- System commands: "status," "how much ram is free," "what time is it" → LLM picks the right shell command
- Wall status: "firewall," "who's knocking," "security" → instant status from wall_status.json
- Tunnel management: "tunnel home," "tunnel down," "tunnel status" → WireGuard up/down/status
- Home brain: "ask home <question>" → query gemma3:12b on home PC over WireGuard VPN

**For tasks beyond 1.5B model capability:** Encrypted tunnel to home PC (RTX 3080 + Ollama) over WireGuard for access to gemma3:12b or larger models.

---

### Layer 3: Security — "The Wall"

**Purpose:** Firewall monitoring with visual and physical feedback.

**Text layer (Phase 1 — complete):**
- `nftables` / `ufw` as the firewall
- `wall_watcher.py` — Python daemon tailing UFW logs via `journalctl`, polling every 5 seconds
- Classifies state: IDLE / BLOCKED / WATCHING / STORM (based on block count in 60-second rolling window)
- Writes `wall_status.json` — shared state consumed by the agent, Waybar, and Godot
- `citadel-wall.service` — systemd unit keeping the daemon alive
- `waybar_wall.py` — Waybar custom module outputting JSON with text, tooltip, and CSS class

**Visual layer (Phase 2 — complete):**
- Godot 4.6.2 scene in OpenGL ES compatibility mode
- Fullscreen transparent overlay on the display
- 2D fbm noise shader creating organic flame effect at screen edges
- Shader uniforms driven by `wall_status.json` via GDScript controller (reads file every 2 seconds)
- Four visual states with smooth lerp transitions:
  - IDLE: faint blue embers at edges (5% opacity)
  - BLOCKED: warm amber glow (30% intensity)
  - WATCHING: bright orange (60% intensity)
  - STORM: red flare with rapid pulse (100% intensity)

---

### Layer 4: Network — "The Tunnel"

**Purpose:** Encrypted connectivity to home network and mesh capability.

**Components (tested and working):**
- **WireGuard** — VPN tunnel to home network. Subnet: 10.0.0.1 (home PC) / 10.0.0.2 (deck). Port 51820/UDP. Home PC's Ollama API reachable at `http://10.0.0.1:11434/`.
- Config: `/etc/wireguard/home-vpn.conf` on deck, WireGuard app on home PC.
- Agent integration: "tunnel home" / "tunnel down" / "tunnel status" commands.

**Planned (needs real hardware):**
- **Tailscale** (optional) — zero-config mesh for multi-device access
- **IWD** (iNet Wireless Daemon) — lightweight wireless management, replaces NetworkManager
- **Kill switch** — physical button wired to GPIO, executes `rfkill block all` to hard-cut all radios

---

### Layer 5: Interface — "The Deck"

**Purpose:** The user experience in the glasses.

**Components:**
- **Sway** — tiling Wayland compositor, keyboard-driven, no mouse required
- **Foot** or **Alacritty** — GPU-accelerated terminal emulator
- **Waybar** — status bar showing: wall state (via custom/wall module), WiFi signal, VPN status, battery, NPU load, time
- **Custom keybindings** — everything is a hotkey or a typed command to the Agent

**Design principle:** Zero mouse dependency. Every action is reachable by keyboard. The entire UX is built around typed commands and tiled windows.

---

## 3. Build Phases

### Phase 0: Hardware Proof of Concept — NOT STARTED
**Buy:** Orange Pi 5 Plus 16GB, NVMe SSD, RayNeo Air 3s, WiFi module
**Do:** Install Armbian. Confirm glasses work as display. Confirm NPU is detected.
**Success:** Sitting with glasses on, seeing a Linux desktop, typing commands.

### Phase 1: The Agent + The Wall (text) — ✅ COMPLETE
**Built:** `agent.py`, `wall_watcher.py`, `citadel-wall.service`, `waybar_wall.py`
**Tested:** Natural language commands, firewall monitoring, Waybar output, wall-agent integration.

### Phase 2: The Wall (visual) — ✅ COMPLETE
**Built:** Godot 4 Burning Wall overlay (project.godot, wall.tscn, burning_wall.gdshader, wall_controller.gd)
**Tested:** All four states visually confirmed with smooth transitions on test laptop.

### Phase 3: The Tunnel + Agent Integration — ✅ COMPLETE (software)
**Built:** WireGuard VPN configs, agent tunnel commands, home brain relay.
**Tested:** Encrypted tunnel, gemma3:12b queries over VPN, tunnel up/down/status.
**Not tested (needs hardware):** Boot-to-deck automation, IWD, kill switch.

### Phase 4: The Spine (optional) — NOT STARTED
**Build:** Mount hardware inside a keyboard chassis.
**Success:** An unassuming keyboard that is a full computer.

---

## 4. Open Questions

1. **Audio over USB-C DP** — does Linux audio output work through the RayNeo speakers on the Orange Pi? Needs testing.
2. **Power consumption** — how long does the Orange Pi 5 Plus + glasses run on a 65W 20,000mAh power bank? Unknown until tested.
3. **Godot on Mali-G610** — the Burning Wall shader was tested on Intel HD 4000. Performance on Mali-G610 needs verification; may need shader simplification.
4. **RKLLM model conversion** — exact workflow from HuggingFace to RKNN on x86 machine needs documenting during Phase 0.

---

## 5. Test Platform

**Machine:** Medion Akoya P7818, Debian 12.13 (bookworm)
**CPU:** Intel i3-3110M (4 threads @ 2.40GHz) — CPU-only inference simulates NPU-class performance
**GPU:** NVIDIA GT 730M (discrete, requires `prime-run` alias) / Intel HD 4000 (default)
**RAM:** 7.64 GiB
**Ollama:** qwen2.5:0.5b on CPU (~3-5 sec response time)
**Network:** 192.168.0.77/24, SSH on port 22

**Development access:** ssh-remote MCP server provides direct command execution, file upload, and file reading on the laptop from Claude Desktop. No manual file transfer needed.

**All project files on the test laptop live in `~/cyberdeck/`. No exceptions.**

**OpenSnitch note:** OpenSnitch on the test laptop blocks WireGuard kernel traffic and cannot be configured to allow it. Disable OpenSnitch during VPN testing: `sudo systemctl stop opensnitch`. This is a test-platform artifact — the real deck will not run OpenSnitch.

---

## 6. Handover — What Comes Next

### Hardware Required to Proceed

| Component | Purpose | Estimated Price (DKK) |
|---|---|---|
| Orange Pi 5 Plus 16GB | Compute platform (RK3588, NPU, USB-C DP) | 960–1410 kr |
| 512GB M.2 NVMe SSD | Storage | ~410 kr |
| RayNeo Air 3s AR glasses | Private display | 2300–3720 kr |
| M.2 E-key WiFi 6 module | Wireless connectivity | ~110 kr |
| **Minimum to start Phase 0** | **SBC + SSD + Glasses + WiFi** | **~4250 kr** |

### Remaining Software Work (needs real hardware)

**Layer 1 — The Lens:**
- Sway compositor configuration (tiling layout tuned for 1080p glasses)
- `udev` rule for glasses plug/unplug detection
- Deck-mode toggle script

**Layer 2 — The Agent (backend swap):**
- Replace Ollama with RKLLM runtime for NPU inference
- Convert model from HuggingFace → RKNN format (done on x86 machine)
- Update `agent.py` to call RKLLM instead of Ollama localhost API
- All agent logic (wall, tunnel, home brain) carries over unchanged

**Layer 3 — The Wall (hardware integration):**
- GPIO LED strip wiring (optional)
- Test Godot overlay on Mali-G610 in OpenGL ES compatibility mode
- Performance tuning if needed

**Layer 4 — The Tunnel:**
- Update WireGuard endpoint from LAN IP to public/dynamic DNS for real remote use
- IWD wireless daemon setup
- Hardware kill switch (GPIO + `rfkill block all`)

**Layer 5 — The Deck:**
- Sway + Foot + Waybar full configuration
- Boot-to-deck automation (auto-login, auto-start Sway, auto-start daemons)
- Keybinding map

### What Transfers Directly

All Python code (`agent.py`, `wall_watcher.py`, `waybar_wall.py`) runs on any Linux system with Python 3.11+. The Godot project runs on any system with Godot 4.x. The WireGuard config needs only the endpoint IP updated. The systemd service file works as-is on Armbian.

The software is ready. The hardware is the next step.

---

*This document is the source of truth for the Cyberdeck 2026 project. All design decisions trace back here.*
