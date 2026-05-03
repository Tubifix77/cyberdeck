# The Citadel — Cyberdeck 2026

A sovereign computing platform: local AI, private AR display, encrypted tunnel home, no corporate telemetry.

## What is this?

The 1980s cyberdeck from William Gibson's *Neuromancer* — rebuilt with 2026 technology. Not a prop. Not a laptop. A specialized instrument for private, encrypted, sovereign computing.

The deck is a small ARM SBC inside a keyboard shell, displayed through AR glasses only the operator can see, protected by a firewall whose state is rendered as ambient light at the edges of vision. For simple commands it thinks locally on its own NPU. For real intelligence it tunnels home to a desktop GPU over an encrypted VPN.

## Architecture

See [cyberdeck-architecture.md](cyberdeck-architecture.md) for the full specification, hardware platform, software stack, build phases, and handover notes.

## Components

### The Agent (`agent.py`)
Local AI command interpreter running on a 0.5B parameter model. Accepts natural language, decides whether to execute a shell command or answer directly. Includes keyword fast-paths for firewall status, VPN tunnel management, and home brain queries over WireGuard.

### The Wall (`wall_watcher.py`, `waybar_wall.py`, `wall_overlay/`)
Firewall monitor daemon that tails UFW logs, classifies threat state (IDLE / BLOCKED / WATCHING / STORM), and drives both a Waybar status widget and a Godot 4 shader overlay. The Burning Wall renders organic flame effects at the edges of the display that shift from cool blue (idle) through amber (activity) to red pulse (attack).

### The Tunnel (`home-vpn.conf`)
WireGuard VPN configuration for encrypted tunnel to home network. Enables the agent to query large language models (gemma3:12b) running on a home desktop GPU over an encrypted connection.

## Hardware Target

- **Compute:** Orange Pi 5 Plus 16GB (RK3588, 6 TOPS NPU)
- **Display:** RayNeo Air 3s AR glasses (1080p, USB-C DP)
- **Tunnel:** WireGuard to home PC
- **OS:** Armbian (Debian-based)
- **Cost:** ~4,250 DKK minimum (~€570)

## Project Status

Phases 1–3 software complete and tested on a Debian 12 test platform. Awaiting target hardware for final integration. See the architecture document for the full handover.

## File Structure

```
cyberdeck/
├── cyberdeck-architecture.md   # Full architecture and handover
├── agent.py                    # The Agent — AI command interpreter
├── wall_watcher.py             # The Wall — firewall monitor daemon
├── waybar_wall.py              # Waybar status bar module
├── citadel-wall.service        # systemd unit for wall daemon
├── home-vpn.conf               # WireGuard config (template)
├── wall_overlay/               # Godot 4 project
│   ├── project.godot
│   ├── wall.tscn
│   ├── burning_wall.gdshader
│   └── wall_controller.gd
└── README.md
```

## License

MIT
